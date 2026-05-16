"""POST/DELETE /session — kept for OOP spec compliance."""

from fastapi import APIRouter, HTTPException

from app.services.session_service import SessionService
from app.utils.helpers import generate_session_id

router = APIRouter()
_session_svc = SessionService()


@router.post("/session", status_code=201)
def create_session(user_id: str = "anonymous") -> dict[str, str]:
    """Create a new session."""
    sid = generate_session_id()
    _session_svc.create(sid, user_id)
    return {"session_id": sid}


@router.delete("/session/{session_id}")
def delete_session(session_id: str) -> dict[str, str]:
    """Delete a session."""
    if not _session_svc.exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    _session_svc.delete(session_id)
    return {"deleted_session_id": session_id}
