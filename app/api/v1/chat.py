"""POST /chat — the primary endpoint for the SHL assessment agent."""

import concurrent.futures

from fastapi import APIRouter

from app.graph.builder import build_graph
from app.graph.state import GraphState
from app.models.request import ChatRequest
from app.models.response import ChatResponse, Recommendation
from app.utils.logger import get_logger

router = APIRouter()
_logger = get_logger(__name__)
_graph = build_graph()

# Thread pool for timeout enforcement
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Process a stateless conversation through the LangGraph pipeline.

    Full conversation history is passed in every request.
    The evaluator caps each call at 30 seconds.
    """
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Validate: must have at least one user message
    user_msgs = [m for m in messages if m["role"] == "user"]
    if not user_msgs:
        return ChatResponse(
            reply="Please send a message to get started.",
            recommendations=[],
            end_of_conversation=False,
        )

    last_user = _extract_last_user(messages)

    initial_state: GraphState = {
        "session_id": "stateless",
        "user_input": last_user,
        "messages": messages,
        "metadata": {},
    }

    try:
        # Execute with timeout to stay within 30s evaluator limit
        future = _executor.submit(_graph.invoke, initial_state)
        final = future.result(timeout=25.0)  # 25s to leave headroom
        return _build_response(final)
    except concurrent.futures.TimeoutError:
        _logger.error("Graph invocation timed out after 25s")
        return ChatResponse(
            reply="I'm taking too long to respond. Based on what I know so far, "
                  "could you please repeat or simplify your request?",
            recommendations=[],
            end_of_conversation=False,
        )
    except Exception as exc:
        _logger.exception("Graph invocation error: %s", exc)
        return ChatResponse(
            reply="I encountered an error processing your request. Please try again.",
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
            reply=parsed.get("reply", f"I encountered an issue: {state['error']}. "
                             "Could you rephrase your request?"),
            recommendations=[],
            end_of_conversation=False,
        )

    recs = _extract_recs(parsed.get("recommendations", []))
    reply = parsed.get("reply", state.get("response", ""))

    # Ensure reply is never empty
    if not reply or not reply.strip():
        reply = "I'm not sure how to respond to that. Could you provide more details about the role you're hiring for?"

    return ChatResponse(
        reply=reply,
        recommendations=recs,
        end_of_conversation=bool(parsed.get("end_of_conversation", False)),
    )


def _extract_recs(raw_recs: list) -> list[Recommendation]:
    """Parse raw recommendation dicts into validated Recommendation models."""
    if not isinstance(raw_recs, list):
        return []
    return [
        Recommendation(
            name=r["name"], url=r["url"], test_type=r.get("test_type", "K"),
        )
        for r in raw_recs
        if isinstance(r, dict) and r.get("name") and r.get("url")
    ][:10]
