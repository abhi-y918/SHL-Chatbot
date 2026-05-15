"""All LangGraph node functions for the agentic pipeline."""

from langchain_core.messages import HumanMessage

from app.core.exceptions import GraphError, LLMError, ValidationError
from app.enums.agent_types import AgentType
from app.graph.state import GraphState
from app.services.llm_service import LLMService
from app.utils.helpers import sanitize_input
from app.utils.logger import get_logger

_logger = get_logger(__name__)
_llm_service = LLMService()


def input_validator(state: GraphState) -> GraphState:
    """Validate and sanitise the raw user input.

    Sets state["error"] on failure; mutates state["user_input"] on success.
    """
    try:
        raw = state.get("user_input", "")
        if not raw or not raw.strip():
            raise ValidationError("Empty input", "user_input must not be blank")
        state["user_input"] = sanitize_input(raw)
        _logger.debug("input_validator: input accepted")
    except ValidationError as exc:
        state["error"] = exc.detail
    return state


def intent_classifier(state: GraphState) -> GraphState:
    """Classify the user's intent as 'chat' or 'summary'.

    Uses a simple heuristic; can be replaced with an LLM call.
    """
    try:
        text = state.get("user_input", "").lower()
        if any(kw in text for kw in ("summarize", "summary", "tldr", "recap")):
            state["intent"] = AgentType.SUMMARY.value
        else:
            state["intent"] = AgentType.CHAT.value
        _logger.debug("intent_classifier: intent=%s", state["intent"])
    except Exception as exc:
        state["error"] = str(exc)
    return state


def agent_router(state: GraphState) -> GraphState:
    """Map the classified intent to a concrete AgentType enum value."""
    try:
        intent = state.get("intent", AgentType.CHAT.value)
        state["agent_type"] = AgentType(intent)
        _logger.debug("agent_router: agent_type=%s", state["agent_type"])
    except ValueError as exc:
        state["error"] = f"Unknown intent: {exc}"
    return state


def llm_caller(state: GraphState) -> GraphState:
    """Invoke the LLM via the active agent and store the raw response."""
    try:
        from app.agents.chat_agent import ChatAgent
        from app.agents.summary_agent import SummaryAgent

        agent_type = state.get("agent_type", AgentType.CHAT)
        session_id = state.get("session_id", "")
        message = state.get("user_input", "")
        history = list(state.get("messages", []))

        agent = ChatAgent() if agent_type == AgentType.CHAT else SummaryAgent()
        reply = agent.process(session_id=session_id, message=message, history=history)
        state["response"] = reply
        state["messages"] = [*history, HumanMessage(content=message)]
        _logger.debug("llm_caller: got reply (%d chars)", len(reply))
    except LLMError as exc:
        state["error"] = exc.detail
    except Exception as exc:
        state["error"] = str(exc)
    return state


def response_formatter(state: GraphState) -> GraphState:
    """Post-process the raw LLM reply (trim whitespace, length guard)."""
    try:
        raw = state.get("response", "")
        state["response"] = raw.strip()
    except Exception as exc:
        state["error"] = str(exc)
    return state


def output_node(state: GraphState) -> GraphState:
    """Terminal node — logs final state and surfaces any lingering errors."""
    if state.get("error"):
        raise GraphError("Pipeline error", state["error"])
    _logger.info("output_node: pipeline complete for session=%s", state.get("session_id"))
    return state
