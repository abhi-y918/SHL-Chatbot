"""LangGraph node name enumeration."""

from enum import Enum


class NodeName(str, Enum):
    """Node names used in add_edge() and add_conditional_edges()."""

    INPUT_VALIDATOR = "input_validator"
    INTENT_CLASSIFIER = "intent_classifier"
    AGENT_ROUTER = "agent_router"
    LLM_CALLER = "llm_caller"
    RESPONSE_FORMATTER = "response_formatter"
    OUTPUT_NODE = "output_node"
