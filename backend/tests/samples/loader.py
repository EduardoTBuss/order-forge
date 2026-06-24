"""
Load test sample files as base64 strings for use in integration tests.
"""

import base64
from pathlib import Path

SAMPLES_DIR = Path(__file__).parent


def load_pdf_as_base64(filename: str) -> str:
    """Load a PDF file and return it as a base64 string."""
    filepath = SAMPLES_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(
            f"Sample PDF not found: {filepath}. "
            "Run 'python -m tests.samples.generate_pdfs' to generate test PDFs."
        )
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def load_audio_as_base64(filename: str) -> str:
    """Load an audio file and return it as a base64 string."""
    filepath = SAMPLES_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(
            f"Sample audio not found: {filepath}. "
            "Please add the audio file to the samples directory."
        )
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# Lazy-loaded PDF samples
_cache: dict[str, str] = {}


def get_single_page_invoice() -> str:
    """Get the single page invoice PDF as base64."""
    if "single_page_invoice" not in _cache:
        _cache["single_page_invoice"] = load_pdf_as_base64("single_page_invoice.pdf")
    return _cache["single_page_invoice"]


def get_multi_page_contract() -> str:
    """Get the multi-page contract PDF as base64."""
    if "multi_page_contract" not in _cache:
        _cache["multi_page_contract"] = load_pdf_as_base64("multi_page_contract.pdf")
    return _cache["multi_page_contract"]


def get_quarterly_report() -> str:
    """Get the quarterly report PDF as base64."""
    if "quarterly_report" not in _cache:
        _cache["quarterly_report"] = load_pdf_as_base64("quarterly_report.pdf")
    return _cache["quarterly_report"]


def get_employee_record() -> str:
    """Get the employee record PDF as base64."""
    if "employee_record" not in _cache:
        _cache["employee_record"] = load_pdf_as_base64("employee_record.pdf")
    return _cache["employee_record"]
