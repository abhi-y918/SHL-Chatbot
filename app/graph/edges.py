
from app.enums.node_names import NodeName
from app.graph.state import GraphState


def route_after_validation(state: GraphState) -> str:
    """Short-circuit to output_node if validation failed."""
    if state.get("error"):
        return NodeName.OUTPUT_NODE.value
    return NodeName.INTENT_CLASSIFIER.value


def route_by_intent(state: GraphState) -> str:
    """Route from intent_classifier to agent_router (or output on error)."""
    if state.get("error"):
        return NodeName.OUTPUT_NODE.value
    return NodeName.AGENT_ROUTER.value
