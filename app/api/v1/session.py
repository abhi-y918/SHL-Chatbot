"""POST /v1/session and DELETE /v1/session/{session_id} endpoints."""

from fastapi import APIRouter, HTTPException

from app.enums.status import StatusCode
from app.models.request import SessionRequest
from app.models.response import SessionResponse
from app.services.session_service import SessionService
from app.utils.logger import get_logger

router = APIRouter()
_logger = get_logger(__name__)
_session_service = SessionService()


@router.post("/session", response_model=SessionResponse, status_code=StatusCode.CREATED)
def create_session(request: SessionRequest) -> SessionResponse:
    """Create a new session for the given user.

    Args:
        request: SessionRequest with user_id and optional metadata.

    Returns:
        SessionResponse containing the new session_id.
    """
    record = _session_service.create(
        user_id=request.user_id,
        metadata=request.metadata,
    )
    return SessionResponse(session_id=record.session_id, status=StatusCode.CREATED)


@router.delete("/session/{session_id}", status_code=StatusCode.OK)
def delete_session(session_id: str) -> dict[str, str]:
    """Terminate and remove a session.

    Args:
        session_id: ID of the session to remove.

    Returns:
        Confirmation dict with deleted session_id.

    Raises:
        HTTPException: 404 if the session does not exist.
    """
    try:
        _session_service.delete(session_id)
    except Exception as exc:
        raise HTTPException(status_code=StatusCode.NOT_FOUND, detail=str(exc)) from exc
    return {"deleted_session_id": session_id}
