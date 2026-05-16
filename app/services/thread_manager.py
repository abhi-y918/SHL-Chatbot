"""ThreadManager: one isolated thread per chat session."""

import threading
from collections.abc import Callable
from typing import Any

from app.utils.logger import get_logger

_logger = get_logger(__name__)
_thread_local = threading.local()


class ThreadManager:
    """Registry of per-session daemon threads."""

    def __init__(self) -> None:
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def spawn(
        self, session_id: str, target: Callable[..., Any],
        args: tuple[Any, ...] = (), kwargs: dict[str, Any] | None = None,
    ) -> threading.Thread:
        """Spawn a daemon thread for session_id."""
        with self._lock:
            thread = threading.Thread(
                target=self._run, args=(session_id, target, args, kwargs or {}),
                daemon=True, name=f"session-{session_id}",
            )
            self._threads[session_id] = thread
        thread.start()
        return thread

    def _run(
        self, session_id: str, target: Callable[..., Any],
        args: tuple[Any, ...], kwargs: dict[str, Any],
    ) -> None:
        _thread_local.session_id = session_id
        try:
            target(*args, **kwargs)
        except Exception as exc:
            _logger.error("Thread %s error: %s", session_id, exc)
        finally:
            with self._lock:
                self._threads.pop(session_id, None)

    def is_alive(self, session_id: str) -> bool:
        """Check if thread is running."""
        t = self._threads.get(session_id)
        return t is not None and t.is_alive()
