"""StateGraph assembly and compilation."""

from langgraph.graph import END, StateGraph

from app.enums.node_names import NodeName
from app.graph.edges import route_after_validation, route_by_intent
from app.graph.nodes import (
    agent_router,
    input_validator,
    intent_classifier,
    llm_caller,
    output_node,
    response_formatter,
)
from app.graph.state import GraphState


def build_graph() -> StateGraph:
    """Assemble and compile the full LangGraph pipeline.

    Returns:
        Compiled StateGraph ready for invocation.
    """
    graph = StateGraph(GraphState)

    _register_nodes(graph)
    _register_edges(graph)

    graph.set_entry_point(NodeName.INPUT_VALIDATOR.value)
    return graph.compile()


def _register_nodes(graph: StateGraph) -> None:
    """Add all processing nodes to the graph."""
    graph.add_node(NodeName.INPUT_VALIDATOR.value, input_validator)
    graph.add_node(NodeName.INTENT_CLASSIFIER.value, intent_classifier)
    graph.add_node(NodeName.AGENT_ROUTER.value, agent_router)
    graph.add_node(NodeName.LLM_CALLER.value, llm_caller)
    graph.add_node(NodeName.RESPONSE_FORMATTER.value, response_formatter)
    graph.add_node(NodeName.OUTPUT_NODE.value, output_node)


def _register_edges(graph: StateGraph) -> None:
    """Wire conditional and static edges between nodes."""
    graph.add_conditional_edges(
        NodeName.INPUT_VALIDATOR.value,
        route_after_validation,
        {
            NodeName.INTENT_CLASSIFIER.value: NodeName.INTENT_CLASSIFIER.value,
            NodeName.OUTPUT_NODE.value: NodeName.OUTPUT_NODE.value,
        },
    )
    graph.add_conditional_edges(
        NodeName.INTENT_CLASSIFIER.value,
        route_by_intent,
        {NodeName.AGENT_ROUTER.value: NodeName.AGENT_ROUTER.value},
    )
    graph.add_edge(NodeName.AGENT_ROUTER.value, NodeName.LLM_CALLER.value)
    graph.add_edge(NodeName.LLM_CALLER.value, NodeName.RESPONSE_FORMATTER.value)
    graph.add_edge(NodeName.RESPONSE_FORMATTER.value, NodeName.OUTPUT_NODE.value)
    graph.add_edge(NodeName.OUTPUT_NODE.value, END)
