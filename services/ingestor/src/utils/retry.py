"""
Retry decorator with exponential backoff and jitter.

Usage::

    from src.utils.retry import retry

    @retry(max_attempts=3, base_delay=2.0, exceptions=(requests.Timeout,))
    def fetch_data(url: str) -> dict:
        ...
"""

from __future__ import annotations

import functools
import logging
import random
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    exponential: bool = True,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator that retries *func* on specified exceptions.

    Args:
        max_attempts: Total number of attempts (1 = no retry).
        base_delay:   Seconds to wait before the first retry.
        exponential:  If True, delay doubles each attempt (base * 2^attempt).
        exceptions:   Tuple of exception types that trigger a retry.

    Returns:
        Decorated function with automatic retry behaviour.

    Raises:
        The last caught exception once all attempts are exhausted.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc

                    if attempt == max_attempts - 1:
                        logger.error(
                            "All %d attempts exhausted for '%s': %s",
                            max_attempts,
                            func.__qualname__,
                            exc,
                        )
                        raise

                    delay = (base_delay * (2 ** attempt)) if exponential else base_delay
                    jitter = random.uniform(0.0, 1.0)
                    total = delay + jitter

                    logger.warning(
                        "Retry %d/%d for '%s' in %.2fs — %s: %s",
                        attempt + 1,
                        max_attempts - 1,
                        func.__qualname__,
                        total,
                        type(exc).__name__,
                        exc,
                    )
                    time.sleep(total)

            raise last_exc  # type: ignore[misc]  # unreachable but satisfies type checkers

        return wrapper  # type: ignore[return-value]

    return decorator
