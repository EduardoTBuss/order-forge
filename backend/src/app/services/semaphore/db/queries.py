from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from sqlalchemy import delete, func, select

from src.app.services.postgresql.service import Database
from src.app.services.semaphore.db.models import ConsumptionLimit, Usage

PeriodType = Literal["minute", "daily", "monthly"]

_PERIOD_INTERVALS: dict[PeriodType, timedelta] = {
    "minute": timedelta(minutes=1),
    "daily": timedelta(days=1),
    "monthly": timedelta(days=30),
}


def _get_period_start(period: PeriodType) -> datetime:
    """Get the start timestamp for a given period."""
    return datetime.now(UTC) - _PERIOD_INTERVALS[period]


async def log_consumption(path: str, tokens: int, cost: float) -> None:
    """Log consumption to the usages table."""
    async with Database.get_async_db() as db:
        record = Usage(
            path=path,
            tokens=tokens,
            cost=cost,
            timestamp=datetime.now(UTC),
        )
        db.add(record)
        await db.commit()


async def get_total_consumption(
    path: str | None = None,
    period: PeriodType | None = None,
) -> tuple[int, float]:
    """Get total consumption for a given path and period."""
    async with Database.get_async_db() as db:
        query = select(
            func.coalesce(func.sum(Usage.tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(Usage.cost), 0.0).label("total_cost"),
        )

        if period:
            period_start = _get_period_start(period)
            query = query.where(Usage.timestamp >= period_start)

        if path:
            query = query.where(Usage.path == path)

        result = await db.execute(query)
        row = result.first()
        total_tokens, total_cost = row if row else (0, 0.0)

        return int(total_tokens), float(total_cost)


async def get_consumptions(
    period: PeriodType | None = None,
    path: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Get the latest consumptions with optional filtering."""
    async with Database.get_async_db() as db:
        query = select(Usage).order_by(Usage.timestamp.desc())

        if period:
            period_start = _get_period_start(period)
            query = query.where(Usage.timestamp >= period_start)

        if path:
            query = query.where(Usage.path == path)

        if limit:
            query = query.limit(limit)

        result = await db.execute(query)

        return [record.to_dict() for record in result.scalars().all()]


async def get_aggregated_consumption(
    period: PeriodType,
) -> dict[str, dict[str, float | int]]:
    """Get aggregated consumption by path for a given period."""
    period_start = _get_period_start(period)

    async with Database.get_async_db() as db:
        query = (
            select(
                Usage.path,
                func.sum(Usage.tokens).label("total_tokens"),
                func.sum(Usage.cost).label("total_cost"),
            )
            .where(Usage.timestamp >= period_start)
            .group_by(Usage.path)
        )

        result = await db.execute(query)
        rows = result.all()

        return {
            path: {"tokens": int(total_tokens), "cost": float(total_cost)}
            for path, total_tokens, total_cost in rows
        }


async def get_limit(
    period: PeriodType, path: str | None = None
) -> ConsumptionLimit | None:
    """Get the consumption limit object for a given period and optional path."""
    async with Database.get_async_db() as db:
        if path:
            query = select(ConsumptionLimit).where(
                ConsumptionLimit.period == period,
                ConsumptionLimit.path == path,
            )
        else:
            query = select(ConsumptionLimit).where(
                ConsumptionLimit.period == period,
                ConsumptionLimit.path.is_(None),
            )

        result = await db.execute(query)
        return result.scalar_one_or_none()


async def set_limit(
    period: PeriodType,
    path: str | None = None,
    max_cost: float | None = None,
    max_tokens: int | None = None,
) -> None:
    """Set or update a consumption limit for a given period and optional path."""
    async with Database.get_async_db() as db:
        if path:
            existing_query = select(ConsumptionLimit).where(
                ConsumptionLimit.period == period,
                ConsumptionLimit.path == path,
            )
        else:
            existing_query = select(ConsumptionLimit).where(
                ConsumptionLimit.period == period,
                ConsumptionLimit.path.is_(None),
            )

        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()

        if existing:
            existing.max_cost = max_cost
            existing.max_tokens = max_tokens
        else:
            new_limit = ConsumptionLimit(
                period=period,
                path=path,
                max_cost=max_cost,
                max_tokens=max_tokens,
            )
            db.add(new_limit)

        await db.commit()


async def delete_limit(period: PeriodType, path: str | None = None) -> bool:
    """Delete a consumption limit. Returns True if a limit was deleted."""
    async with Database.get_async_db() as db:
        if path:
            stmt = delete(ConsumptionLimit).where(
                ConsumptionLimit.period == period,
                ConsumptionLimit.path == path,
            )
        else:
            stmt = delete(ConsumptionLimit).where(
                ConsumptionLimit.period == period,
                ConsumptionLimit.path.is_(None),
            )

        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0  # ty: ignore[unresolved-attribute]


async def get_all_limits() -> list[dict[str, Any]]:
    """Get all consumption limits."""
    async with Database.get_async_db() as db:
        query = select(ConsumptionLimit).order_by(
            ConsumptionLimit.period, ConsumptionLimit.path
        )
        result = await db.execute(query)
        return [limit.to_dict() for limit in result.scalars().all()]
