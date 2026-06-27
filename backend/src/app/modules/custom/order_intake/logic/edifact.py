"""EDIFACT ORDERS D.96A generation for MetallSoft 7.3.

Two non-negotiables from the interface spec drive this module:
1. **PIA+1 is the gate.** A single unresolved internal code rejects the whole
   order, so generation is blocked unless *every* line resolved (no partial
   output). ``EdifactValidationError`` carries the offending line numbers.
2. **UNOA / ASCII only.** Umlauts and accents corrupt the IMD/NAD free-text
   segments silently, so all free text is transliterated to ASCII first.

This is a pure stage: it reads attributes off duck-typed order/line/catalog
objects and does not import the persistence layer at runtime (models are type
hints only), so the domain-critical EDIFACT logic is testable without a database.
"""

from __future__ import annotations

import unicodedata
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app.modules.custom.order_intake.db.models import (
        CatalogItem,
        Order,
        OrderLine,
    )

# AluProfil's fixed recipient GLN (hardcoded in MetallSoft config, spec R2).
SUPPLIER_GLN = "4012345123456"
# Buyer GLNs by customer (13-digit, per the interface spec examples).
BUYER_GLN = {
    "bauprofil": "4012345600007",
    "construxalu": "3012345600005",
    "fenstersystem": "7612345600008",
    "nordic": "7312345600003",
}
_DEFAULT_GLN = "0000000000000"

# Explicit German transliteration applied before generic accent folding.
_DE_MAP = {
    "ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
    "ß": "ss",
}
# EDIFACT service characters that must be released ("?") inside free text.
_ESCAPE = {"?": "??", "+": "?+", ":": "?:", "'": "?'"}


class EdifactValidationError(Exception):
    """Raised when an order cannot be turned into a valid EDIFACT message."""

    def __init__(self, blocking_lines: list[str], reason: str) -> None:
        self.blocking_lines = blocking_lines
        self.reason = reason
        super().__init__(reason)


def transliterate(text: str) -> str:
    """Fold text to UNOA-safe ASCII (German map first, then accent folding)."""
    for source, target in _DE_MAP.items():
        text = text.replace(source, target)
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.encode("ascii", "ignore").decode("ascii")


def _escape(text: str) -> str:
    out = transliterate(text)
    for source, target in _ESCAPE.items():
        out = out.replace(source, target)
    return out


def _fmt_qty(quantity: float) -> str:
    if quantity == int(quantity):
        return str(int(quantity))
    return f"{quantity:.3f}".rstrip("0").rstrip(".")


def _fmt_date(value: date | None, fallback: date) -> str:
    return (value or fallback).strftime("%Y%m%d")


def validate_pia(lines: list[OrderLine]) -> list[str]:
    """Return the line numbers whose PIA+1 code did not resolve (the gate)."""
    return [line.line_no for line in lines if not line.resolved_internal_code]


def generate_edifact(
    order: Order, catalog_index: dict[str, CatalogItem]
) -> tuple[str, int]:
    """Build the EDIFACT message for an order. Raises if the PIA gate fails.

    Returns ``(edi_text, segment_count)``.
    """
    if not order.lines:
        raise EdifactValidationError([], "Order has no line items (spec rule R6).")

    blocking = validate_pia(order.lines)
    if blocking:
        raise EdifactValidationError(
            blocking,
            "Cannot generate EDIFACT: lines without a resolved internal code "
            f"({', '.join(blocking)}). MetallSoft rejects the entire order.",
        )

    now = datetime.now(timezone.utc)
    today = now.date()
    buyer_gln = BUYER_GLN.get(order.customer, _DEFAULT_GLN)
    base_ref = f"OI{order.id}{now.strftime('%H%M%S')}"[:13]
    msg_ref = f"{base_ref}A"

    doc_date = _fmt_date(order.order_date, order.delivery_date_default or today)

    message: list[str] = [
        f"UNH+{msg_ref}+ORDERS:D:96A:UN'",
        f"BGM+220+{_escape(order.order_ref or str(order.id))}+9'",
        f"DTM+137:{doc_date}:102'",
    ]
    if order.order_ref:
        message.append(f"RFF+ON:{_escape(order.order_ref)}'")
    message.extend(
        [
            f"NAD+BY+{buyer_gln}::9'",
            f"NAD+SU+{SUPPLIER_GLN}::9'",
            f"NAD+DP+{buyer_gln}::9'",
            f"CUX+2:{_escape(order.currency)}:9'",
            "PAT+1++5:3:D:30'",
        ]
    )

    for index, line in enumerate(order.lines, start=1):
        resolved = (line.resolved_internal_code or "").strip()
        catalog_item = catalog_index.get(resolved.upper())
        pia_code = (catalog_item.edi_pia_code if catalog_item else resolved).strip()
        message.append(f"LIN+{index}++{pia_code}:SA'")
        message.append(f"PIA+1+{pia_code}:SA'")
        if line.description:
            message.append(f"IMD+F++:::{_escape(line.description)}'")
        unit = line.unit or "PCE"
        quantity = _fmt_qty(line.quantity if line.quantity is not None else 0)
        message.append(f"QTY+21:{quantity}:{unit}'")
        if line.length_mm:
            message.append(f"MEA+PD+AAC+{_fmt_qty(line.length_mm)}:MMT'")
        delivery = _fmt_date(line.delivery_date, order.delivery_date_default or today)
        message.append(f"DTM+2:{delivery}:102'")

    message.append("UNS+S'")
    message.append(f"CNT+2:{len(order.lines)}'")
    # UNT counts every segment in the message group, including UNH and UNT.
    unt_count = len(message) + 1
    message.append(f"UNT+{unt_count}+{msg_ref}'")

    interchange_open = (
        f"UNB+UNOA:2+{buyer_gln}+{SUPPLIER_GLN}+"
        f"{now.strftime('%y%m%d')}:{now.strftime('%H%M')}+{base_ref}'"
    )
    interchange_close = f"UNZ+1+{base_ref}'"

    segments = [interchange_open, *message, interchange_close]
    edi_text = "\n".join(segments) + "\n"
    return edi_text, len(segments)
