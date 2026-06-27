"""SQLAlchemy models for the Order Intake feature.

Tables, one role each:
- ``oi_customers``: the registry of customers and the extraction strategy each
  one uses (deterministic text parser vs. the LLM spine). Selected at upload.
- ``oi_catalog``: the internal product catalog (seeded from the AluProfil CSV).
  The reconciliation join target; ``edi_pia_code`` feeds the EDIFACT PIA+1.
- ``oi_orders``: one row per ingested PDF order, with its lifecycle status.
- ``oi_order_lines``: extracted line items plus their reconciliation result.
- ``oi_edifact_exports``: generated EDIFACT ORDERS D.96A messages.
- ``oi_code_aliases``: learned ``(customer, their code) -> internal AE`` map,
  taught by every operator inline edit (auto-improving reconciliation).
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.services.postgresql.service import Database


class Customer(Database.Base):
    """A customer and the extraction strategy used for its PDFs."""

    __tablename__ = "oi_customers"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    extraction_strategy: Mapped[str] = mapped_column(String, nullable=False)
    api_key: Mapped[str | None] = mapped_column(String, nullable=True)
    api_base_url: Mapped[str | None] = mapped_column(String, nullable=True)
    api_model: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "display_name": self.display_name,
            "country": self.country,
            "extraction_strategy": self.extraction_strategy,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CatalogItem(Database.Base):
    """An internal AluProfil article (the reconciliation target)."""

    __tablename__ = "oi_catalog"

    internal_code: Mapped[str] = mapped_column(String, primary_key=True)
    profile_name: Mapped[str] = mapped_column(String, nullable=False)
    alloy: Mapped[str | None] = mapped_column(String, nullable=True)
    alloy_din: Mapped[str | None] = mapped_column(String, nullable=True)
    temper: Mapped[str | None] = mapped_column(String, nullable=True)
    width_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    wall_thickness_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    profile_type: Mapped[str | None] = mapped_column(String, nullable=True)
    weight_kg_per_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_lengths_mm: Mapped[str | None] = mapped_column(String, nullable=True)
    surface_finishes: Mapped[str | None] = mapped_column(String, nullable=True)
    tolerance_standard: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    edi_pia_code: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="A")

    def to_dict(self) -> dict[str, Any]:
        return {
            "internal_code": self.internal_code,
            "profile_name": self.profile_name,
            "alloy": self.alloy,
            "alloy_din": self.alloy_din,
            "temper": self.temper,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "wall_thickness_mm": self.wall_thickness_mm,
            "profile_type": self.profile_type,
            "weight_kg_per_m": self.weight_kg_per_m,
            "standard_lengths_mm": self.standard_lengths_mm,
            "surface_finishes": self.surface_finishes,
            "tolerance_standard": self.tolerance_standard,
            "category": self.category,
            "edi_pia_code": self.edi_pia_code,
            "status": self.status,
        }


class Order(Database.Base):
    """One ingested customer PDF order."""

    __tablename__ = "oi_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer: Mapped[str] = mapped_column(String, nullable=False)
    source_filename: Mapped[str] = mapped_column(String, nullable=False)
    blob_path: Mapped[str] = mapped_column(String, nullable=False)
    order_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    delivery_date_default: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String, nullable=False, server_default="EUR")
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="in_review"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    lines: Mapped[list["OrderLine"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderLine.line_no",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "customer": self.customer,
            "source_filename": self.source_filename,
            "blob_path": self.blob_path,
            "order_ref": self.order_ref,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "delivery_date_default": (
                self.delivery_date_default.isoformat()
                if self.delivery_date_default
                else None
            ),
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OrderLine(Database.Base):
    """One extracted line item and its reconciliation result."""

    __tablename__ = "oi_order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("oi_orders.id", ondelete="CASCADE"), nullable=False
    )
    line_no: Mapped[str] = mapped_column(String, nullable=False)
    extracted_code: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    length_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    alloy: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_internal_code: Mapped[str | None] = mapped_column(String, nullable=True)
    match_tier: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence_flags: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    order: Mapped["Order"] = relationship(back_populates="lines")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "line_no": self.line_no,
            "extracted_code": self.extracted_code,
            "description": self.description,
            "quantity": self.quantity,
            "unit": self.unit,
            "delivery_date": (
                self.delivery_date.isoformat() if self.delivery_date else None
            ),
            "length_mm": self.length_mm,
            "alloy": self.alloy,
            "resolved_internal_code": self.resolved_internal_code,
            "match_tier": self.match_tier,
            "confidence_flags": list(self.confidence_flags or []),
        }


class EdifactExport(Database.Base):
    """A generated EDIFACT ORDERS D.96A message for an order."""

    __tablename__ = "oi_edifact_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("oi_orders.id", ondelete="CASCADE"), nullable=False
    )
    edi_text: Mapped[str] = mapped_column(Text, nullable=False)
    blob_path: Mapped[str | None] = mapped_column(String, nullable=True)
    segment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "edi_text": self.edi_text,
            "blob_path": self.blob_path,
            "segment_count": self.segment_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CodeAlias(Database.Base):
    """A learned ``(customer, their code) -> internal AE code`` mapping.

    Every operator inline edit (``set_line_code``) teaches one of these rows: the
    next time the same customer sends the same printed code, reconciliation
    resolves it deterministically (tier ``learned``) without the LLM or the spec
    tiers — this is how the system "learns to recognise" repeated codes, the way
    Sabine's clerks do. The key is the *customer's* printed code, not the AE one
    (e.g. FensterSystem's ``PRO-045-0020`` -> ``AE-2024-071``).
    """

    __tablename__ = "oi_code_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_code: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Normalised (UPPER(TRIM(...))) customer-printed code, e.g. "PRO-045-0020".
    customer_part_code: Mapped[str] = mapped_column(String, nullable=False)
    internal_code: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "customer_code", "customer_part_code", name="uq_oi_code_alias"
        ),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "customer_code": self.customer_code,
            "customer_part_code": self.customer_part_code,
            "internal_code": self.internal_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
