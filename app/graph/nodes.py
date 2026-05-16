"""All LangGraph node functions for the SHL assessment pipeline."""

from app.core.exceptions import LLMError, ValidationError
from app.enums.agent_types import AgentType
from app.graph.state import GraphState
from app.services.catalog_service import CatalogService
from app.services.llm_service import LLMService
from app.prompts.chat_prompt import ChatPrompt
from app.prompts.summary_prompt import SummaryPrompt
from app.utils.helpers import safe_json_parse, sanitize_input
from app.utils.logger import get_logger

_logger = get_logger(__name__)

_llm: LLMService | None = None
_catalog: CatalogService | None = None
_chat_prompt = ChatPrompt()
_summary_prompt = SummaryPrompt()


def set_services(llm: LLMService, catalog: CatalogService) -> None:
    """Inject service singletons (called once at app startup)."""
    global _llm, _catalog
    _llm, _catalog = llm, catalog


def input_validator(state: GraphState) -> GraphState:
    """Validate and sanitise the raw user input."""
    try:
        raw = state.get("user_input", "")
        if not raw or not raw.strip():
            raise ValidationError("Empty input")
        state["user_input"] = sanitize_input(raw)
    except ValidationError as exc:
        state["error"] = exc.detail
    return state


def intent_classifier(state: GraphState) -> GraphState:
    """Classify intent: 'summary' for comparisons, 'chat' for everything else."""
    if state.get("error"):
        return state
    text = state.get("user_input", "").lower()
    compare_kw = ("compare", "difference", "differ", "vs", "versus")
    if any(kw in text for kw in compare_kw):
        state["intent"] = AgentType.SUMMARY.value
    else:
        state["intent"] = AgentType.CHAT.value
    return state


def agent_router(state: GraphState) -> GraphState:
    """Set agent_type and retrieve relevant assessments from ChromaDB."""
    if state.get("error"):
        return state
    intent = state.get("intent", AgentType.CHAT.value)
    state["agent_type"] = AgentType(intent)
    query = _build_search_query(state)
    if _catalog:
        results = _catalog.search(query)
        state["retrieved_assessments"] = results
        state["catalog_context"] = _format_context(results)
    return state


def _build_search_query(state: GraphState) -> str:
    """Combine recent user messages into a search query."""
    msgs = state.get("messages", [])
    user_msgs = [m["content"] for m in msgs if m["role"] == "user"]
    if user_msgs:
        return " ".join(user_msgs[-3:])
    return state.get("user_input", "")


def _format_context(assessments: list[dict]) -> str:
    """Format retrieved assessments into a text block for the system prompt."""
    if not assessments:
        return "(No assessments retrieved — ask for more details.)"
    lines = []
    for i, a in enumerate(assessments, 1):
        desc = a.get("description", "")[:300]
        lines.append(
            f"[{i}] {a.get('name', '?')}\n"
            f"    URL: {a.get('url', '')}\n"
            f"    Type: {a.get('test_type', '')}\n"
            f"    Category: {a.get('keys', '')}\n"
            f"    Job Levels: {a.get('job_levels', '')}\n"
            f"    Duration: {a.get('duration', 'N/A')}\n"
            f"    Remote: {a.get('remote', '')}\n"
            f"    Adaptive: {a.get('adaptive', '')}\n"
            f"    Desc: {desc}"
        )
    return "\n\n".join(lines)


def llm_caller(state: GraphState) -> GraphState:
    """Invoke the LLM with the appropriate prompt and conversation history."""
    if state.get("error") or not _llm:
        return state
    try:
        ctx = {"catalog_context": state.get("catalog_context", "")}
        agent_type = state.get("agent_type", AgentType.CHAT)
        prompt = _chat_prompt if agent_type == AgentType.CHAT else _summary_prompt
        system_prompt = prompt.build(ctx)
        state["response"] = _llm.invoke(system_prompt, state.get("messages", []))
    except LLMError as exc:
        state["error"] = exc.detail
    return state


def response_formatter(state: GraphState) -> GraphState:
    """Parse the raw LLM JSON response and validate recommendation URLs."""
    if state.get("error"):
        return state
    parsed = safe_json_parse(state.get("response", ""))
    if _catalog and parsed.get("recommendations"):
        parsed["recommendations"] = _validate_recs(parsed["recommendations"])
    state["parsed_response"] = parsed
    return state


def _validate_recs(recs: list) -> list:
    """Keep only recommendations whose URLs exist in the indexed catalog."""
    valid = [
        r for r in recs
        if isinstance(r, dict)
        and r.get("url")
        and _catalog
        and _catalog.validate_url(r["url"])
    ]
    return valid[:10]


def output_node(state: GraphState) -> GraphState:
    """Terminal node — log outcome."""
    if state.get("error"):
        _logger.warning("Pipeline error: %s", state["error"])
    else:
        _logger.info("Pipeline complete")
    return state
