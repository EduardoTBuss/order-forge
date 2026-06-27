"""Synchronous intake flow.

``run_intake`` chains the stages in order — resolve customer -> ingest -> extract
(by the customer's strategy) -> reconcile (tiered) -> confidence -> persist — and
``generate_order_edifact`` runs the gated EDIFACT export. Plain synchronous
Python (no orchestrator), exactly as the charter requires.

Store roles: Blob keeps the PDF + the .edi, Postgres keeps the relational
customers/orders/lines/catalog/exports, and Mongo keeps the raw extracted
payload + provenance.

Precision strategy (section 7): for LLM sources the model-read code is a
cross-check only — the AE code is resolved from specs/learned map, never trusted
from the model (it swaps digits). Deterministic sources (Bauprofil) keep their
printed AE code. Every operator inline edit teaches a per-customer learned map so
repeated codes resolve without the LLM next time.
"""

import logging
from datetime import datetime, timezone

from src.app.modules.custom.order_intake.db.models import Order, OrderLine
from src.app.modules.custom.order_intake.db.queries import (
    create_order_with_lines,
    delete_all_orders,
    find_catalog_by_code,
    get_code_alias_map,
    get_customer,
    get_order,
    get_order_line,
    list_active_catalog,
    save_edifact_export,
    set_order_status,
    update_line_resolution,
    upsert_code_alias,
)
from src.app.modules.custom.order_intake.logic.confidence import compute_flags
from src.app.modules.custom.order_intake.logic.edifact import generate_edifact
from src.app.modules.custom.order_intake.logic.extract import (
    ExtractedOrder,
    extract_order,
)
from src.app.modules.custom.order_intake.logic.extract.base import (
    SOURCE_TEXT_PARSER,
    STRATEGY_LLM_API,
    STRATEGY_OLLAMA,
    ExtractedLine,
)
from src.app.modules.custom.order_intake.logic.ingest import (
    clear_all_files,
    extract_markdown,
    extract_text,
    store_edi,
    store_pdf,
)
from src.app.modules.custom.order_intake.logic.reconcile import (
    TIER_MANUAL,
    ReconResult,
    build_catalog_index,
    reconcile_line,
)
from src.app.modules.custom.order_intake.logic.seed import (
    ensure_catalog_seeded,
)
from src.app.services.cosmosdb.service import CosmosDBService

logger = logging.getLogger(__name__)

STATUS_IN_REVIEW = "in_review"
STATUS_EDIFACT_GENERATED = "edifact_generated"

# Strategies whose extracted code must NOT be trusted to resolve the AE code
# (the model transcribes and swaps digits); specs/learned map resolve instead.
_LLM_STRATEGIES = (STRATEGY_OLLAMA, STRATEGY_LLM_API)

_MONGO_DB = "order_intake"
_MONGO_COLLECTION = "raw_payloads"


class OrderNotFoundError(Exception):
    """Raised when an order id does not exist."""


class CustomerNotFoundError(Exception):
    """Raised when the selected customer code is not registered."""


class LineNotFoundError(Exception):
    """Raised when an order line id does not exist for the order."""


class CatalogCodeNotFoundError(Exception):
    """Raised when a manually-assigned code is not an active catalog item."""


async def _store_provenance(order_id: int, extracted: ExtractedOrder) -> None:
    """Persist the raw extracted payload + provenance to the document store.

    Best-effort: the relational store is the source of truth, so a document-store
    hiccup must not fail the intake. It still exercises the third persistence
    technology on the happy path.
    """
    try:
        service = await CosmosDBService.build_or_create(
            _MONGO_DB, _MONGO_COLLECTION
        )
        await service.create_item(
            {
                "order_id": order_id,
                "customer": extracted.customer,
                "source": extracted.source,
                "raw_payload": extracted.raw_payload,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as exc:  # noqa: BLE001 - provenance is auxiliary
        logger.warning("Could not store provenance for order %s: %s", order_id, exc)


def _extraction_input(content: bytes, strategy: str) -> str:
    """Pick the text fed to extraction.

    LLM strategies get a markdown rendering (``pymupdf4llm``) that preserves the
    table columns — so the unit/quantity columns stay aligned and the model is
    less likely to read a value from the wrong column. The deterministic
    Bauprofil parser keeps the raw ``pypdf`` text its regexes are tuned to.
    """
    text = extract_text(content)
    if strategy in _LLM_STRATEGIES:
        markdown = extract_markdown(content)
        if markdown and markdown.strip():
            return markdown
    return text


async def run_intake(filename: str, content: bytes, customer_code: str) -> int:
    """Ingest a PDF end to end for the selected customer; return the order id."""
    await ensure_catalog_seeded()

    customer = await get_customer(customer_code)
    if customer is None:
        raise CustomerNotFoundError(f"Customer '{customer_code}' is not registered.")

    blob_path = store_pdf(filename, content)
    extraction_text = _extraction_input(content, customer.extraction_strategy)
    extracted = extract_order(
        extraction_text,
        customer.extraction_strategy,
        customer_code,
        customer.api_key,
        customer.api_base_url,
        customer.api_model,
    )

    catalog_items = await list_active_catalog()
    catalog_index = build_catalog_index(catalog_items)
    learned_map = await get_code_alias_map(customer_code)

    # Deterministic sources print the real AE code; LLM sources must not be
    # trusted to transcribe it (the AE is resolved from specs instead).
    trust_code = extracted.source == SOURCE_TEXT_PARSER

    lines: list[OrderLine] = []
    for item in extracted.lines:
        recon = reconcile_line(
            item.extracted_code,
            item.description,
            item.alloy,
            catalog_index,
            catalog_items,
            learned_map=learned_map,
            trust_extracted_code=trust_code,
        )
        flags = compute_flags(item, recon)
        lines.append(
            OrderLine(
                line_no=item.line_no,
                extracted_code=item.extracted_code,
                description=item.description,
                quantity=item.quantity,
                unit=item.unit,
                delivery_date=item.delivery_date,
                length_mm=item.length_mm,
                alloy=item.alloy,
                resolved_internal_code=recon.resolved_internal_code,
                match_tier=recon.match_tier,
                confidence_flags=flags,
            )
        )

    order = Order(
        customer=customer_code,
        source_filename=filename,
        blob_path=blob_path,
        order_ref=extracted.order_ref,
        order_date=extracted.order_date,
        delivery_date_default=extracted.delivery_date_default,
        currency=extracted.currency,
        status=STATUS_IN_REVIEW,
    )

    order_id = await create_order_with_lines(order, lines)
    await _store_provenance(order_id, extracted)
    logger.info(
        "Intake complete: order %s (%s) with %d line(s)",
        order_id,
        customer_code,
        len(lines),
    )
    return order_id


async def clear_all_orders() -> dict[str, int]:
    """Clear all read & generated files and their orders (a demo "reset").

    Deletes every order row (cascading to lines + EDIFACT exports), every blob in
    the order-intake container (uploaded PDFs + generated .edi), and the raw
    provenance documents. Customers, the learned code map and the catalog are
    intentionally kept. Returns counts for the UI.
    """
    deleted_orders = await delete_all_orders()
    deleted_files = clear_all_files()
    try:
        service = await CosmosDBService.build_or_create(
            _MONGO_DB, _MONGO_COLLECTION
        )
        await service.delete_items({})
    except Exception as exc:  # noqa: BLE001 - provenance is auxiliary
        logger.warning("Could not clear provenance: %s", exc)
    logger.info(
        "Cleared order intake: %d order(s), %d file(s)",
        deleted_orders,
        deleted_files,
    )
    return {"deleted_orders": deleted_orders, "deleted_files": deleted_files}


async def generate_order_edifact(order_id: int) -> tuple[Order, str]:
    """Generate, persist, and store the EDIFACT export for an order.

    Raises ``OrderNotFoundError`` if the order is missing, or
    ``EdifactValidationError`` (from the edifact stage) if the PIA gate fails.
    """
    order = await get_order(order_id)
    if order is None:
        raise OrderNotFoundError(f"Order {order_id} not found")

    catalog_index = build_catalog_index(await list_active_catalog())
    edi_text, segment_count = generate_edifact(order, catalog_index)

    edi_blob_path = store_edi(order_id, edi_text)
    await save_edifact_export(order_id, edi_text, edi_blob_path, segment_count)
    await set_order_status(order_id, STATUS_EDIFACT_GENERATED)

    refreshed = await get_order(order_id)
    if refreshed is None:  # pragma: no cover - just persisted it
        raise OrderNotFoundError(f"Order {order_id} not found")
    return refreshed, edi_text


async def set_line_code(order_id: int, line_id: int, internal_code: str) -> Order:
    """Manually assign an internal code to a line (operator inline edit).

    Validates the code against the active catalog, marks the line as ``manual``
    (a trusted tier), recomputes its confidence flags, and — crucially — teaches
    the per-customer learned map so the same customer code resolves on its own
    next time (auto-improving reconciliation).
    """
    line = await get_order_line(line_id)
    if line is None or line.order_id != order_id:
        raise LineNotFoundError(f"Line {line_id} not found for order {order_id}")

    catalog_item = await find_catalog_by_code(internal_code)
    if catalog_item is None:
        raise CatalogCodeNotFoundError(
            f"'{internal_code}' is not an active catalog code."
        )

    extracted = ExtractedLine(
        line_no=line.line_no, quantity=line.quantity, unit=line.unit
    )
    recon = ReconResult(catalog_item.internal_code, TIER_MANUAL, catalog_item)
    flags = compute_flags(extracted, recon)
    await update_line_resolution(
        line_id, catalog_item.internal_code, TIER_MANUAL, flags
    )

    refreshed = await get_order(order_id)
    if refreshed is None:  # pragma: no cover
        raise OrderNotFoundError(f"Order {order_id} not found")

    # Teach the learned map: (this customer, the code they printed) -> AE code.
    if line.extracted_code:
        await upsert_code_alias(
            refreshed.customer, line.extracted_code, catalog_item.internal_code
        )

    return refreshed
