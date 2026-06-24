import asyncio
import logging
import re
from typing import Any, Callable

from openai import RateLimitError

func_type = Callable[..., Any]


class MaxRetriesExceeded(Exception):
    """Exception raised when the maximum number of retries is exceeded."""

    def __init__(self, max_retries: int) -> None:
        self.message = f"Maximum number of retries exceeded: {max_retries} attempts"
        super().__init__(self.message)


def __extract_wait_time(error: RateLimitError) -> int:
    """Extracts the waiting time from a RateLimitError message."""
    match = re.search(r"(?<=after )\d+(?= seconds)", str(error))
    return int(match.group(0)) if match else 60


def retry_on_rate_limit(
    max_retries: int = 3,
) -> Callable[[func_type], func_type]:
    """
    This decorator wraps a function and automatically retries its execution
    if a RateLimitError is raised, waiting for the recommended time extracted
    from the error message. If the function still fails after `max_retries`
    attempts, it raises a MaxRetriesExceeded exception.
    """

    def decorator(func: func_type) -> func_type:
        async def wrapper(*args, **kwargs) -> Any:
            for _ in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except RateLimitError as e:
                    wait_time = __extract_wait_time(e)
                    logging.info(f"RETRYING AFTER {wait_time}")
                    await asyncio.sleep(wait_time)

            raise MaxRetriesExceeded(max_retries)

        return wrapper

    return decorator
