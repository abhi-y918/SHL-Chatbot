"""Session lifecycle management (minimal — API is stateless)."""

import threading
import time
from dataclasses import dataclass, field

from app.utils.logger import get_logger

_logger = get_logger(__name__)


@dataclass
class SessionRecord:
    """Metadata stored per active session."""

    session_id: str
    user_id: str
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.last_active = time.time()


class SessionService:
    """Thread-safe session registry."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}
        self._lock = threading.Lock()

    def create(self, session_id: str, user_id: str) -> SessionRecord:
        """Create and register a new session."""
        record = SessionRecord(session_id=session_id, user_id=user_id)
        with self._lock:
            self._sessions[session_id] = record
        _logger.info("Session created: %s", session_id)
        return record

    def exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self._sessions

    def delete(self, session_id: str) -> None:
        """Remove a session."""
        with self._lock:
            self._sessions.pop(session_id, None)
        _logger.info("Session deleted: %s", session_id)
