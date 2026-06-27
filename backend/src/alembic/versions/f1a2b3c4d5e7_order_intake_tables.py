"""order_intake tables + catalog seed

Creates the four Order Intake tables and seeds the catalog from the CSV bundled
with the module (``custom/order_intake/db/catalog_seed.csv``). Seeding here means
a fresh database has the catalog available immediately (runtime seeding is a
belt-and-suspenders fallback for empty test databases).

Revision ID: f1a2b3c4d5e7
Revises: d1a2b3c4d5e6
Create Date: 2026-06-25 10:30:00.000000
"""

import csv
from pathlib import Path
from typing import Any, Sequence, Union

import sqlalchemy as sa

from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "f1a2b3c4d5e7"
down_revision: Union[str, None] = "d1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SEED_CSV = (
    Path(__file__).resolve().parents[2]
    / "app/modules/custom/order_intake/db/catalog_seed.csv"
)
_FLOAT_FIELDS = ("width_mm", "height_mm", "wall_thickness_mm", "weight_kg_per_m")


def _to_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value)


def _load_seed_rows() -> list[dict[str, Any]]:
    if not _SEED_CSV.exists():
        return []
    rows: list[dict[str, Any]] = []
    with _SEED_CSV.open(newline="", encoding="utf-8") as handle:
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


def upgrade() -> None:
    op.create_table(
        "oi_catalog",
        sa.Column("internal_code", sa.String(), nullable=False),
        sa.Column("profile_name", sa.String(), nullable=False),
        sa.Column("alloy", sa.String(), nullable=True),
        sa.Column("alloy_din", sa.String(), nullable=True),
        sa.Column("temper", sa.String(), nullable=True),
        sa.Column("width_mm", sa.Float(), nullable=True),
        sa.Column("height_mm", sa.Float(), nullable=True),
        sa.Column("wall_thickness_mm", sa.Float(), nullable=True),
        sa.Column("profile_type", sa.String(), nullable=True),
        sa.Column("weight_kg_per_m", sa.Float(), nullable=True),
        sa.Column("standard_lengths_mm", sa.String(), nullable=True),
        sa.Column("surface_finishes", sa.String(), nullable=True),
        sa.Column("tolerance_standard", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("edi_pia_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="A", nullable=False),
        sa.PrimaryKeyConstraint("internal_code"),
    )

    op.create_table(
        "oi_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer", sa.String(), nullable=False),
        sa.Column("source_filename", sa.String(), nullable=False),
        sa.Column("blob_path", sa.String(), nullable=False),
        sa.Column("order_ref", sa.String(), nullable=True),
        sa.Column("order_date", sa.Date(), nullable=True),
        sa.Column("delivery_date_default", sa.Date(), nullable=True),
        sa.Column("currency", sa.String(), server_default="EUR", nullable=False),
        sa.Column("status", sa.String(), server_default="in_review", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "oi_order_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("line_no", sa.String(), nullable=False),
        sa.Column("extracted_code", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("delivery_date", sa.Date(), nullable=True),
        sa.Column("length_mm", sa.Float(), nullable=True),
        sa.Column("alloy", sa.String(), nullable=True),
        sa.Column("resolved_internal_code", sa.String(), nullable=True),
        sa.Column("match_tier", sa.String(), nullable=True),
        sa.Column(
            "confidence_flags",
            pg.JSONB(),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["oi_orders.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_oi_order_lines_order_id", "oi_order_lines", ["order_id"], unique=False
    )

    op.create_table(
        "oi_edifact_exports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("edi_text", sa.Text(), nullable=False),
        sa.Column("blob_path", sa.String(), nullable=True),
        sa.Column("segment_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["oi_orders.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    rows = _load_seed_rows()
    if rows:
        catalog = sa.table(
            "oi_catalog",
            sa.column("internal_code", sa.String),
            sa.column("profile_name", sa.String),
            sa.column("alloy", sa.String),
            sa.column("alloy_din", sa.String),
            sa.column("temper", sa.String),
            sa.column("width_mm", sa.Float),
            sa.column("height_mm", sa.Float),
            sa.column("wall_thickness_mm", sa.Float),
            sa.column("profile_type", sa.String),
            sa.column("weight_kg_per_m", sa.Float),
            sa.column("standard_lengths_mm", sa.String),
            sa.column("surface_finishes", sa.String),
            sa.column("tolerance_standard", sa.String),
            sa.column("category", sa.String),
            sa.column("edi_pia_code", sa.String),
            sa.column("status", sa.String),
        )
        op.bulk_insert(catalog, rows)


def downgrade() -> None:
    op.drop_table("oi_edifact_exports")
    op.drop_index("ix_oi_order_lines_order_id", table_name="oi_order_lines")
    op.drop_table("oi_order_lines")
    op.drop_table("oi_orders")
    op.drop_table("oi_catalog")
