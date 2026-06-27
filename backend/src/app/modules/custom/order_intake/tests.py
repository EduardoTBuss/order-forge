"""Integration + unit tests for the Order Intake module.

Integration tests drive the real endpoints against Postgres, Blob (Azurite) and
the seeded catalog, registering the customers they need (customers are no longer
pre-seeded). Pure-function tests lock the domain-critical bits (the PIA gate,
ASCII transliteration, exact match, the section-7 precision rules).
"""

import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient

from src.app.modules.custom.order_intake.db.models import (
    CatalogItem,
    Order,
    OrderLine,
)
from src.app.modules.custom.order_intake.db.queries import normalize_part_code
from src.app.modules.custom.order_intake.logic.confidence import (
    FLAG_AMBIGUOUS_UNIT,
    FLAG_CODE_MISMATCH,
    FLAG_UNMATCHED_CODE,
    FLAG_WEAK_MATCH,
    compute_flags,
)
from src.app.modules.custom.order_intake.logic.edifact import (
    EdifactValidationError,
    generate_edifact,
    transliterate,
)
from src.app.modules.custom.order_intake.logic.extract.base import ExtractedLine
from src.app.modules.custom.order_intake.logic.extract.llm import (
    _ORDER_JSON_SCHEMA,
    _extract_json,
    _norm_unit,
    _response_format_candidates,
    payload_to_order,
)
from src.app.modules.custom.order_intake.logic.reconcile import (
    CODE_CHECK_CONFIRMED,
    CODE_CHECK_MISMATCH,
    TIER_DIMENSION,
    TIER_EXACT,
    TIER_FUZZY,
    TIER_LEARNED,
    TIER_NONE,
    ReconResult,
    build_catalog_index,
    normalize_alloy,
    parse_dimensions,
    reconcile_code,
    reconcile_line,
)

pytestmark = pytest.mark.integration

_ASSETS = Path(__file__).parent / "tests_assets"
_BAUPROFIL_PDF = _ASSETS / "PO-2026-0615.pdf"


def _pdf_files() -> dict[str, tuple[str, bytes, str]]:
    return {
        "file": (
            "PO-2026-0615.pdf",
            _BAUPROFIL_PDF.read_bytes(),
            "application/pdf",
        )
    }


async def _ensure_customer(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
    code: str,
    strategy: str,
) -> None:
    """Register a customer, tolerating it already existing (409)."""
    resp = await async_client.post(
        f"{api_prefix}/customers",
        json={
            "code": code,
            "display_name": f"Test {code}",
            "country": "DE",
            "extraction_strategy": strategy,
        },
        headers=headers,
    )
    assert resp.status_code in (201, 409), resp.text


async def _create_order(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
    customer_code: str = "bauprofil",
    strategy: str = "bauprofil_text",
) -> dict:
    await _ensure_customer(async_client, api_prefix, headers, customer_code, strategy)
    response = await async_client.post(
        f"{api_prefix}/orders",
        files=_pdf_files(),
        data={"customer_code": customer_code},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Customer endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_customers_reflects_created(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    code = f"acme-{uuid.uuid4().hex[:8]}"
    await _ensure_customer(async_client, api_prefix, headers, code, "ollama")
    resp = await async_client.get(f"{api_prefix}/customers", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    codes = {c["code"] for c in body["customers"]}
    assert code in codes
    assert "bauprofil_text" in body["strategies"]
    assert "ollama" in body["strategies"]


@pytest.mark.asyncio
async def test_create_customer_and_duplicate(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    code = f"acme-{uuid.uuid4().hex[:8]}"
    payload = {
        "code": code,
        "display_name": "ACME Test",
        "country": "FR",
        "extraction_strategy": "ollama",
    }
    first = await async_client.post(
        f"{api_prefix}/customers", json=payload, headers=headers
    )
    assert first.status_code == 201, first.text
    assert first.json()["code"] == code

    dup = await async_client.post(
        f"{api_prefix}/customers", json=payload, headers=headers
    )
    assert dup.status_code == 409


@pytest.mark.asyncio
async def test_create_customer_rejects_unknown_strategy(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    resp = await async_client.post(
        f"{api_prefix}/customers",
        json={"code": "bad-strat", "display_name": "x", "extraction_strategy": "nope"},
        headers=headers,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Order intake integration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_order_bauprofil_happy_path(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """Upload the Bauprofil PDF: 7 lines, all resolved, gate open."""
    detail = await _create_order(async_client, api_prefix, headers)

    assert detail["customer"] == "bauprofil"
    assert detail["status"] == "in_review"
    assert detail["order_ref"] == "BP-2026-00487"
    assert detail["line_count"] == 7
    assert detail["unmatched_count"] == 0
    assert detail["can_generate_edifact"] is True

    codes = {line["resolved_internal_code"] for line in detail["lines"]}
    assert "AE-2024-034" in codes
    kgm_line = next(ln for ln in detail["lines"] if ln["line_no"] == "030")
    assert kgm_line["unit"] == "KGM"
    assert kgm_line["quantity"] == 2400


@pytest.mark.asyncio
async def test_upload_llm_customer_is_stage_two(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """A customer on the 'llm' strategy reports Stage 2 (422), not a crash."""
    code = f"llm-{uuid.uuid4().hex[:8]}"
    await _ensure_customer(async_client, api_prefix, headers, code, "ollama")
    response = await async_client.post(
        f"{api_prefix}/orders",
        files=_pdf_files(),
        data={"customer_code": code},
        headers=headers,
    )
    assert response.status_code == 422
    assert "OI_LLM_BASE_URL" in response.text


@pytest.mark.asyncio
async def test_upload_unknown_customer_400(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    response = await async_client.post(
        f"{api_prefix}/orders",
        files=_pdf_files(),
        data={"customer_code": f"missing-{uuid.uuid4().hex[:8]}"},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_and_get_order(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    created = await _create_order(async_client, api_prefix, headers)
    order_id = created["id"]

    list_resp = await async_client.get(f"{api_prefix}/orders", headers=headers)
    assert list_resp.status_code == 200
    ids = {o["id"] for o in list_resp.json()["orders"]}
    assert order_id in ids

    get_resp = await async_client.get(
        f"{api_prefix}/orders/{order_id}", headers=headers
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == order_id


@pytest.mark.asyncio
async def test_get_source_pdf(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    created = await _create_order(async_client, api_prefix, headers)
    resp = await async_client.get(
        f"{api_prefix}/orders/{created['id']}/source-pdf", headers=headers
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_generate_edifact_happy_path(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """Approving generates a valid EDIFACT ORDERS D.96A message."""
    created = await _create_order(async_client, api_prefix, headers)
    order_id = created["id"]

    resp = await async_client.post(
        f"{api_prefix}/orders/{order_id}/edifact", headers=headers
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    edi = body["edi_text"]

    assert body["status"] == "edifact_generated"
    assert edi.startswith("UNB+UNOA:2+")
    assert "UNH+" in edi and "ORDERS:D:96A:UN" in edi
    assert "PIA+1+AE-2024-034:SA'" in edi
    assert "UNZ+1+" in edi

    after = await async_client.get(
        f"{api_prefix}/orders/{order_id}", headers=headers
    )
    assert after.json()["status"] == "edifact_generated"


@pytest.mark.asyncio
async def test_get_order_not_found(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    resp = await async_client.get(f"{api_prefix}/orders/999999", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_order_empty_file(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    await _ensure_customer(async_client, api_prefix, headers, "bauprofil", "bauprofil_text")
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    resp = await async_client.post(
        f"{api_prefix}/orders",
        files=files,
        data={"customer_code": "bauprofil"},
        headers=headers,
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Pure-function tests (no services)
# ---------------------------------------------------------------------------


def _catalog_index() -> dict[str, CatalogItem]:
    item = CatalogItem(
        internal_code="AE-2024-034",
        profile_name="Equal Angle 40x40x3",
        edi_pia_code="AE-2024-034",
        status="A",
    )
    return build_catalog_index([item])


def test_transliterate_to_unoa_ascii() -> None:
    assert transliterate("Düsseldorf Größe") == "Duesseldorf Groesse"
    assert transliterate("straße") == "strasse"
    assert transliterate("façade référence") == "facade reference"


def test_reconcile_exact_is_normalised() -> None:
    index = _catalog_index()
    assert reconcile_code("  ae-2024-034 ", index).match_tier == TIER_EXACT
    assert reconcile_code("ZZ-999999", index).match_tier == TIER_NONE
    assert reconcile_code(None, index).match_tier == TIER_NONE


def test_compute_flags_signals() -> None:
    ok_line = ExtractedLine(line_no="010", quantity=150, unit="PCE")
    ok_recon = ReconResult("AE-2024-034", TIER_EXACT, None)
    assert compute_flags(ok_line, ok_recon) == []

    bad_line = ExtractedLine(line_no="020", quantity=None, unit=None)
    bad_recon = ReconResult(None, TIER_NONE, None)
    flags = compute_flags(bad_line, bad_recon)
    assert FLAG_UNMATCHED_CODE in flags
    assert FLAG_AMBIGUOUS_UNIT in flags


def test_edifact_gate_blocks_unresolved_line() -> None:
    """A single unresolved PIA+1 blocks the whole order (MetallSoft rule)."""
    order = Order(
        id=1,
        customer="bauprofil",
        source_filename="x.pdf",
        blob_path="orders/x.pdf",
        currency="EUR",
        status="in_review",
    )
    order.lines = [
        OrderLine(
            line_no="010",
            resolved_internal_code="AE-2024-034",
            quantity=10,
            unit="PCE",
        ),
        OrderLine(
            line_no="020",
            resolved_internal_code=None,
            quantity=5,
            unit="PCE",
        ),
    ]
    with pytest.raises(EdifactValidationError) as exc_info:
        generate_edifact(order, _catalog_index())
    assert "020" in exc_info.value.blocking_lines


def test_edifact_generates_when_all_resolved() -> None:
    order = Order(
        id=7,
        customer="bauprofil",
        source_filename="x.pdf",
        blob_path="orders/x.pdf",
        order_ref="BP-2026-00487",
        currency="EUR",
        status="in_review",
    )
    order.lines = [
        OrderLine(
            line_no="010",
            description="Winkelprofil 40x40x3 EN AW-6060 T66",
            resolved_internal_code="AE-2024-034",
            quantity=150,
            unit="PCE",
        )
    ]
    edi, segment_count = generate_edifact(order, _catalog_index())
    assert edi.startswith("UNB+UNOA:2+")
    assert "PIA+1+AE-2024-034:SA'" in edi
    assert "QTY+21:150:PCE'" in edi
    assert segment_count > 5


def test_llm_payload_to_order_mapping() -> None:
    """The LLM JSON payload maps to a normalised order (no model call)."""
    payload = {
        "order_ref": "CA-2026-0873",
        "order_date": "2026-04-10",
        "currency": "EUR",
        "lines": [
            {
                "line_no": "1",
                "code": "AE-2024-034",
                "description": "Corniere",
                "quantity": 120,
                "unit": "pieces",
                "delivery_date": "2026-05-01",
                "length_mm": 6000,
                "alloy": "EN AW-6060",
            },
            {"code": None, "description": "profile special", "quantity": "50", "unit": "m"},
        ],
    }
    order = payload_to_order(payload, "construxalu", "ollama")
    assert order.customer == "construxalu"
    assert order.source == "ollama"
    assert order.order_ref == "CA-2026-0873"
    assert len(order.lines) == 2
    assert order.lines[0].extracted_code == "AE-2024-034"
    assert order.lines[0].unit == "PCE"
    assert order.lines[0].quantity == 120
    assert order.lines[1].line_no == "020"
    assert order.lines[1].unit == "MTR"
    assert order.lines[1].quantity == 50.0


def _tier_catalog() -> list[CatalogItem]:
    return [
        CatalogItem(
            internal_code="AE-2024-036", profile_name="Equal Angle 40x40x3",
            alloy="EN AW-6060", temper="T66", width_mm=40.0, height_mm=40.0,
            wall_thickness_mm=3.0, edi_pia_code="AE-2024-036", status="A",
        ),
        CatalogItem(
            internal_code="AE-2024-071", profile_name="T-Slot Profile 40x40 Nut 8",
            alloy="EN AW-6060", temper="T66", width_mm=40.0, height_mm=40.0,
            wall_thickness_mm=2.5, edi_pia_code="AE-2024-071", status="A",
        ),
        CatalogItem(
            internal_code="AE-2025-030", profile_name="Heat Sink 100x30 20 Fins",
            alloy="EN AW-6063", temper="T5", width_mm=100.0, height_mm=30.0,
            wall_thickness_mm=10.0, edi_pia_code="AE-2025-030", status="A",
        ),
        # A *different* valid code at 20x20x2 — used to prove a wrong read code
        # never silently wins over the spec resolution (section 7-A).
        CatalogItem(
            internal_code="AE-2024-034", profile_name="Equal Angle 20x20x2",
            alloy="EN AW-6060", temper="T66", width_mm=20.0, height_mm=20.0,
            wall_thickness_mm=2.0, edi_pia_code="AE-2024-034", status="A",
        ),
    ]


def test_alloy_and_dimension_helpers() -> None:
    assert normalize_alloy("6060") == "EN AW-6060"
    assert normalize_alloy("AlMgSi0.5") == "EN AW-6060"
    assert normalize_alloy("EN AW-6063") == "EN AW-6063"
    assert normalize_alloy("3.2315") == "EN AW-6082"
    assert parse_dimensions("Corniere 40x40x3 mm") == (40.0, 40.0, 3.0)
    assert parse_dimensions("40 x 30 x 2,5") == (40.0, 30.0, 2.5)
    assert parse_dimensions("no dims here") is None
    # Round tube: "Ø D x wall" maps to (D, D, wall) so it matches the catalog.
    assert parse_dimensions("Tube rond Ø 40×3 mm, EN AW-6063") == (40.0, 40.0, 3.0)
    assert parse_dimensions("Round tube Ø 50x3") == (50.0, 50.0, 3.0)


def test_reconcile_round_tube_resolves_by_dimension() -> None:
    """A round tube (Ø 40×3) resolves by dimension; the read code confirms it.

    Reproduces the screenshot's "Tube rond Ø 40×3" line that previously fell to
    "No match" because the 2-number diameter notation was not parsed.
    """
    items = [
        CatalogItem(
            internal_code="AE-2024-052", profile_name="Round Tube OD40x3",
            alloy="EN AW-6060", temper="T66", width_mm=40.0, height_mm=40.0,
            wall_thickness_mm=3.0, edi_pia_code="AE-2024-052", status="A",
        )
    ]
    index = build_catalog_index(items)
    recon = reconcile_line(
        "AE-2024-052",
        "Tube rond Ø 40×3 mm, EN AW-6063 T66, 5500 mm",
        "6063",
        index,
        items,
        trust_extracted_code=False,
    )
    assert recon.match_tier == TIER_DIMENSION
    assert recon.resolved_internal_code == "AE-2024-052"
    assert recon.code_check == CODE_CHECK_CONFIRMED


def test_reconcile_tiers() -> None:
    items = _tier_catalog()
    index = build_catalog_index(items)

    dim = reconcile_line(None, "Corniere 40x40x3 mm EN AW-6060", "6060", index, items)
    assert dim.match_tier == TIER_DIMENSION
    assert dim.resolved_internal_code == "AE-2024-036"

    fz = reconcile_line(None, "Heat Sink 100x30 20 Fins", None, index, items)
    assert fz.match_tier == TIER_FUZZY
    assert fz.resolved_internal_code == "AE-2025-030"

    nomatch = reconcile_line(None, "completely unrelated gibberish zzz", None, index, items)
    assert nomatch.match_tier == TIER_NONE


# ---------------------------------------------------------------------------
# Section 7-A: resolve by specs, read code is only a cross-check
# ---------------------------------------------------------------------------


def test_specs_win_over_wrong_read_code_for_llm() -> None:
    """A swapped/wrong read code never silently wins over the spec resolution.

    The line describes a 40x40x3 angle (-> AE-2024-036) but the model read the
    code "AE-2024-034" (a *real* but different catalog item: 20x20x2). With the
    LLM source untrusted, specs resolve to AE-2024-036 and the disagreement is
    surfaced as ``code_mismatch`` — not a silent wrong product.
    """
    items = _tier_catalog()
    index = build_catalog_index(items)
    recon = reconcile_line(
        "AE-2024-034",
        "Corniere a ailes egales 40x40x3 mm EN AW-6060 T66",
        "6060",
        index,
        items,
        trust_extracted_code=False,
    )
    assert recon.match_tier == TIER_DIMENSION
    assert recon.resolved_internal_code == "AE-2024-036"
    assert recon.code_check == CODE_CHECK_MISMATCH

    line = ExtractedLine(line_no="004", quantity=200, unit="PCE")
    flags = compute_flags(line, recon)
    assert FLAG_CODE_MISMATCH in flags
    assert FLAG_WEAK_MATCH in flags  # dimension tier is not trusted
    assert FLAG_UNMATCHED_CODE not in flags  # it DID resolve, just via specs


def test_read_code_confirmed_when_it_agrees() -> None:
    """When the read code agrees with the spec resolution, no mismatch flag."""
    items = _tier_catalog()
    index = build_catalog_index(items)
    recon = reconcile_line(
        "AE-2024-036",
        "Equal angle 40x40x3 EN AW-6060",
        "6060",
        index,
        items,
        trust_extracted_code=False,
    )
    assert recon.resolved_internal_code == "AE-2024-036"
    assert recon.code_check == CODE_CHECK_CONFIRMED
    line = ExtractedLine(line_no="004", quantity=200, unit="PCE")
    assert FLAG_CODE_MISMATCH not in compute_flags(line, recon)


def test_customer_own_code_is_not_a_mismatch() -> None:
    """A customer's own (non-catalog) code that differs is not an alarm."""
    items = _tier_catalog()
    index = build_catalog_index(items)
    recon = reconcile_line(
        "PRO-045-0020",  # FensterSystem-style code, not in our catalog
        "Equal angle 40x40x3 EN AW-6060",
        "6060",
        index,
        items,
        trust_extracted_code=False,
    )
    assert recon.resolved_internal_code == "AE-2024-036"
    assert recon.code_check != CODE_CHECK_MISMATCH
    line = ExtractedLine(line_no="004", quantity=200, unit="PCE")
    assert FLAG_CODE_MISMATCH not in compute_flags(line, recon)


def test_deterministic_exact_code_still_trusted() -> None:
    """Bauprofil (trusted source) keeps resolving by its printed AE code."""
    items = _tier_catalog()
    index = build_catalog_index(items)
    recon = reconcile_line(
        "AE-2024-034", None, None, index, items, trust_extracted_code=True
    )
    assert recon.match_tier == TIER_EXACT
    assert recon.resolved_internal_code == "AE-2024-034"


# ---------------------------------------------------------------------------
# Section 7-B: learned per-customer code map
# ---------------------------------------------------------------------------


def test_learned_map_resolves_first() -> None:
    """A taught ``(customer, code) -> AE`` mapping resolves deterministically."""
    items = _tier_catalog()
    index = build_catalog_index(items)
    learned = {"PRO-045-0020": "AE-2024-071"}
    recon = reconcile_line(
        "PRO-045-0020",
        "Some window frame, no parseable dimensions",
        None,
        index,
        items,
        learned_map=learned,
        trust_extracted_code=False,
    )
    assert recon.match_tier == TIER_LEARNED
    assert recon.resolved_internal_code == "AE-2024-071"
    # Learned is a trusted tier — no weak_match flag.
    line = ExtractedLine(line_no="010", quantity=120, unit="PCE")
    assert compute_flags(line, recon) == []


def test_normalize_part_code_helper() -> None:
    assert normalize_part_code("  pro-045-0020 ") == "PRO-045-0020"
    assert normalize_part_code(None) is None
    assert normalize_part_code("   ") is None


# ---------------------------------------------------------------------------
# Section 7-D: structured output (unit enum) + French unit handling
# ---------------------------------------------------------------------------


def test_unit_enum_in_json_schema() -> None:
    """The structured-output schema constrains unit to the four EDIFACT codes."""
    line_schema = _ORDER_JSON_SCHEMA["schema"]["properties"]["lines"]["items"]
    unit_enum = line_schema["properties"]["unit"]["enum"]
    assert set(unit_enum) == {"PCE", "MTR", "KGM", "TNE", None}


def test_response_format_candidates_order() -> None:
    """API path tries json_schema first; ollama keeps json_object first."""
    api = _response_format_candidates(use_json_schema=True)
    first, second = api[0], api[1]
    assert first is not None and first["type"] == "json_schema"
    assert second is not None and second["type"] == "json_object"
    assert api[-1] is None  # plain-text fallback always last

    ollama = _response_format_candidates(use_json_schema=False)
    o_first = ollama[0]
    assert o_first is not None and o_first["type"] == "json_object"
    assert ollama[-1] is None


def test_french_and_metric_unit_aliases() -> None:
    """French 'u' (unité) -> PCE and 'ml' (mètre linéaire) -> MTR."""
    assert _norm_unit("u") == "PCE"
    assert _norm_unit("U") == "PCE"
    assert _norm_unit("unité") == "PCE"
    assert _norm_unit("ml") == "MTR"
    assert _norm_unit("kg") == "KGM"
    assert _norm_unit("t") == "TNE"
    assert _norm_unit("???") is None


# ---------------------------------------------------------------------------
# Inline edit + learned-map end to end
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inline_edit_line(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    # Dedicated customer: inline edit now teaches a learned alias, which must not
    # leak into the shared 'bauprofil' deterministic happy-path tests.
    created = await _create_order(
        async_client, api_prefix, headers, customer_code=f"edit-{uuid.uuid4().hex[:8]}"
    )
    line = created["lines"][0]
    resp = await async_client.patch(
        f"{api_prefix}/orders/{created['id']}/lines/{line['id']}",
        json={"resolved_internal_code": "AE-2024-050"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    edited = next(l for l in resp.json()["lines"] if l["id"] == line["id"])
    assert edited["resolved_internal_code"] == "AE-2024-050"
    assert edited["match_tier"] == "manual"


@pytest.mark.asyncio
async def test_learned_map_is_taught_and_reused(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """An operator edit teaches a (customer, code) -> AE that a re-upload reuses.

    Uses a dedicated customer so the alias does not leak into other tests. The
    Bauprofil parser prints AE-2024-034 on line 010; after the operator reassigns
    that line to AE-2024-050, a fresh upload of the same PDF resolves line 010 via
    the learned tier to AE-2024-050.
    """
    customer = f"learn-{uuid.uuid4().hex[:8]}"
    first = await _create_order(
        async_client, api_prefix, headers, customer_code=customer
    )
    line010 = next(ln for ln in first["lines"] if ln["line_no"] == "010")
    assert line010["resolved_internal_code"] == "AE-2024-034"

    patch = await async_client.patch(
        f"{api_prefix}/orders/{first['id']}/lines/{line010['id']}",
        json={"resolved_internal_code": "AE-2024-050"},
        headers=headers,
    )
    assert patch.status_code == 200, patch.text

    # Re-upload the same PDF for the same customer -> line 010 now learned.
    second = await _create_order(
        async_client, api_prefix, headers, customer_code=customer
    )
    reline = next(ln for ln in second["lines"] if ln["line_no"] == "010")
    assert reline["resolved_internal_code"] == "AE-2024-050"
    assert reline["match_tier"] == "learned"


@pytest.mark.asyncio
async def test_confirm_resolved_code_marks_manual_and_teaches(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """The "Confirm" action (PATCH with the line's own resolved code) accepts the
    system guess, marks the line manual, and teaches the alias so a re-upload of
    the same customer resolves it via the learned tier."""
    customer = f"cfm-{uuid.uuid4().hex[:8]}"
    first = await _create_order(
        async_client, api_prefix, headers, customer_code=customer
    )
    line010 = next(ln for ln in first["lines"] if ln["line_no"] == "010")
    resolved = line010["resolved_internal_code"]
    assert resolved == "AE-2024-034"

    # Confirm: assign the *already resolved* code (one-click accept the guess).
    resp = await async_client.patch(
        f"{api_prefix}/orders/{first['id']}/lines/{line010['id']}",
        json={"resolved_internal_code": resolved},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    edited = next(l for l in resp.json()["lines"] if l["id"] == line010["id"])
    assert edited["match_tier"] == "manual"

    second = await _create_order(
        async_client, api_prefix, headers, customer_code=customer
    )
    reline = next(ln for ln in second["lines"] if ln["line_no"] == "010")
    assert reline["match_tier"] == "learned"
    assert reline["resolved_internal_code"] == "AE-2024-034"


@pytest.mark.asyncio
async def test_inline_edit_invalid_code(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    created = await _create_order(
        async_client, api_prefix, headers, customer_code=f"edit-{uuid.uuid4().hex[:8]}"
    )
    line = created["lines"][0]
    resp = await async_client.patch(
        f"{api_prefix}/orders/{created['id']}/lines/{line['id']}",
        json={"resolved_internal_code": "ZZ-999999"},
        headers=headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_llm_api_requires_key(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    code = f"api-{uuid.uuid4().hex[:8]}"
    # Without a key -> 400
    no_key = await async_client.post(
        f"{api_prefix}/customers",
        json={"code": code, "display_name": "X", "extraction_strategy": "llm_api"},
        headers=headers,
    )
    assert no_key.status_code == 400
    # With a key -> 201, and the key is never returned
    with_key = await async_client.post(
        f"{api_prefix}/customers",
        json={
            "code": code,
            "display_name": "X",
            "extraction_strategy": "llm_api",
            "api_key": "sk-test-123",
        },
        headers=headers,
    )
    assert with_key.status_code == 201, with_key.text
    body = with_key.json()
    assert body["has_api_key"] is True
    assert "api_key" not in body


@pytest.mark.asyncio
async def test_delete_customer(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    code = f"del-{uuid.uuid4().hex[:8]}"
    await _ensure_customer(async_client, api_prefix, headers, code, "bauprofil_text")
    first = await async_client.delete(f"{api_prefix}/customers/{code}", headers=headers)
    assert first.status_code == 204
    again = await async_client.delete(f"{api_prefix}/customers/{code}", headers=headers)
    assert again.status_code == 404


@pytest.mark.asyncio
async def test_create_customer_rejects_url_as_key(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    resp = await async_client.post(
        f"{api_prefix}/customers",
        json={
            "code": f"u-{uuid.uuid4().hex[:8]}",
            "display_name": "X",
            "extraction_strategy": "llm_api",
            "api_key": "http://localhost:8000/custom/order-intake",
        },
        headers=headers,
    )
    assert resp.status_code == 400
    assert "URL" in resp.text


@pytest.mark.asyncio
async def test_clear_all_orders(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """The clear endpoint wipes all orders and reports how many were removed."""
    await _create_order(
        async_client, api_prefix, headers, customer_code=f"clr-{uuid.uuid4().hex[:8]}"
    )
    resp = await async_client.delete(f"{api_prefix}/orders", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["deleted_orders"] >= 1
    assert "deleted_files" in body

    after = await async_client.get(f"{api_prefix}/orders", headers=headers)
    assert after.status_code == 200
    assert after.json()["orders"] == []


def test_extract_json_strips_markdown_fences() -> None:
    nl = chr(10)
    fenced = (
        '```json' + nl + '{"lines": [{"code": "AE-1", "quantity": 5}]}' + nl + '```'
    )
    out = _extract_json(fenced)
    assert out["lines"][0]["code"] == "AE-1"
    preamble = 'Here is the JSON:' + nl + '{"order_ref": "X", "lines": []}'
    assert _extract_json(preamble)["order_ref"] == "X"
    assert _extract_json("not json at all") == {"lines": []}
