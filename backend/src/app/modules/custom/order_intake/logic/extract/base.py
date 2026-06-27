"""Shared types and helpers for extraction.

Extraction normalises any customer PDF into an ``ExtractedOrder`` regardless of
the strategy used. The strategy is chosen per customer (selected at upload):
- ``bauprofil_text``: deterministic DIN-table parser (works today, no AI).
- ``ollama``: a small local model served by Ollama (free, offline).
- ``llm_api``: an external OpenAI-compatible LLM using the customer's API key.

The reconciliation and EDIFACT stages only ever see the normalised shape, so a
new extractor is a drop-in addition.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

# Provenance markers stored alongside the raw payload in the document store.
SOURCE_TEXT_PARSER = "text_parser"
SOURCE_OLLAMA = "ollama"
SOURCE_LLM_API = "llm_api"

# Extraction strategies a customer can be configured with.
STRATEGY_BAUPROFIL_TEXT = "bauprofil_text"
STRATEGY_OLLAMA = "ollama"
STRATEGY_LLM_API = "llm_api"
KNOWN_STRATEGIES = (
    STRATEGY_BAUPROFIL_TEXT,
    STRATEGY_OLLAMA,
    STRATEGY_LLM_API,
)
# Strategies that require a per-customer API key.
KEYED_STRATEGIES = (STRATEGY_LLM_API,)


@dataclass
class ExtractedLine:
    """One line item as read from the PDF, before reconciliation."""

    line_no: str
    extracted_code: str | None = None
    description: str | None = None
    quantity: float | None = None
    unit: str | None = None
    unit_raw: str | None = None
    delivery_date: date | None = None
    length_mm: float | None = None
    alloy: str | None = None


@dataclass
class ExtractedOrder:
    """A whole order as read from the PDF, before reconciliation."""

    customer: str
    source: str
    order_ref: str | None = None
    order_date: date | None = None
    delivery_date_default: date | None = None
    currency: str = "EUR"
    lines: list[ExtractedLine] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)


def de_date_to_date(value: str | None) -> date | None:
    """Convert a German ``dd.mm.yyyy`` date string to a ``date`` (or None)."""
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


def parse_de_number(value: str) -> float:
    """Parse a German-formatted number (``2.400`` -> 2400, ``3,95`` -> 3.95)."""
    return float(value.strip().replace(".", "").replace(",", "."))
