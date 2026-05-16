"""LangGraph state definition."""

from typing import Any

from typing_extensions import TypedDict

from app.enums.agent_types import AgentType


class GraphState(TypedDict, total=False):
    """Shared state passed between all LangGraph nodes."""

    session_id: str
    user_input: str
    intent: str
    agent_type: AgentType
    messages: list[dict[str, str]]
    retrieved_assessments: list[dict[str, Any]]
    catalog_context: str
    response: str
    parsed_response: dict[str, Any]
    error: str
    metadata: dict[str, Any]
