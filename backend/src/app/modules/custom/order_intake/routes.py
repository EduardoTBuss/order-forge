"""FastAPI routes for the Order Intake feature (thin — delegates to logic/)."""

import logging

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.exc import IntegrityError

from src.app.modules.custom.order_intake.db.queries import (
    create_customer,
    delete_customer,
    get_order,
    list_customers,
    list_orders,
)
from src.app.modules.custom.order_intake.logic.edifact import EdifactValidationError
from src.app.modules.custom.order_intake.logic.extract import (
    ExtractionNotAvailableError,
)
from src.app.modules.custom.order_intake.logic.extract.llm import LLMExtractionError
from src.app.modules.custom.order_intake.logic.extract.base import KNOWN_STRATEGIES
from src.app.modules.custom.order_intake.logic.flow import (
    CatalogCodeNotFoundError,
    CustomerNotFoundError,
    LineNotFoundError,
    OrderNotFoundError,
    clear_all_orders,
    generate_order_edifact,
    generate_order_edifact,
    run_intake,
    set_line_code,
)
from src.app.modules.custom.order_intake.logic.ingest import load_pdf
from src.app.modules.custom.order_intake.schemas.io import (
    CreateCustomerInput,
    ClearResultOutput,
    CustomerListOutput,
    CustomerListOutput,
    CustomerOutput,
    EdifactOutput,
    OrderDetailOutput,
    OrderListOutput,
    OrderSummaryOutput,
    UpdateLineInput,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["order_intake"])


@router.get("/customers")
async def order_intake_list_customers() -> CustomerListOutput:
    """List selectable customers and the available extraction strategies."""
    customers = await list_customers()
    return CustomerListOutput(
        customers=[CustomerOutput.from_orm_customer(c) for c in customers],
        strategies=list(KNOWN_STRATEGIES),
    )


@router.post("/customers", status_code=201)
async def order_intake_create_customer(req: CreateCustomerInput) -> CustomerOutput:
    """Register a new customer with its extraction strategy."""
    if req.extraction_strategy == "llm_api" and not req.api_key:
        raise HTTPException(
            status_code=400,
            detail="The 'llm_api' strategy requires an api_key.",
        )
    if req.api_key and req.api_key.strip().lower().startswith("http"):
        raise HTTPException(
            status_code=400,
            detail="That looks like a URL, not an API key. Paste the provider "
            "key (e.g. OpenAI 'sk-...').",
        )
    try:
        customer = await create_customer(
            code=req.code,
            display_name=req.display_name,
            country=req.country,
            extraction_strategy=req.extraction_strategy,
            api_key=req.api_key,
            api_base_url=req.api_base_url,
            api_model=req.api_model,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail=f"Customer '{req.code}' already exists."
        )
    return CustomerOutput.from_orm_customer(customer)


@router.post("/orders", status_code=201)
async def order_intake_create_order(
    file: UploadFile = File(...),
    customer_code: str = Form(...),
) -> OrderDetailOutput:
    """Upload a customer PDF, extract, reconcile, and persist a draft order."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    filename = file.filename or "order.pdf"
    try:
        order_id = await run_intake(filename, content, customer_code)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ExtractionNotAvailableError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except LLMExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Intake failed for %s", filename)
        raise HTTPException(status_code=500, detail=f"Intake failed: {exc}")

    order = await get_order(order_id)
    if order is None:
        raise HTTPException(status_code=500, detail="Order vanished after creation.")
    return OrderDetailOutput.from_orm_order(order)


@router.delete("/customers/{code}", status_code=204)
async def order_intake_delete_customer(code: str) -> Response:
    """Delete a registered customer."""
    deleted = await delete_customer(code)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"Customer '{code}' not found.")
    return Response(status_code=204)


@router.get("/orders")
async def order_intake_list_orders() -> OrderListOutput:
    """List all ingested orders (newest first) with status counters."""
    orders = await list_orders()
    return OrderListOutput(
        orders=[OrderSummaryOutput.from_orm_order(order) for order in orders]
    )


@router.delete("/orders")
async def order_intake_clear_orders() -> ClearResultOutput:
    """Clear all orders and their files (uploaded PDFs + generated .edi).

    A demo "reset": removes orders, their blobs and provenance. Customers, the
    learned code map and the catalog are kept.
    """
    result = await clear_all_orders()
    return ClearResultOutput(**result)


@router.get("/orders/{order_id}")
async def order_intake_get_order(order_id: int) -> OrderDetailOutput:
    """Fetch the full reconciliation view for one order."""
    order = await get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")
    return OrderDetailOutput.from_orm_order(order)


@router.get("/orders/{order_id}/source-pdf")
async def order_intake_get_source_pdf(order_id: int) -> Response:
    """Stream the original PDF for the side-by-side reconciliation pane."""
    order = await get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")
    try:
        content = load_pdf(order.blob_path)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"PDF not found: {exc}")
    return Response(content=content, media_type="application/pdf")


@router.patch("/orders/{order_id}/lines/{line_id}")
async def order_intake_update_line(
    order_id: int, line_id: int, req: UpdateLineInput
) -> OrderDetailOutput:
    """Operator inline edit: assign an internal catalog code to a line."""
    try:
        order = await set_line_code(order_id, line_id, req.resolved_internal_code)
    except LineNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except CatalogCodeNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return OrderDetailOutput.from_orm_order(order)


@router.post("/orders/{order_id}/edifact", status_code=201)
async def order_intake_generate_edifact(order_id: int) -> EdifactOutput:
    """Approve & generate the EDIFACT export (gated on the PIA+1 validation)."""
    try:
        order, edi_text = await generate_order_edifact(order_id)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")
    except EdifactValidationError as exc:
        raise HTTPException(
            status_code=409,
            detail={"message": exc.reason, "blocking_lines": exc.blocking_lines},
        )

    segment_count = edi_text.strip().count("\n") + 1
    return EdifactOutput(
        order_id=order.id,
        status=order.status,
        filename=f"order-{order.id}.edi",
        segment_count=segment_count,
        edi_text=edi_text,
    )
