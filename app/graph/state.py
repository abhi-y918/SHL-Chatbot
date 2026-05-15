"""LangGraph state definition."""

from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.enums.agent_types import AgentType


class GraphState(TypedDict, total=False):
    """Shared mutable state passed between all LangGraph nodes.

    Fields:
        session_id:  Caller's session identifier.
        user_input:  Raw user message text.
        intent:      Classified intent label (e.g. "chat", "summary").
        agent_type:  Resolved AgentType enum value.
        messages:    Full conversation history (append-only via add_messages).
        response:    Final assistant reply text.
        error:       Error message string if any node fails.
        metadata:    Arbitrary key-value pairs for observability.
    """

    session_id: str
    user_input: str
    intent: str
    agent_type: AgentType
    messages: Annotated[list[BaseMessage], add_messages]
    response: str
    error: str
    metadata: dict[str, Any]
