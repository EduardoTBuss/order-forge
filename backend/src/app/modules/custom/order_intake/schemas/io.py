"""Input/output models for the Order Intake endpoints.

Every endpoint returns a dedicated, documented model. Serialisation from the ORM
lives here as classmethods so the routes stay thin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

from src.app.modules.custom.order_intake.logic.extract.base import KNOWN_STRATEGIES

if TYPE_CHECKING:
    from src.app.modules.custom.order_intake.db.models import (
        Customer,
        Order,
        OrderLine,
    )


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------


class CustomerOutput(BaseModel):
    """A registered customer and its extraction strategy."""

    code: str = Field(..., description="Customer slug.", examples=["bauprofil"])
    display_name: str = Field(
        ..., description="Human-readable name.", examples=["Bauprofil Bauelemente GmbH"]
    )
    country: str | None = Field(None, description="ISO country code.", examples=["DE"])
    extraction_strategy: str = Field(
        ...,
        description="How this customer's PDFs are extracted.",
        examples=["bauprofil_text"],
    )
    active: bool = Field(True, description="Whether the customer is selectable.")
    has_api_key: bool = Field(
        False,
        description="Whether an API key is stored (the key itself is never returned).",
        examples=[False],
    )
    api_base_url: str | None = Field(
        None,
        description="Provider base URL for 'llm_api' (OpenAI-compatible).",
        examples=["https://api.openai.com/v1"],
    )
    api_model: str | None = Field(
        None, description="Model for 'llm_api'.", examples=["gpt-4o-mini"]
    )

    @classmethod
    def from_orm_customer(cls, customer: Customer) -> CustomerOutput:
        return cls(
            code=customer.code,
            display_name=customer.display_name,
            country=customer.country,
            extraction_strategy=customer.extraction_strategy,
            active=customer.active,
            has_api_key=bool(customer.api_key),
            api_base_url=customer.api_base_url,
            api_model=customer.api_model,
        )


class CustomerListOutput(BaseModel):
    """The customers available to pick at upload, plus the known strategies."""

    customers: list[CustomerOutput] = Field(
        default_factory=list, description="Registered, active customers."
    )
    strategies: list[str] = Field(
        default_factory=list,
        description="Extraction strategies a new customer can use.",
        examples=[["bauprofil_text", "llm"]],
    )


class CreateCustomerInput(BaseModel):
    """Payload to register a new customer."""

    code: str = Field(
        ...,
        description="Unique slug (lowercase letters, digits, '-', '_').",
        examples=["acme-fr"],
        min_length=2,
        max_length=40,
        pattern=r"^[a-z0-9][a-z0-9_-]*$",
    )
    display_name: str = Field(
        ..., description="Human-readable name.", examples=["ACME Façades"], min_length=1
    )
    country: str | None = Field(None, description="ISO country code.", examples=["FR"])
    extraction_strategy: str = Field(
        default="bauprofil_text",
        description="Extraction strategy: bauprofil_text, ollama, or llm_api.",
        examples=["ollama"],
    )
    api_key: str | None = Field(
        default=None,
        description="API key for the 'llm_api' strategy (stored locally).",
        examples=["sk-..."],
    )
    api_base_url: str | None = Field(
        default=None,
        description="Provider base URL for 'llm_api' (default OpenAI). "
        "OpenAI-compatible, e.g. https://openrouter.ai/api/v1.",
        examples=["https://api.openai.com/v1"],
    )
    api_model: str | None = Field(
        default=None,
        description="Model for 'llm_api' (default gpt-4o-mini).",
        examples=["gpt-4o-mini"],
    )

    @field_validator("extraction_strategy")
    @classmethod
    def _validate_strategy(cls, value: str) -> str:
        if value not in KNOWN_STRATEGIES:
            raise ValueError(
                f"extraction_strategy must be one of {list(KNOWN_STRATEGIES)}"
            )
        return value


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


class OrderLineOutput(BaseModel):
    """One reconciled line item shown on the reconciliation screen."""

    id: int = Field(..., description="Line id.", examples=[42])
    line_no: str = Field(..., description="Position number from the PDF.", examples=["010"])
    extracted_code: str | None = Field(
        None, description="Code read from the customer PDF.", examples=["AE-2024-034"]
    )
    description: str | None = Field(
        None,
        description="Item description as extracted.",
        examples=["Winkelprofil gleichschenklig 40x40x3 mm, EN AW-6060 T66"],
    )
    quantity: float | None = Field(None, description="Ordered quantity.", examples=[150])
    unit: str | None = Field(
        None, description="EDIFACT unit of measure (DE 6411).", examples=["PCE"]
    )
    delivery_date: str | None = Field(
        None, description="Requested delivery date (ISO).", examples=["2026-09-15"]
    )
    length_mm: float | None = Field(
        None, description="Profile length in mm, if stated.", examples=[6000]
    )
    alloy: str | None = Field(None, description="Alloy as extracted.", examples=["EN AW-6060"])
    resolved_internal_code: str | None = Field(
        None,
        description="Internal catalog code resolved by reconciliation.",
        examples=["AE-2024-034"],
    )
    match_tier: str | None = Field(
        None, description="Reconciliation tier ('exact' or 'none').", examples=["exact"]
    )
    confidence_flags: list[str] = Field(
        default_factory=list,
        description="Concrete risk signals raised for this line.",
        examples=[["ambiguous_unit"]],
    )

    @classmethod
    def from_orm_line(cls, line: OrderLine) -> OrderLineOutput:
        return cls(
            id=line.id,
            line_no=line.line_no,
            extracted_code=line.extracted_code,
            description=line.description,
            quantity=line.quantity,
            unit=line.unit,
            delivery_date=(
                line.delivery_date.isoformat() if line.delivery_date else None
            ),
            length_mm=line.length_mm,
            alloy=line.alloy,
            resolved_internal_code=line.resolved_internal_code,
            match_tier=line.match_tier,
            confidence_flags=list(line.confidence_flags or []),
        )


class OrderSummaryOutput(BaseModel):
    """A row in the orders list, with status badges."""

    id: int = Field(..., description="Order id.", examples=[1])
    customer: str = Field(..., description="Selected customer.", examples=["bauprofil"])
    order_ref: str | None = Field(
        None, description="Customer order reference.", examples=["BP-2026-00487"]
    )
    source_filename: str = Field(
        ..., description="Uploaded PDF filename.", examples=["PO-2026-0615.pdf"]
    )
    status: str = Field(..., description="Lifecycle status.", examples=["in_review"])
    currency: str = Field(..., description="Order currency.", examples=["EUR"])
    created_at: str | None = Field(
        None, description="Creation timestamp (ISO).", examples=["2026-06-25T09:30:00Z"]
    )
    line_count: int = Field(..., description="Number of line items.", examples=[7])
    flagged_count: int = Field(
        ..., description="Lines carrying at least one flag.", examples=[1]
    )
    unmatched_count: int = Field(
        ..., description="Lines without a resolved code.", examples=[0]
    )

    @classmethod
    def from_orm_order(cls, order: Order) -> OrderSummaryOutput:
        flagged = sum(1 for ln in order.lines if ln.confidence_flags)
        unmatched = sum(1 for ln in order.lines if not ln.resolved_internal_code)
        return cls(
            id=order.id,
            customer=order.customer,
            order_ref=order.order_ref,
            source_filename=order.source_filename,
            status=order.status,
            currency=order.currency,
            created_at=order.created_at.isoformat() if order.created_at else None,
            line_count=len(order.lines),
            flagged_count=flagged,
            unmatched_count=unmatched,
        )


class OrderDetailOutput(OrderSummaryOutput):
    """The full reconciliation view for one order."""

    order_date: str | None = Field(
        None, description="Document date (ISO).", examples=["2026-06-15"]
    )
    delivery_date_default: str | None = Field(
        None, description="Header-level delivery date (ISO).", examples=["2026-09-15"]
    )
    blob_path: str = Field(
        ..., description="Blob path of the original PDF.", examples=["orders/ab12-PO.pdf"]
    )
    can_generate_edifact: bool = Field(
        ...,
        description="True when every line resolved (the EDIFACT gate is open).",
        examples=[True],
    )
    blocking_lines: list[str] = Field(
        default_factory=list,
        description="Line numbers blocking EDIFACT generation.",
        examples=[[]],
    )
    lines: list[OrderLineOutput] = Field(
        default_factory=list, description="Reconciled line items."
    )

    @classmethod
    def from_orm_order(cls, order: Order) -> OrderDetailOutput:
        blocking = [ln.line_no for ln in order.lines if not ln.resolved_internal_code]
        flagged = sum(1 for ln in order.lines if ln.confidence_flags)
        return cls(
            id=order.id,
            customer=order.customer,
            order_ref=order.order_ref,
            source_filename=order.source_filename,
            status=order.status,
            currency=order.currency,
            created_at=order.created_at.isoformat() if order.created_at else None,
            line_count=len(order.lines),
            flagged_count=flagged,
            unmatched_count=len(blocking),
            order_date=order.order_date.isoformat() if order.order_date else None,
            delivery_date_default=(
                order.delivery_date_default.isoformat()
                if order.delivery_date_default
                else None
            ),
            blob_path=order.blob_path,
            can_generate_edifact=bool(order.lines) and not blocking,
            blocking_lines=blocking,
            lines=[OrderLineOutput.from_orm_line(ln) for ln in order.lines],
        )


class OrderListOutput(BaseModel):
    """A list of order summaries."""

    orders: list[OrderSummaryOutput] = Field(
        default_factory=list, description="All ingested orders, newest first."
    )


class EdifactOutput(BaseModel):
    """A generated EDIFACT ORDERS D.96A message."""

    order_id: int = Field(..., description="Order id.", examples=[1])
    status: str = Field(..., description="Order status after export.", examples=["edifact_generated"])
    filename: str = Field(
        ..., description="Suggested .edi filename.", examples=["order-1.edi"]
    )
    segment_count: int = Field(
        ..., description="Total EDIFACT segments emitted.", examples=[47]
    )
    edi_text: str = Field(
        ...,
        description="The EDIFACT ORDERS D.96A message text.",
        examples=["UNB+UNOA:2+...'\nUNH+...'\n..."],
    )


class ClearResultOutput(BaseModel):
    """Result of clearing all orders and their files."""

    deleted_orders: int = Field(
        ..., description="Orders deleted (with their lines/exports).", examples=[3]
    )
    deleted_files: int = Field(
        ..., description="Blobs deleted (uploaded PDFs + generated .edi).", examples=[6]
    )


class UpdateLineInput(BaseModel):
    """Operator inline edit: assign an internal code to a line."""

    resolved_internal_code: str = Field(
        ...,
        description="An active internal catalog code to assign to the line.",
        examples=["AE-2024-034"],
        min_length=1,
    )
