"""Async database access for the Order Intake feature.

All persistence goes through the shared ``Database`` async session helper so the
module reuses the same engine/pool as the rest of the app. The catalog match
uses ``UPPER(TRIM(...))`` on both sides to mirror MetallSoft's exact-match rule.
"""

from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from src.app.modules.custom.order_intake.db.models import (
    CatalogItem,
    CodeAlias,
    Customer,
    EdifactExport,
    Order,
    OrderLine,
)
from src.app.services.postgresql.service import Database


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------


async def customers_count() -> int:
    """Return the number of registered customers."""
    async with Database.get_async_db() as session:
        result = await session.execute(select(func.count()).select_from(Customer))
        return int(result.scalar_one())


async def bulk_upsert_customers(rows: list[dict[str, Any]]) -> int:
    """Insert customer rows idempotently (no-op on existing code)."""
    if not rows:
        return 0
    async with Database.get_async_db() as session:
        stmt = pg_insert(Customer).values(rows).on_conflict_do_nothing(
            index_elements=["code"]
        )
        await session.execute(stmt)
    return len(rows)


async def list_customers() -> list[Customer]:
    """Return all active customers, ordered by display name."""
    async with Database.get_async_db() as session:
        result = await session.execute(
            select(Customer)
            .where(Customer.active.is_(True))
            .order_by(Customer.display_name)
        )
        return list(result.scalars().all())


async def get_customer(code: str) -> Customer | None:
    """Fetch a single customer by code."""
    async with Database.get_async_db() as session:
        result = await session.execute(select(Customer).where(Customer.code == code))
        return result.scalar_one_or_none()


async def delete_customer(code: str) -> int:
    """Delete a customer by code; return the number of rows deleted."""
    async with Database.get_async_db() as session:
        result = await session.execute(delete(Customer).where(Customer.code == code))
        return int(result.rowcount or 0)


async def create_customer(
    code: str,
    display_name: str,
    country: str | None,
    extraction_strategy: str,
    api_key: str | None = None,
    api_base_url: str | None = None,
    api_model: str | None = None,
) -> Customer:
    """Insert a new customer and return it."""
    async with Database.get_async_db() as session:
        session.add(
            Customer(
                code=code,
                display_name=display_name,
                country=country,
                extraction_strategy=extraction_strategy,
                api_key=api_key,
                api_base_url=api_base_url,
                api_model=api_model,
                active=True,
            )
        )
        await session.flush()
    created = await get_customer(code)
    assert created is not None
    return created


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


async def catalog_count() -> int:
    """Return the number of rows currently in the catalog table."""
    async with Database.get_async_db() as session:
        result = await session.execute(select(func.count()).select_from(CatalogItem))
        return int(result.scalar_one())


async def bulk_upsert_catalog(rows: list[dict[str, Any]]) -> int:
    """Insert catalog rows idempotently (no-op on existing internal_code)."""
    if not rows:
        return 0
    async with Database.get_async_db() as session:
        stmt = pg_insert(CatalogItem).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["internal_code"])
        await session.execute(stmt)
    return len(rows)


async def list_active_catalog() -> list[CatalogItem]:
    """Return all active catalog items, ordered by internal code."""
    async with Database.get_async_db() as session:
        result = await session.execute(
            select(CatalogItem)
            .where(CatalogItem.status == "A")
            .order_by(CatalogItem.internal_code)
        )
        return list(result.scalars().all())


async def find_catalog_by_code(code: str) -> CatalogItem | None:
    """Exact, normalised lookup of an active catalog item by internal code.

    Mirrors MetallSoft: ``UPPER(TRIM(code)) = UPPER(TRIM(input))`` and the
    article must be active (``status = 'A'``).
    """
    normalised = code.strip().upper()
    async with Database.get_async_db() as session:
        result = await session.execute(
            select(CatalogItem).where(
                func.upper(func.trim(CatalogItem.internal_code)) == normalised,
                CatalogItem.status == "A",
            )
        )
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Learned code aliases  (customer's printed code -> internal AE code)
# ---------------------------------------------------------------------------


def normalize_part_code(code: str | None) -> str | None:
    """Normalise a customer-printed code for the alias key (UPPER(TRIM))."""
    if not code:
        return None
    cleaned = code.strip().upper()
    return cleaned or None


async def get_code_alias_map(customer_code: str) -> dict[str, str]:
    """Return the customer's learned ``part_code(normalised) -> internal_code``.

    Used at intake to resolve repeated customer codes deterministically, before
    any spec/fuzzy tier or LLM guess.
    """
    async with Database.get_async_db() as session:
        result = await session.execute(
            select(
                CodeAlias.customer_part_code, CodeAlias.internal_code
            ).where(CodeAlias.customer_code == customer_code)
        )
        return {row[0]: row[1] for row in result.all()}


async def upsert_code_alias(
    customer_code: str, customer_part_code: str, internal_code: str
) -> None:
    """Teach/refresh one ``(customer, their code) -> internal code`` mapping.

    Called whenever an operator assigns an internal code to a line that carried a
    customer-printed code. Idempotent: re-assigning updates the target.
    """
    part = normalize_part_code(customer_part_code)
    if not part:
        return
    async with Database.get_async_db() as session:
        stmt = (
            pg_insert(CodeAlias)
            .values(
                customer_code=customer_code,
                customer_part_code=part,
                internal_code=internal_code.strip().upper(),
            )
            .on_conflict_do_update(
                constraint="uq_oi_code_alias",
                set_={
                    "internal_code": internal_code.strip().upper(),
                    "updated_at": func.now(),
                },
            )
        )
        await session.execute(stmt)


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


async def create_order_with_lines(order: Order, lines: list[OrderLine]) -> int:
    """Persist an order and its lines in a single transaction; return order id."""
    async with Database.get_async_db() as session:
        order.lines = lines
        session.add(order)
        await session.flush()
        order_id = order.id
    return order_id


async def get_order(order_id: int) -> Order | None:
    """Fetch a single order with its lines eagerly loaded."""
    async with Database.get_async_db() as session:
        result = await session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.lines))
        )
        return result.scalar_one_or_none()


async def list_orders() -> list[Order]:
    """List all orders (with lines) newest first."""
    async with Database.get_async_db() as session:
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.lines))
            .order_by(Order.created_at.desc(), Order.id.desc())
        )
        return list(result.scalars().all())


async def set_order_status(order_id: int, status: str) -> None:
    """Update the lifecycle status of an order."""
    async with Database.get_async_db() as session:
        await session.execute(
            update(Order).where(Order.id == order_id).values(status=status)
        )


async def save_edifact_export(
    order_id: int, edi_text: str, blob_path: str | None, segment_count: int
) -> int:
    """Persist a generated EDIFACT message and return its id."""
    async with Database.get_async_db() as session:
        result = await session.execute(
            insert(EdifactExport)
            .values(
                order_id=order_id,
                edi_text=edi_text,
                blob_path=blob_path,
                segment_count=segment_count,
            )
            .returning(EdifactExport.id)
        )
        return int(result.scalar_one())


async def get_order_line(line_id: int) -> OrderLine | None:
    """Fetch a single order line by id."""
    async with Database.get_async_db() as session:
        result = await session.execute(
            select(OrderLine).where(OrderLine.id == line_id)
        )
        return result.scalar_one_or_none()


async def delete_all_orders() -> int:
    """Delete every order (cascades to lines + EDIFACT exports). Returns count."""
    async with Database.get_async_db() as session:
        result = await session.execute(delete(Order))
        return int(result.rowcount or 0)


async def update_line_resolution(
    line_id: int, internal_code: str, match_tier: str, flags: list[str]
) -> None:
    """Set a line's resolved code, tier and recomputed confidence flags."""
    async with Database.get_async_db() as session:
        await session.execute(
            update(OrderLine)
            .where(OrderLine.id == line_id)
            .values(
                resolved_internal_code=internal_code,
                match_tier=match_tier,
                confidence_flags=flags,
            )
        )
