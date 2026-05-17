"""Custom decorators: @retry, @log_execution, @validate_session."""

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from app.core.exceptions import SessionError
from app.utils.logger import get_logger

_logger = get_logger(__name__)
F = TypeVar("F", bound=Callable[..., Any])


def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable[[F], F]:
    """Retry a function on exception up to max_attempts times."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    _logger.warning(
                        "Attempt %d/%d failed for %s: %s",
                        attempt, max_attempts, func.__name__, exc,
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_exc  # type: ignore[misc]
        return wrapper  # type: ignore[return-value]

    return decorator


def log_execution(func: F) -> F:
    """Log function entry, exit, and wall-clock execution time."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        _logger.info("-> %s", func.__name__)
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            _logger.info("<- %s (%.3fs)", func.__name__, time.perf_counter() - start)
            return result
        except Exception as exc:
            _logger.error("XX %s raised %s", func.__name__, exc)
            raise
    return wrapper  # type: ignore[return-value]


def validate_session(func: F) -> F:
    """Ensure session_id is a non-empty string."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        sid = kwargs.get("session_id") or (args[1] if len(args) > 1 else None)
        if not sid or not str(sid).strip():
            raise SessionError("Invalid session", "session_id must be non-empty")
        return func(*args, **kwargs)
    return wrapper  # type: ignore[return-value]
