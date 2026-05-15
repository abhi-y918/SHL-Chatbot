"""ThreadManager: one isolated thread per chat session."""

import threading
from collections.abc import Callable
from typing import Any

from app.core.exceptions import SessionError
from app.utils.logger import get_logger

_logger = get_logger(__name__)

_thread_local = threading.local()


class ThreadManager:
    """Manages a registry of per-session threads with strict isolation.

    Each session ID maps to exactly one daemon Thread. Threads share no
    mutable state — all context is passed via thread-local storage.
    """

    def __init__(self) -> None:
        """Initialise an empty thread registry and a registry lock."""
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def spawn(
        self,
        session_id: str,
        target: Callable[..., Any],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> threading.Thread:
        """Spawn a new daemon thread for *session_id*.

        Args:
            session_id: Unique session identifier.
            target: Callable to run in the thread.
            args: Positional arguments for *target*.
            kwargs: Keyword arguments for *target*.

        Returns:
            The started Thread.

        Raises:
            SessionError: If a thread for *session_id* already exists.
        """
        with self._lock:
            if session_id in self._threads:
                raise SessionError(
                    "Thread already exists",
                    f"session_id={session_id} already has a running thread",
                )
            thread = threading.Thread(
                target=self._run_in_context,
                args=(session_id, target, args, kwargs or {}),
                daemon=True,
                name=f"session-{session_id}",
            )
            self._threads[session_id] = thread
        thread.start()
        _logger.info("Thread spawned for session: %s", session_id)
        return thread

    def _run_in_context(
        self,
        session_id: str,
        target: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Wrap *target* with thread-local session context and clean up on exit."""
        _thread_local.session_id = session_id
        try:
            target(*args, **kwargs)
        except Exception as exc:
            _logger.error("Thread %s raised: %s", session_id, exc)
        finally:
            self._cleanup(session_id)

    def _cleanup(self, session_id: str) -> None:
        """Remove the thread entry for *session_id* from the registry."""
        with self._lock:
            self._threads.pop(session_id, None)
        _logger.info("Thread cleaned up for session: %s", session_id)

    def terminate(self, session_id: str) -> None:
        """Mark a session thread for cleanup (threads cannot be force-killed in Python).

        Args:
            session_id: Session whose thread should be removed from tracking.
        """
        self._cleanup(session_id)

    def is_alive(self, session_id: str) -> bool:
        """Check if a thread is currently running for *session_id*.

        Args:
            session_id: Session to query.

        Returns:
            True if the thread exists and is alive.
        """
        thread = self._threads.get(session_id)
        return thread is not None and thread.is_alive()
