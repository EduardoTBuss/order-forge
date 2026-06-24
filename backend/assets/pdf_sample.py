"""Sample PDF as base64 for schema examples."""

import base64
from pathlib import Path

_PDF_PATH = Path(__file__).parent / "fake_invoice.pdf"
PDF_SAMPLE = base64.b64encode(_PDF_PATH.read_bytes()).decode()
