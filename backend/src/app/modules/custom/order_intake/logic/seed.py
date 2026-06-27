"""Catalog seeding.

The AluProfil catalog (the company's product master data) ships with the module
as ``db/catalog_seed.csv`` and is loaded into ``oi_catalog`` idempotently — it is
reference data the reconciliation needs, not a demo example. Customers are NOT
seeded: the operator registers them explicitly (or creates new ones) at upload.
"""

import csv
import logging
from pathlib import Path
from typing import Any

from src.app.modules.custom.order_intake.db.queries import (
    bulk_upsert_catalog,
    catalog_count,
)

logger = logging.getLogger(__name__)

SEED_PATH = Path(__file__).resolve().parent.parent / "db" / "catalog_seed.csv"

_FLOAT_FIELDS = (
    "width_mm",
    "height_mm",
    "wall_thickness_mm",
    "weight_kg_per_m",
)


def _to_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value)


def load_seed_rows() -> list[dict[str, Any]]:
    """Parse the bundled catalog CSV into rows ready for the ORM."""
    rows: list[dict[str, Any]] = []
    with SEED_PATH.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row: dict[str, Any] = {
                "internal_code": raw["internal_code"].strip(),
                "profile_name": raw["profile_name"].strip(),
                "alloy": raw["alloy"].strip() or None,
                "alloy_din": raw["alloy_din"].strip() or None,
                "temper": raw["temper"].strip() or None,
                "profile_type": raw["profile_type"].strip() or None,
                "standard_lengths_mm": raw["standard_lengths_mm"].strip() or None,
                "surface_finishes": raw["surface_finishes"].strip() or None,
                "tolerance_standard": raw["tolerance_standard"].strip() or None,
                "category": raw["category"].strip() or None,
                "edi_pia_code": raw["edi_pia_code"].strip(),
                "status": "A",
            }
            for field in _FLOAT_FIELDS:
                row[field] = _to_float(raw.get(field))
            rows.append(row)
    return rows


async def ensure_catalog_seeded() -> int:
    """Seed the catalog if empty; return the number of rows after seeding."""
    existing = await catalog_count()
    if existing > 0:
        return existing
    rows = load_seed_rows()
    await bulk_upsert_catalog(rows)
    count = await catalog_count()
    logger.info("Seeded order-intake catalog with %d rows", count)
    return count
