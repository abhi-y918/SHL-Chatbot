"""Conditional edge routing logic for the LangGraph pipeline."""

from app.enums.agent_types import AgentType
from app.enums.node_names import NodeName
from app.graph.state import GraphState


def route_by_intent(state: GraphState) -> str:
    """Return the next node name based on the classified intent.

    Used as the routing function for add_conditional_edges() from intent_classifier.

    Args:
        state: Current graph state after intent classification.

    Returns:
        NodeName string value — either AGENT_ROUTER or OUTPUT_NODE (on error).
    """
    if state.get("error"):
        return NodeName.OUTPUT_NODE.value
    intent = state.get("intent", AgentType.CHAT.value)
    if intent == AgentType.SUMMARY.value:
        return NodeName.AGENT_ROUTER.value
    return NodeName.AGENT_ROUTER.value


def route_after_validation(state: GraphState) -> str:
    """Short-circuit to output_node if validation failed.

    Args:
        state: Current graph state after input_validator.

    Returns:
        NodeName string value.
    """
    if state.get("error"):
        return NodeName.OUTPUT_NODE.value
    return NodeName.INTENT_CLASSIFIER.value
