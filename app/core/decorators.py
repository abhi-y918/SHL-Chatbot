"""Custom decorators: @retry, @log_execution, @validate_session."""

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from app.core.exceptions import SessionError
from app.utils.logger import get_logger

F = TypeVar("F", bound=Callable[..., Any])

_logger = get_logger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable[[F], F]:
    """Retry a function on exception up to *max_attempts* times with *delay* seconds between tries.

    Args:
        max_attempts: Maximum number of invocation attempts.
        delay: Seconds to wait between retries.

    Returns:
        Decorator that wraps the target function with retry logic.
    """

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
                        attempt,
                        max_attempts,
                        func.__name__,
                        exc,
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_exc  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator


def log_execution(func: F) -> F:
    """Log function entry, exit, and wall-clock execution time.

    Args:
        func: Function to wrap.

    Returns:
        Wrapped function with logging side-effects.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        _logger.info("→ Entering %s", func.__name__)
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            _logger.info("← Exiting %s (%.3fs)", func.__name__, elapsed)
            return result
        except Exception as exc:
            elapsed = time.perf_counter() - start
            _logger.error("✗ %s raised %s after %.3fs", func.__name__, exc, elapsed)
            raise

    return wrapper  # type: ignore[return-value]


def validate_session(func: F) -> F:
    """Ensure the first positional argument after *self* is a non-empty session_id string.

    Expects decorated method signature: method(self, session_id: str, ...).

    Raises:
        SessionError: If session_id is missing or empty.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        session_id: str | None = kwargs.get("session_id") or (
            args[1] if len(args) > 1 else None
        )
        if not session_id or not str(session_id).strip():
            raise SessionError("Invalid session", "session_id must be a non-empty string")
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
