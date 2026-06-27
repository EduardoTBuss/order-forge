"""Reconciliation against the internal catalog (tiered, decreasing confidence).

Tiers, in order:
0. ``learned``   — a ``(customer, their code)`` mapping taught by an operator edit.
1. ``exact``     — extracted code == internal code (deterministic sources only).
2. ``dimension`` — alloy alias + parsed dimensions match a catalog profile.
3. ``fuzzy``     — best fuzzy match of the description above a threshold.
Plus ``manual`` (operator-assigned) and ``none``.

The ``AE-XXXX-XXX`` code is never invented — every tier resolves to a real
catalog row. **Crucially, for LLM-extracted lines the model-read code is NOT used
to resolve** (cheap models swap a digit, and a swapped digit can hit *another*
valid code → a silent wrong product, dangerous in MetallSoft). Instead specs
(dimension/alloy/fuzzy) resolve the AE code, and the read code is only a
**cross-check**: if it disagrees with the resolved code (and is itself a real
catalog code) we raise ``code_check == "mismatch"``. Deterministic sources
(Bauprofil prints the real AE code) keep trusting the exact code.

This is a pure stage: it does not import the persistence layer at runtime.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from rapidfuzz import fuzz

if TYPE_CHECKING:
    from src.app.modules.custom.order_intake.db.models import CatalogItem

TIER_LEARNED = "learned"
TIER_EXACT = "exact"
TIER_DIMENSION = "dimension"
TIER_FUZZY = "fuzzy"
TIER_MANUAL = "manual"
TIER_NONE = "none"

# Trusted tiers need no human second-look; the rest are flagged ``weak_match``.
TRUSTED_TIERS = {TIER_EXACT, TIER_MANUAL, TIER_LEARNED}

# Cross-check of the model-read code against the spec-resolved code.
CODE_CHECK_CONFIRMED = "confirmed"  # read code == resolved code (or absent+trusted)
CODE_CHECK_MISMATCH = "mismatch"  # read code is a *different* valid catalog code
CODE_CHECK_ABSENT = "absent"  # no read code, or it is not an internal code

_FUZZY_THRESHOLD = 86.0
_DIM_TOLERANCE = 0.1  # mm

# Alloy aliases → canonical EN AW designation (numeric / DIN / AlMgSi names).
_ALLOY_CANON = {
    "6060": "EN AW-6060", "almgsi0.5": "EN AW-6060", "almgsi05": "EN AW-6060",
    "3.3206": "EN AW-6060",
    "6063": "EN AW-6063", "3.3221": "EN AW-6063",
    "6082": "EN AW-6082", "almgsi1": "EN AW-6082", "3.2315": "EN AW-6082",
    "6005a": "EN AW-6005A", "6005": "EN AW-6005A", "almgsi0.7": "EN AW-6005A",
    "3.3210": "EN AW-6005A",
}
_EN_AW_RE = re.compile(r"en\s*aw[-\s]?(\d{4}[a-z]?)", re.IGNORECASE)
_DIM3_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*[x×*]\s*(\d+(?:[.,]\d+)?)\s*[x×*]\s*(\d+(?:[.,]\d+)?)"
)
# Round tube: a diameter symbol (Ø / ⌀ / "diam" / "rond" / "round" / "rundrohr")
# followed by ``D x wall``. Catalog round tubes store the OD in both width and
# height, so a round tube reads as ``(D, D, wall)`` for the dimension matcher.
_ROUND_RE = re.compile(
    r"(?:[Ø⌀]|diam[.\w]*|tube\s+rond|round\s+tube|rundrohr)\D{0,12}?"
    r"(\d+(?:[.,]\d+)?)\s*[x×*]\s*(\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)


@dataclass
class ReconResult:
    """The outcome of reconciling one extracted line against the catalog."""

    resolved_internal_code: str | None
    match_tier: str
    catalog_item: "CatalogItem | None"
    code_check: str = CODE_CHECK_ABSENT


def normalize_alloy(text: str | None) -> str | None:
    """Map any alloy spelling (6060 / AlMgSi0.5 / EN AW-6060 / 3.3206) to EN AW."""
    if not text:
        return None
    match = _EN_AW_RE.search(text)
    if match:
        return f"EN AW-{match.group(1).upper()}"
    low = text.lower().replace(" ", "")
    for alias, canon in _ALLOY_CANON.items():
        if alias in low:
            return canon
    return None


def _to_mm(value: str) -> float:
    return float(value.replace(",", "."))


def parse_dimensions(text: str | None) -> tuple[float, float, float] | None:
    """Parse ``WxHxT`` (mm) from free text, if present.

    Recognises both rectangular ``WxHxT`` and round tubes (``Ø D x wall``), the
    latter mapped to ``(D, D, wall)`` since the catalog stores a round tube's
    outside diameter in both width and height.
    """
    if not text:
        return None
    match = _DIM3_RE.search(text)
    if match:
        w, h, t = match.groups()
        return (_to_mm(w), _to_mm(h), _to_mm(t))
    round_match = _ROUND_RE.search(text)
    if round_match:
        diameter, wall = (_to_mm(g) for g in round_match.groups())
        return (diameter, diameter, wall)
    return None


def build_catalog_index(items: list[CatalogItem]) -> dict[str, CatalogItem]:
    """Index active catalog items by their normalised internal code."""
    return {item.internal_code.strip().upper(): item for item in items}


def _norm(code: str | None) -> str | None:
    return code.strip().upper() if code else None


def _code_check(
    read_code: str | None, resolved_code: str, index: dict[str, CatalogItem]
) -> str:
    """Cross-check the model-read code against the spec-resolved code.

    Only flags a *mismatch* when the read code is itself a valid catalog code
    pointing elsewhere — that is the silent-wrong-product danger. A customer's
    own (non-AE) code that merely differs is not an alarm.
    """
    norm = _norm(read_code)
    if not norm:
        return CODE_CHECK_ABSENT
    if norm == resolved_code.strip().upper():
        return CODE_CHECK_CONFIRMED
    if norm in index:
        return CODE_CHECK_MISMATCH
    return CODE_CHECK_ABSENT


def reconcile_code(
    extracted_code: str | None, index: dict[str, CatalogItem]
) -> ReconResult:
    """Exact-match a code against the catalog (used by inline edit too)."""
    norm = _norm(extracted_code)
    if not norm:
        return ReconResult(None, TIER_NONE, None, CODE_CHECK_ABSENT)
    item = index.get(norm)
    if item is not None:
        return ReconResult(item.internal_code, TIER_EXACT, item, CODE_CHECK_CONFIRMED)
    return ReconResult(None, TIER_NONE, None, CODE_CHECK_ABSENT)


def _close(a: float | None, b: float) -> bool:
    return a is not None and abs(a - b) <= _DIM_TOLERANCE


def _match_by_dimension(
    dims: tuple[float, float, float],
    alloy: str | None,
    catalog: list[CatalogItem],
) -> CatalogItem | None:
    w, h, t = dims
    wanted = {w, h}
    candidates = [
        c
        for c in catalog
        if _close(c.wall_thickness_mm, t)
        and {c.width_mm, c.height_mm} == wanted
    ]
    if alloy:
        with_alloy = [c for c in candidates if normalize_alloy(c.alloy) == alloy]
        if with_alloy:
            candidates = with_alloy
    return candidates[0] if len(candidates) == 1 else None


def _match_by_fuzzy(
    description: str, alloy: str | None, catalog: list[CatalogItem]
) -> CatalogItem | None:
    best: CatalogItem | None = None
    best_score = 0.0
    for item in catalog:
        target = item.profile_name
        if item.alloy:
            target = f"{target} {item.alloy}"
        score = fuzz.token_set_ratio(description, target)
        if alloy and normalize_alloy(item.alloy) == alloy:
            score += 5.0
        if score > best_score:
            best_score, best = score, item
    if best is not None and best_score >= _FUZZY_THRESHOLD:
        return best
    return None


def reconcile_line(
    extracted_code: str | None,
    description: str | None,
    alloy: str | None,
    index: dict[str, CatalogItem],
    catalog: list[CatalogItem],
    *,
    learned_map: dict[str, str] | None = None,
    trust_extracted_code: bool = True,
) -> ReconResult:
    """Resolve a line to a catalog code through the tiers, in confidence order.

    ``learned_map`` maps a customer's normalised printed code to an internal
    code (taught by operator edits) and wins over everything. When
    ``trust_extracted_code`` is False (LLM sources), the read code never resolves
    — only specs do — and the read code is kept purely as a cross-check
    (``code_check``). Deterministic sources (Bauprofil) keep ``trust=True`` so
    the printed AE code is the exact tier.
    """
    norm_code = _norm(extracted_code)

    # Tier 0 — learned (customer, their code) -> internal. Operator-taught, trusted.
    if learned_map and norm_code and norm_code in learned_map:
        target = learned_map[norm_code]
        item = index.get(target.strip().upper())
        if item is not None:
            return ReconResult(
                item.internal_code, TIER_LEARNED, item, CODE_CHECK_CONFIRMED
            )

    # Tier 1 — trusted exact code (deterministic sources only).
    if trust_extracted_code and norm_code:
        item = index.get(norm_code)
        if item is not None:
            return ReconResult(
                item.internal_code, TIER_EXACT, item, CODE_CHECK_CONFIRMED
            )

    # Spec tiers — the AE code is resolved from specs, never from a read code.
    canon_alloy = normalize_alloy(alloy) or normalize_alloy(description)

    dims = parse_dimensions(description)
    if dims is not None:
        item = _match_by_dimension(dims, canon_alloy, catalog)
        if item is not None:
            check = _code_check(extracted_code, item.internal_code, index)
            return ReconResult(item.internal_code, TIER_DIMENSION, item, check)

    if description:
        item = _match_by_fuzzy(description, canon_alloy, catalog)
        if item is not None:
            check = _code_check(extracted_code, item.internal_code, index)
            return ReconResult(item.internal_code, TIER_FUZZY, item, check)

    return ReconResult(None, TIER_NONE, None, CODE_CHECK_ABSENT)
