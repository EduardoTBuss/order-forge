"""LLM extractors (Stage-2 spine), in two flavours that share one core:

- ``extract_with_ollama``: a small local model served by Ollama (free, offline).
- ``extract_with_api``: an external OpenAI-compatible LLM using the customer's
  own API key (better quality; the key is supplied per customer).

Both read the PDF text and return the normalised ``ExtractedOrder``. The model
only *reads* — it never invents the internal ``AE-XXXX-XXX`` code; reconciliation
against the catalog stays deterministic downstream, and (section 7) the read code
is treated as a cross-check, not the source of truth.

Structured output (section 7-D): the external API path asks the provider for a
JSON **schema** where ``unit`` is a strict enum ``{PCE, MTR, KGM, TNE}`` — the
model cannot invent a unit. Providers that do not support ``json_schema`` fall
back to ``json_object`` and then to plain text, all parsed by ``_extract_json``.

Local (Ollama) config, passed to the backend container via docker-compose:
- ``OI_LLM_BASE_URL`` e.g. ``http://ollama:11434/v1`` (enables the local mode)
- ``OI_LLM_MODEL``    e.g. ``qwen2.5:1.5b``
External API config:
- ``OI_LLM_API_BASE_URL`` default ``https://api.openai.com/v1``
- ``OI_LLM_API_MODEL``    default ``gpt-4o-mini``
- key: supplied per customer at registration.
"""

import json
import logging
import os
import re
import unicodedata
from datetime import date, datetime
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAI,
)

from src.app.modules.custom.order_intake.logic.extract.base import (
    SOURCE_LLM_API,
    SOURCE_OLLAMA,
    ExtractedLine,
    ExtractedOrder,
)

logger = logging.getLogger(__name__)


class LLMExtractionError(Exception):
    """A user-actionable error from the LLM provider (bad key, unreachable…)."""


_OLLAMA_DEFAULT_MODEL = "qwen2.5:1.5b"
_API_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_API_DEFAULT_MODEL = "gpt-4o-mini"

# The four EDIFACT units of measure MetallSoft accepts (DE 6411).
ALLOWED_UNITS = ("PCE", "MTR", "KGM", "TNE")

_UNIT_MAP = {
    "pce": "PCE", "pcs": "PCE", "pc": "PCE", "piece": "PCE", "pieces": "PCE",
    "stk": "PCE", "stueck": "PCE", "st": "PCE", "ea": "PCE", "unit": "PCE",
    "unite": "PCE", "unites": "PCE", "u": "PCE", "stueck.": "PCE",
    "mtr": "MTR", "m": "MTR", "meter": "MTR", "metre": "MTR", "ml": "MTR",
    "kgm": "KGM", "kg": "KGM", "kilogram": "KGM", "kgs": "KGM",
    "tne": "TNE", "t": "TNE", "tonne": "TNE", "ton": "TNE", "to": "TNE",
}

# JSON schema for structured output. ``unit`` is a strict enum so the model
# cannot invent a unit of measure (section 7-D).
_ORDER_JSON_SCHEMA: dict[str, Any] = {
    "name": "purchase_order",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "order_ref": {"type": ["string", "null"]},
            "order_date": {"type": ["string", "null"]},
            "currency": {"type": ["string", "null"]},
            "lines": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "line_no": {"type": ["string", "null"]},
                        "code": {"type": ["string", "null"]},
                        "description": {"type": ["string", "null"]},
                        "quantity": {"type": ["number", "null"]},
                        "unit": {
                            "type": ["string", "null"],
                            "enum": ["PCE", "MTR", "KGM", "TNE", None],
                        },
                        "delivery_date": {"type": ["string", "null"]},
                        "length_mm": {"type": ["number", "null"]},
                        "alloy": {"type": ["string", "null"]},
                    },
                    "required": [
                        "line_no", "code", "description", "quantity", "unit",
                        "delivery_date", "length_mm", "alloy",
                    ],
                },
            },
        },
        "required": ["order_ref", "order_date", "currency", "lines"],
    },
}

_SYSTEM_PROMPT = (
    "You read a supplier purchase order and return STRICT JSON only — no prose. "
    "Do not invent data; use null for missing fields. Never guess an internal "
    "article code."
)

_USER_TEMPLATE = """Extract the order into this exact JSON shape:

{{
  "order_ref": string|null,
  "order_date": "YYYY-MM-DD"|null,
  "currency": string|null,
  "lines": [
    {{
      "line_no": string|null,
      "code": string|null,
      "description": string|null,
      "quantity": number|null,
      "unit": "PCE"|"MTR"|"KGM"|"TNE"|null,
      "delivery_date": "YYYY-MM-DD"|null,
      "length_mm": number|null,
      "alloy": string|null
    }}
  ]
}}

Keep each "description" concise (max ~80 chars).
Unit rules — ALWAYS fill "unit" with one of PCE/MTR/KGM/TNE by mapping the
document's unit (never invent another value):
- pieces / Stück / Stk / pcs / units / unité / "u" / a piece count -> "PCE"
- meter / metre / m / ml / running length -> "MTR"
- kilogram / kg -> "KGM"
- tonne / t -> "TNE"
Return ONLY the JSON object. Document:
---
{document}
---"""


def ollama_configured() -> bool:
    """True when the local Ollama endpoint is configured (``OI_LLM_BASE_URL``)."""
    return bool(os.getenv("OI_LLM_BASE_URL"))


def _parse_date(value: Any) -> date | None:
    if not value or not isinstance(value, str):
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _norm_unit(value: Any) -> str | None:
    """Map any unit spelling (accent-insensitive) to an EDIFACT UOM code."""
    if not value or not isinstance(value, str):
        return None
    folded = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    if not folded:
        return None
    if folded in _UNIT_MAP:
        return _UNIT_MAP[folded]
    if "stk" in folded or "stuck" in folded or "piece" in folded or "pcs" in folded:
        return "PCE"
    if folded.startswith("kg") or "kilogram" in folded:
        return "KGM"
    if "tonne" in folded or "ton" in folded:
        return "TNE"
    if "met" in folded or folded in {"m", "mtr"}:
        return "MTR"
    return None


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None
    return None


def payload_to_order(
    payload: dict[str, Any], customer_code: str, source: str
) -> ExtractedOrder:
    """Map the model's JSON payload into a normalised ExtractedOrder (pure)."""
    raw_lines = payload.get("lines") or []
    lines: list[ExtractedLine] = []
    for index, item in enumerate(raw_lines, start=1):
        if not isinstance(item, dict):
            continue
        line_no = item.get("line_no")
        lines.append(
            ExtractedLine(
                line_no=str(line_no)
                if line_no not in (None, "")
                else f"{index * 10:03d}",
                extracted_code=(item.get("code") or None),
                description=(item.get("description") or None),
                quantity=_to_float(item.get("quantity")),
                unit=_norm_unit(item.get("unit")),
                unit_raw=item.get("unit")
                if isinstance(item.get("unit"), str)
                else None,
                delivery_date=_parse_date(item.get("delivery_date")),
                length_mm=_to_float(item.get("length_mm")),
                alloy=(item.get("alloy") or None),
            )
        )
    return ExtractedOrder(
        customer=customer_code,
        source=source,
        order_ref=(payload.get("order_ref") or None),
        order_date=_parse_date(payload.get("order_date")),
        delivery_date_default=_parse_date(payload.get("delivery_date")),
        currency=(payload.get("currency") or "EUR"),
        lines=lines,
        raw_payload=payload,
    )


def _extract_json(content: str) -> dict[str, Any]:
    """Parse JSON from a model response, tolerating markdown fences/preamble."""
    text = (content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            try:
                payload = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                payload = {"lines": []}
        else:
            payload = {"lines": []}
    return payload if isinstance(payload, dict) else {"lines": []}


def _response_format_candidates(use_json_schema: bool) -> list[dict[str, Any] | None]:
    """Response-format candidates to try, in order, with graceful fallback.

    Structured ``json_schema`` (enum-constrained ``unit``) is tried first on the
    API path; providers that reject it fall back to ``json_object`` and then to
    plain text. Ollama keeps ``json_object`` first to preserve its behaviour.
    """
    candidates: list[dict[str, Any] | None] = []
    if use_json_schema:
        candidates.append({"type": "json_schema", "json_schema": _ORDER_JSON_SCHEMA})
    candidates.append({"type": "json_object"})
    candidates.append(None)  # plain text, parsed leniently
    return candidates


def _is_response_format_error(exc: APIStatusError) -> bool:
    detail = (getattr(exc, "message", "") or str(exc)).lower()
    return exc.status_code == 400 and (
        "response_format" in detail
        or "json_schema" in detail
        or "schema" in detail
        or "response format" in detail
    )


def _run_extraction(
    text: str,
    customer_code: str,
    *,
    base_url: str,
    model: str,
    api_key: str,
    source: str,
    max_tokens: int = 2048,
    use_json_schema: bool = False,
    ollama_options: dict[str, Any] | None = None,
) -> ExtractedOrder:
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=300.0)
    base_kwargs: dict[str, Any] = {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _USER_TEMPLATE.format(document=text[:8000])},
        ],
    }
    if ollama_options is not None:
        base_kwargs["extra_body"] = {"options": ollama_options}

    candidates = _response_format_candidates(use_json_schema)
    completion = None
    last_error: APIStatusError | None = None
    for response_format in candidates:
        kwargs = dict(base_kwargs)
        if response_format is not None:
            kwargs["response_format"] = response_format
        try:
            completion = client.chat.completions.create(**kwargs)
            break
        except AuthenticationError as exc:
            raise LLMExtractionError(
                "Invalid API key for this customer (provider returned 401). "
                "Check the key and the Base URL match the same provider."
            ) from exc
        except APIConnectionError as exc:
            raise LLMExtractionError(
                "Could not reach the LLM provider. Check the Base URL "
                "(OpenAI-compatible '/v1' endpoint) and your network."
            ) from exc
        except APIStatusError as exc:
            # A provider that rejects this response_format → try the next, simpler
            # one. Any other 4xx/5xx is a real error and surfaces to the operator.
            if _is_response_format_error(exc):
                last_error = exc
                continue
            raise LLMExtractionError(
                f"LLM provider returned HTTP {exc.status_code}: "
                f"{getattr(exc, 'message', '') or exc}. Check the Base URL is an "
                "OpenAI-compatible '/v1' endpoint and the Model name is valid."
            ) from exc

    if completion is None:
        detail = getattr(last_error, "message", "") or str(last_error)
        raise LLMExtractionError(
            f"LLM provider rejected every response format (last: {detail}). "
            "Check the Model name supports JSON output."
        )

    content = completion.choices[0].message.content or "{}"
    payload = _extract_json(content)
    return payload_to_order(payload, customer_code, source)


def extract_with_ollama(text: str, customer_code: str) -> ExtractedOrder:
    """Extract using the local Ollama model (free, offline)."""
    return _run_extraction(
        text,
        customer_code,
        base_url=os.getenv("OI_LLM_BASE_URL", ""),
        model=os.getenv("OI_LLM_MODEL", _OLLAMA_DEFAULT_MODEL),
        api_key=os.getenv("OI_LLM_API_KEY", "ollama"),
        source=SOURCE_OLLAMA,
        max_tokens=2048,
        use_json_schema=False,
        ollama_options={"num_ctx": 8192},
    )


def extract_with_api(
    text: str,
    customer_code: str,
    api_key: str,
    base_url: str | None = None,
    model: str | None = None,
) -> ExtractedOrder:
    """Extract using an external OpenAI-compatible LLM with the customer's key.

    ``base_url``/``model`` override the env defaults, so each customer can use a
    different provider (OpenAI, OpenRouter, etc.). Structured output with an
    enum-constrained ``unit`` is requested, with graceful fallback.
    """
    return _run_extraction(
        text,
        customer_code,
        base_url=base_url
        or os.getenv("OI_LLM_API_BASE_URL", _API_DEFAULT_BASE_URL),
        model=model or os.getenv("OI_LLM_API_MODEL", _API_DEFAULT_MODEL),
        api_key=api_key,
        source=SOURCE_LLM_API,
        max_tokens=4096,
        use_json_schema=True,
    )
