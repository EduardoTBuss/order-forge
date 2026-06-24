import logging
from typing import Any

from src.app.services.semaphore.db.models import ConsumptionLimit
from src.app.services.semaphore.db.queries import (
    PeriodType,
    delete_limit,
    get_aggregated_consumption,
    get_all_limits,
    get_consumptions,
    get_limit,
    get_total_consumption,
    log_consumption,
    set_limit,
)

logger = logging.getLogger(__name__)


class NoTokensAvailableError(Exception):
    """Exception raised when a path has no tokens available."""


class SemaphoreService:
    @staticmethod
    async def log_consumption(path: str, tokens: int, cost: float) -> None:
        """Log consumption for a given path."""
        await log_consumption(path, tokens, cost)

    @staticmethod
    async def get_total_consumption(
        path: str | None = None,
        period: PeriodType | None = None,
    ) -> tuple[int, float]:
        """Get total consumption for a given path and period."""
        return await get_total_consumption(path, period)

    @staticmethod
    async def _check_limit(
        limit: ConsumptionLimit,
        tokens: int,
        cost: float,
        period: PeriodType,
        scope_desc: str,
    ) -> bool:
        """Check if consumption is within a specific limit. Returns False if blocked."""
        if limit.max_cost is not None:
            passed = cost < limit.max_cost
            logger.info(
                f"[LIMIT CHECK] period={period} {scope_desc} "
                f"cost={cost:.4f}/{limit.max_cost:.4f} -> {'PASS' if passed else 'BLOCKED'}"
            )
            if not passed:
                return False

        if limit.max_tokens is not None:
            passed = tokens < limit.max_tokens
            logger.info(
                f"[LIMIT CHECK] period={period} {scope_desc} "
                f"tokens={tokens}/{limit.max_tokens} -> {'PASS' if passed else 'BLOCKED'}"
            )
            if not passed:
                return False

        return True

    @staticmethod
    async def has_consumption_available(
        path: str | None = None,
    ) -> bool:
        """Check if consumption is within limits stored in the database."""
        periods: list[PeriodType] = ["minute", "daily", "monthly"]

        for period in periods:
            # Check path-specific limit first (if a path was provided)
            if path:
                path_limit = await get_limit(period, path)
                if path_limit is not None:
                    tokens, cost = await SemaphoreService.get_total_consumption(
                        path, period
                    )
                    if not await SemaphoreService._check_limit(
                        path_limit, tokens, cost, period, f"endpoint={path}"
                    ):
                        return False

            # Always check global limit
            global_limit = await get_limit(period, None)
            if global_limit is not None:
                # For global limits, sum consumption across ALL paths
                tokens, cost = await SemaphoreService.get_total_consumption(
                    None, period
                )
                if not await SemaphoreService._check_limit(
                    global_limit, tokens, cost, period, "scope=global"
                ):
                    return False

        return True

    @staticmethod
    async def aggregated_consumption(
        period: PeriodType,
    ) -> dict[str, dict[str, float | int]]:
        """Get aggregated consumption by path for a given period."""
        return await get_aggregated_consumption(period)

    @staticmethod
    async def get_consumptions(
        period: PeriodType | None = None,
        path: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get the latest consumptions with optional filtering."""
        return await get_consumptions(period, path, limit)

    @staticmethod
    async def set_limit(
        period: PeriodType,
        path: str | None = None,
        max_cost: float | None = None,
        max_tokens: int | None = None,
    ) -> None:
        """Set or update a consumption limit."""
        await set_limit(period, path, max_cost, max_tokens)

    @staticmethod
    async def get_limit(
        period: PeriodType,
        path: str | None = None,
    ) -> ConsumptionLimit | None:
        """Get a consumption limit."""
        return await get_limit(period, path)

    @staticmethod
    async def delete_limit(
        period: PeriodType,
        path: str | None = None,
    ) -> bool:
        """Delete a consumption limit. Returns True if deleted."""
        return await delete_limit(period, path)

    @staticmethod
    async def get_all_limits() -> list[dict[str, Any]]:
        """Get all consumption limits."""
        return await get_all_limits()
