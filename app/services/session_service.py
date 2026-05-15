"""Session lifecycle management."""

import threading
import time
from dataclasses import dataclass, field

from app.config import get_settings
from app.core.exceptions import SessionError
from app.utils.helpers import generate_session_id
from app.utils.logger import get_logger

_logger = get_logger(__name__)
_settings = get_settings()


@dataclass
class SessionRecord:
    """Metadata stored per active session."""

    session_id: str
    user_id: str
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    metadata: dict[str, str] = field(default_factory=dict)

    def touch(self) -> None:
        """Update the last-active timestamp to now."""
        self.last_active = time.time()

    def is_expired(self, timeout: int) -> bool:
        """Return True if the session has been idle longer than *timeout* seconds."""
        return (time.time() - self.last_active) > timeout


class SessionService:
    """Creates, retrieves, and destroys session records in a thread-safe registry."""

    def __init__(self) -> None:
        """Initialise an empty session registry with a lock."""
        self._sessions: dict[str, SessionRecord] = {}
        self._lock = threading.Lock()

    def create(self, user_id: str, metadata: dict[str, str] | None = None) -> SessionRecord:
        """Create and register a new session.

        Args:
            user_id: Owning user identifier.
            metadata: Optional extra key-value pairs.

        Returns:
            Newly created SessionRecord.
        """
        session_id = generate_session_id()
        record = SessionRecord(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )
        with self._lock:
            self._sessions[session_id] = record
        _logger.info("Session created: %s", session_id)
        return record

    def get(self, session_id: str) -> SessionRecord:
        """Retrieve a session record by ID, updating its last-active timestamp.

        Args:
            session_id: Target session identifier.

        Returns:
            The matching SessionRecord.

        Raises:
            SessionError: If the session does not exist.
        """
        with self._lock:
            record = self._sessions.get(session_id)
        if record is None:
            raise SessionError("Session not found", f"session_id={session_id}")
        record.touch()
        return record

    def delete(self, session_id: str) -> None:
        """Remove a session from the registry.

        Args:
            session_id: Session to delete.

        Raises:
            SessionError: If the session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise SessionError("Session not found", f"session_id={session_id}")
            del self._sessions[session_id]
        _logger.info("Session deleted: %s", session_id)

    def purge_expired(self) -> int:
        """Remove all sessions that have exceeded the configured timeout.

        Returns:
            Count of sessions purged.
        """
        timeout = _settings.session_timeout
        expired = [sid for sid, r in self._sessions.items() if r.is_expired(timeout)]
        with self._lock:
            for sid in expired:
                self._sessions.pop(sid, None)
        if expired:
            _logger.info("Purged %d expired session(s)", len(expired))
        return len(expired)
