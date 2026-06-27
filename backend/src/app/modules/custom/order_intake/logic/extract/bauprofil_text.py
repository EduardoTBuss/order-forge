"""Deterministic text parser for Bauprofil (DE) purchase orders.

Bauprofil ships a disciplined DIN-style table and — crucially — already prints
AluProfil's internal ``AE-XXXX-XXX`` codes in the ``Art.-Nr.`` column, so the
happy path needs no LLM. This parser reads the PDF text layer and produces the
normalised ``ExtractedOrder``. It is validated against the real fixtures.

Each position spans: a header line ("010 AE-2024-034 <desc>"), an optional block
of material/dimension lines, then a quantity row ("150 Stk. <price> <date>").
Description accumulation stops at the quantity row so the last position does not
swallow the page footer / terms.
"""

import re

from src.app.modules.custom.order_intake.logic.extract.base import (
    SOURCE_TEXT_PARSER,
    ExtractedLine,
    ExtractedOrder,
    de_date_to_date,
    parse_de_number,
)

# Unit tokens seen in Bauprofil orders mapped to EDIFACT UOM codes (DE 6411).
_UNIT_MAP = {
    "stk": "PCE",
    "stk.": "PCE",
    "stueck": "PCE",
    "stück": "PCE",
    "st": "PCE",
    "kg": "KGM",
    "m": "MTR",
}

_ORDER_REF_RE = re.compile(r"Bestell-Nr\.?:\s*([A-Z0-9-]+)", re.IGNORECASE)
_ORDER_DATE_RE = re.compile(r"Bestelldatum:\s*(\d{2}\.\d{2}\.\d{4})", re.IGNORECASE)
_DELIVERY_RE = re.compile(r"Liefertermin:\s*(\d{2}\.\d{2}\.\d{4})", re.IGNORECASE)

# A position header: "010 AE-2024-034 Winkelprofil ..."
_POS_RE = re.compile(r"^(\d{3})\s+(AE-\d{4}-\d{3})\s+(.*)$")
# The quantity row: "150 Stk. 27,80 4.170,00 15.09.2026"
_QTY_RE = re.compile(
    r"^([\d.]+(?:,\d+)?)\s+(Stk\.?|kg|m|St(?:ü|u)?ck)\s+"
    r"[\d.]+,\d{2}\s+[\d.]+,\d{2}\s+(\d{2}\.\d{2}\.\d{4})\s*$",
    re.IGNORECASE,
)
# Length, tolerant of mojibake on the "Länge" label ("Lnge:", "Länge:").
_LEN_RE = re.compile(r"nge:\s*([\d.]+)\s*mm", re.IGNORECASE)
_ALLOY_RE = re.compile(r"(EN\s*AW-\d{4}[A-Z]?)")

CUSTOMER = "bauprofil"


def _normalise_unit(raw: str) -> str | None:
    return _UNIT_MAP.get(raw.strip().lower())


def _finalise_line(acc: dict[str, object]) -> ExtractedLine:
    desc_parts = acc["desc_parts"]
    assert isinstance(desc_parts, list)
    description = " ".join(p for p in desc_parts if p).strip() or None
    alloy = None
    if description:
        match = _ALLOY_RE.search(description)
        alloy = match.group(1).replace("  ", " ") if match else None
    return ExtractedLine(
        line_no=str(acc["pos"]),
        extracted_code=str(acc["code"]),
        description=description,
        quantity=acc["qty"],  # type: ignore[arg-type]
        unit=acc["unit"],  # type: ignore[arg-type]
        unit_raw=acc["unit_raw"],  # type: ignore[arg-type]
        delivery_date=de_date_to_date(acc["date"]),  # type: ignore[arg-type]
        length_mm=acc["length"],  # type: ignore[arg-type]
        alloy=alloy,
    )


def parse_bauprofil(text: str) -> ExtractedOrder:
    """Parse Bauprofil order text into a normalised ``ExtractedOrder``."""
    lines = [ln.strip() for ln in text.splitlines()]

    ref_match = _ORDER_REF_RE.search(text)
    order_date_match = _ORDER_DATE_RE.search(text)
    delivery_match = _DELIVERY_RE.search(text)

    items: list[ExtractedLine] = []
    acc: dict[str, object] | None = None

    for ln in lines:
        header = _POS_RE.match(ln)
        if header:
            if acc is not None:
                items.append(_finalise_line(acc))
            acc = {
                "pos": header.group(1),
                "code": header.group(2),
                "desc_parts": [header.group(3)],
                "qty": None,
                "unit": None,
                "unit_raw": None,
                "date": None,
                "length": None,
            }
            continue
        if acc is None:
            continue

        qty = _QTY_RE.match(ln)
        if qty and acc["qty"] is None:
            acc["qty"] = parse_de_number(qty.group(1))
            acc["unit_raw"] = qty.group(2)
            acc["unit"] = _normalise_unit(qty.group(2))
            acc["date"] = qty.group(3)
            continue

        # Keep building the description only until the quantity row is seen,
        # so the final position does not absorb the footer/terms block.
        if acc["qty"] is None:
            desc_parts = acc["desc_parts"]
            assert isinstance(desc_parts, list)
            desc_parts.append(ln)
            length = _LEN_RE.search(ln)
            if length and acc["length"] is None:
                acc["length"] = float(length.group(1).replace(".", ""))

    if acc is not None:
        items.append(_finalise_line(acc))

    raw_payload = {
        "customer": CUSTOMER,
        "order_ref": ref_match.group(1) if ref_match else None,
        "order_date": order_date_match.group(1) if order_date_match else None,
        "delivery_default": delivery_match.group(1) if delivery_match else None,
        "lines": [
            {
                "line_no": it.line_no,
                "code": it.extracted_code,
                "description": it.description,
                "quantity": it.quantity,
                "unit_raw": it.unit_raw,
                "unit": it.unit,
                "delivery_date": (
                    it.delivery_date.isoformat() if it.delivery_date else None
                ),
                "length_mm": it.length_mm,
                "alloy": it.alloy,
            }
            for it in items
        ],
    }

    return ExtractedOrder(
        customer=CUSTOMER,
        source=SOURCE_TEXT_PARSER,
        order_ref=ref_match.group(1) if ref_match else None,
        order_date=de_date_to_date(
            order_date_match.group(1) if order_date_match else None
        ),
        delivery_date_default=de_date_to_date(
            delivery_match.group(1) if delivery_match else None
        ),
        currency="EUR",
        lines=items,
        raw_payload=raw_payload,
    )
