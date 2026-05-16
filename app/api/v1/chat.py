"""POST /chat — the primary endpoint for the SHL assessment agent."""

from fastapi import APIRouter

from app.graph.builder import build_graph
from app.graph.state import GraphState
from app.models.request import ChatRequest
from app.models.response import ChatResponse, Recommendation
from app.utils.logger import get_logger

router = APIRouter()
_logger = get_logger(__name__)
_graph = build_graph()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Process a stateless conversation through the LangGraph pipeline.

    Full conversation history is passed in every request.
    """
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    last_user = _extract_last_user(messages)

    initial_state: GraphState = {
        "session_id": "stateless",
        "user_input": last_user,
        "messages": messages,
        "metadata": {},
    }

    try:
        final = _graph.invoke(initial_state)
        return _build_response(final)
    except Exception as exc:
        _logger.exception("Graph invocation error: %s", exc)
        return ChatResponse(
            reply="I encountered an error. Please try again.",
            recommendations=[],
            end_of_conversation=False,
        )


def _extract_last_user(messages: list[dict[str, str]]) -> str:
    """Return the content of the most recent user message."""
    for m in reversed(messages):
        if m["role"] == "user":
            return m["content"]
    return ""


def _build_response(state: dict) -> ChatResponse:
    """Convert the final GraphState into an evaluator-compliant ChatResponse."""
    parsed = state.get("parsed_response", {})

    if state.get("error"):
        return ChatResponse(
            reply=parsed.get("reply", f"Error: {state['error']}"),
            recommendations=[],
            end_of_conversation=False,
        )

    recs = _extract_recs(parsed.get("recommendations", []))

    return ChatResponse(
        reply=parsed.get("reply", state.get("response", "")),
        recommendations=recs,
        end_of_conversation=bool(parsed.get("end_of_conversation", False)),
    )


def _extract_recs(raw_recs: list) -> list[Recommendation]:
    """Parse raw recommendation dicts into validated Recommendation models."""
    return [
        Recommendation(
            name=r["name"], url=r["url"], test_type=r.get("test_type", "K"),
        )
        for r in raw_recs
        if isinstance(r, dict) and r.get("name") and r.get("url")
    ][:10]
