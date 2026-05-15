"""POST /v1/chat endpoint."""

from fastapi import APIRouter, HTTPException

from app.enums.agent_types import AgentType
from app.enums.status import StatusCode
from app.graph.builder import build_graph
from app.models.request import ChatRequest
from app.models.response import ChatResponse
from app.services.session_service import SessionService
from app.utils.logger import get_logger

router = APIRouter()
_logger = get_logger(__name__)
_session_service = SessionService()
_graph = build_graph()


@router.post("/chat", response_model=ChatResponse, status_code=StatusCode.OK)
def chat(request: ChatRequest) -> ChatResponse:
    """Process a user chat message through the LangGraph pipeline.

    Args:
        request: ChatRequest containing session_id and message.

    Returns:
        ChatResponse with the assistant reply.

    Raises:
        HTTPException: 404 if the session does not exist.
        HTTPException: 500 on unhandled pipeline errors.
    """
    _validate_session_exists(request.session_id)
    initial_state = _build_initial_state(request)
    final_state = _invoke_graph(initial_state)
    return _build_response(request.session_id, final_state)


def _validate_session_exists(session_id: str) -> None:
    """Raise 404 if the session is not registered."""
    try:
        _session_service.get(session_id)
    except Exception as exc:
        raise HTTPException(status_code=StatusCode.NOT_FOUND, detail=str(exc)) from exc


def _build_initial_state(request: ChatRequest) -> dict[str, object]:
    """Construct the initial LangGraph state from the request."""
    return {
        "session_id": request.session_id,
        "user_input": request.message,
        "messages": [],
        "metadata": {},
    }


def _invoke_graph(state: dict[str, object]) -> dict[str, object]:
    """Run the compiled graph and return the final state."""
    try:
        return dict(_graph.invoke(state))
    except Exception as exc:
        _logger.error("Graph invocation failed: %s", exc)
        raise HTTPException(
            status_code=StatusCode.INTERNAL_ERROR,
            detail=f"Pipeline error: {exc}",
        ) from exc


def _build_response(session_id: str, state: dict[str, object]) -> ChatResponse:
    """Map the final graph state to a ChatResponse."""
    return ChatResponse(
        session_id=session_id,
        message=str(state.get("response", "")),
        agent_type=AgentType(state.get("agent_type", AgentType.CHAT)),
        status=StatusCode.OK,
    )
