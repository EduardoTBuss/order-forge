"""Ingestion: store the original PDF in Blob and read its text layer.

The original PDF is kept in its own ``order-intake`` Blob container so the
reconciliation UI can show it side by side with the extracted data.

Two text renderings are produced:
- ``extract_text`` (``pypdf``): the raw concatenated text layer. The
  deterministic Bauprofil parser is tuned to this.
- ``extract_markdown`` (``pymupdf4llm``): a markdown rendering that preserves the
  table structure, so the unit/quantity columns stay aligned. The LLM strategies
  use this (lighter columns => fewer wrong-column reads). It is light, pure-CPU,
  no OCR/GPU — scanned PDFs still need a different path (out of prototype scope).

Embedded-JSON extraction is intentionally absent: the day-1 spike-gate found no
embedded JSON in the real fixtures (see CHANGELOG / docs).
"""

import io
import logging
import re
import uuid

from pypdf import PdfReader

from src.app.services.blob_storage.service import BlobStorageService

logger = logging.getLogger(__name__)

BLOB_CONTAINER = "order-intake"
_blob_service = BlobStorageService(container_name=BLOB_CONTAINER)

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(filename: str) -> str:
    cleaned = _SAFE_NAME_RE.sub("_", filename.strip()) or "order.pdf"
    if not cleaned.lower().endswith(".pdf"):
        cleaned = f"{cleaned}.pdf"
    return cleaned


def store_pdf(filename: str, content: bytes) -> str:
    """Upload the PDF under a collision-free path; return the stored blob path."""
    safe = _safe_filename(filename)
    path = f"orders/{uuid.uuid4().hex[:12]}-{safe}"
    _blob_service.upload(path, content, overwrite=False, hash_suffix=False)
    logger.info("Stored order PDF at blob path %s", path)
    return path


def load_pdf(blob_path: str) -> bytes:
    """Download the original PDF bytes for a stored order."""
    return _blob_service.download(blob_path)


def extract_text(content: bytes) -> str:
    """Extract the concatenated text layer from a PDF (``pypdf``)."""
    reader = PdfReader(io.BytesIO(content))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def extract_markdown(content: bytes) -> str | None:
    """Render the PDF to column-preserving markdown via ``pymupdf4llm``.

    Returns ``None`` when the library is unavailable or rendering fails, so the
    caller transparently falls back to the plain ``pypdf`` text. Light and
    CPU-only — no OCR/GPU (scanned PDFs are out of the prototype scope).
    """
    try:
        import pymupdf  # type: ignore
        import pymupdf4llm  # type: ignore
    except Exception as exc:  # noqa: BLE001 - optional dependency
        logger.info("pymupdf4llm not available, using pypdf text: %s", exc)
        return None
    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
        try:
            return pymupdf4llm.to_markdown(doc, show_progress=False)
        finally:
            doc.close()
    except Exception as exc:  # noqa: BLE001 - fall back to pypdf text
        logger.warning("pymupdf4llm rendering failed, using pypdf text: %s", exc)
        return None


def clear_all_files() -> int:
    """Delete every blob in the ``order-intake`` container (read PDFs + .edi).

    Best-effort per blob; returns how many were deleted. The container is
    dedicated to this module, so wiping it is the "clear read & generated files"
    action. The catalog/customers/aliases live in Postgres and are untouched.
    """
    deleted = 0
    try:
        names = _blob_service.list_contents("", recursive=True)
    except Exception as exc:  # noqa: BLE001 - nothing to clear / container absent
        logger.info("No order-intake blobs to clear: %s", exc)
        return 0
    for name in names:
        try:
            _blob_service.delete(name)
            deleted += 1
        except Exception as exc:  # noqa: BLE001 - keep clearing the rest
            logger.warning("Could not delete blob %s: %s", name, exc)
    logger.info("Cleared %d order-intake blob(s)", deleted)
    return deleted


def store_edi(order_id: int, edi_text: str) -> str:
    """Upload a generated EDIFACT message; return the stored blob path."""
    path = f"edifact/order-{order_id}-{uuid.uuid4().hex[:8]}.edi"
    _blob_service.upload(
        path, edi_text.encode("ascii", "ignore"), overwrite=False, hash_suffix=False
    )
    logger.info("Stored EDIFACT export at blob path %s", path)
    return path
