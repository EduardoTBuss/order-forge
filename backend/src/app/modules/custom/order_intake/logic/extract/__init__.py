"""Extraction dispatch by strategy.

The customer selected at upload carries an ``extraction_strategy`` (and, for the
API strategy, an API key); this module maps it to an extractor:
- ``bauprofil_text``: deterministic DIN-table parser (Bauprofil layout only).
- ``ollama``: a small local model (free, offline). Needs ``OI_LLM_BASE_URL``.
- ``llm_api``: an external OpenAI-compatible LLM using the customer's API key.
"""

from src.app.modules.custom.order_intake.logic.extract.base import (
    STRATEGY_BAUPROFIL_TEXT,
    STRATEGY_LLM_API,
    STRATEGY_OLLAMA,
    ExtractedOrder,
)
from src.app.modules.custom.order_intake.logic.extract.bauprofil_text import (
    parse_bauprofil,
)
from src.app.modules.custom.order_intake.logic.extract.llm import (
    extract_with_api,
    extract_with_ollama,
    ollama_configured,
)


class ExtractionNotAvailableError(Exception):
    """Raised when no extractor is available yet for the chosen strategy."""

    def __init__(self, strategy: str, reason: str) -> None:
        self.strategy = strategy
        super().__init__(reason)


def extract_order(
    text: str,
    strategy: str,
    customer_code: str,
    api_key: str | None = None,
    api_base_url: str | None = None,
    api_model: str | None = None,
) -> ExtractedOrder:
    """Extract a normalised order from PDF text using the customer's strategy."""
    if strategy == STRATEGY_BAUPROFIL_TEXT:
        order = parse_bauprofil(text)
        order.customer = customer_code
        return order

    if strategy == STRATEGY_OLLAMA:
        if not ollama_configured():
            raise ExtractionNotAvailableError(
                STRATEGY_OLLAMA,
                "The local 'ollama' strategy needs OI_LLM_BASE_URL set and "
                "Ollama running with a model pulled (e.g. `ollama pull "
                "qwen2.5:1.5b`).",
            )
        return extract_with_ollama(text, customer_code)

    if strategy == STRATEGY_LLM_API:
        if not api_key:
            raise ExtractionNotAvailableError(
                STRATEGY_LLM_API,
                "The 'llm_api' strategy needs an API key on the customer. "
                "Register the customer with its API key.",
            )
        return extract_with_api(
            text, customer_code, api_key, api_base_url, api_model
        )

    raise ExtractionNotAvailableError(
        strategy, f"Unknown extraction strategy '{strategy}'."
    )


__all__ = [
    "ExtractedOrder",
    "ExtractionNotAvailableError",
    "extract_order",
]
