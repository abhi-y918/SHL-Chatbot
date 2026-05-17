
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
        # Sanitize: collapse whitespace, strip
        cleaned = sanitize_input(raw)
        # Truncate excessively long input to prevent token overflow
        if len(cleaned) > 4000:
            cleaned = cleaned[:4000]
        state["user_input"] = cleaned
    except ValidationError as exc:
        state["error"] = exc.detail
    return state


def intent_classifier(state: GraphState) -> GraphState:
    """Classify intent: 'summary' for comparisons, 'chat' for everything else."""
    if state.get("error"):
        return state
    text = state.get("user_input", "").lower()
    compare_kw = (
        "compare", "comparison", "difference", "differ", "differs",
        "vs", "versus", "distinguish",
        "what separates", "contrast",
    )
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
    """Combine ALL user messages into a search query for better retrieval.

    Using all user messages ensures that refinement requests ("add AWS",
    "drop REST") still retrieve the correct base assessments alongside
    the newly requested ones.
    """
    msgs = state.get("messages", [])
    user_msgs = [m["content"] for m in msgs if m["role"] == "user"]
    if user_msgs:
        # Use all user messages, but limit total length
        combined = " ".join(user_msgs)
        return combined[:2000]  # Prevent excessively long queries
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
        messages = state.get("messages", [])

        # Calculate turn awareness metrics
        total_messages = len(messages)
        user_turn_count = sum(1 for m in messages if m["role"] == "user")

        ctx = {
            "catalog_context": state.get("catalog_context", ""),
            "turn_count": str(user_turn_count),
            "total_messages": str(total_messages),
        }
        agent_type = state.get("agent_type", AgentType.CHAT)

        # Use chat prompt for everything (unified), summary prompt only for
        # explicit comparison requests
        if agent_type == AgentType.SUMMARY:
            prompt = _summary_prompt
        else:
            prompt = _chat_prompt

        system_prompt = prompt.build(ctx)
        state["response"] = _llm.invoke(system_prompt, messages)
    except LLMError as exc:
        state["error"] = exc.detail
    return state


def response_formatter(state: GraphState) -> GraphState:
    """Parse the raw LLM JSON response and validate recommendation URLs."""
    if state.get("error"):
        return state

    parsed = safe_json_parse(state.get("response", ""))

    # Ensure recommendations is always a list, never null/None
    if parsed.get("recommendations") is None:
        parsed["recommendations"] = []

    # Ensure end_of_conversation is always a boolean
    if not isinstance(parsed.get("end_of_conversation"), bool):
        parsed["end_of_conversation"] = False

    # Validate and filter recommendations
    if _catalog and parsed.get("recommendations"):
        parsed["recommendations"] = _validate_recs(parsed["recommendations"])

    # ── Structural guardrail: first-turn vagueness ──────────────────────
    # If this is the first user message and the query is short/vague,
    # force empty recommendations to prevent premature recommending.
    messages = state.get("messages", [])
    user_msgs = [m for m in messages if m["role"] == "user"]
    if len(user_msgs) == 1:
        first_msg = user_msgs[0]["content"].strip()
        # Short first messages (< 15 words) need strong specificity signals
        if len(first_msg.split()) < 15 and not _has_strong_signals(first_msg):
            parsed["recommendations"] = []
            parsed["end_of_conversation"] = False

    # ── Structural guardrail: end_of_conversation ───────────────────────
    # Never end the conversation without providing recommendations.
    if parsed.get("end_of_conversation") and not parsed.get("recommendations"):
        parsed["end_of_conversation"] = False

    state["parsed_response"] = parsed
    return state


def _has_strong_signals(text: str) -> bool:
    """Check if text has enough specificity to recommend on turn 1.

    We look for presence of job-description-like markers such as
    specific technologies, role titles with seniority, or domain terms.
    Returns True only if 3+ distinct signals are found, indicating the
    user has provided role + seniority/skills/purpose.
    """
    text_lower = text.lower()
    # Specific role signals
    role_signals = [
        "job description", "jd", "entry-level", "entry level", "senior",
        "junior", "mid-level", "mid level", "graduate", "manager", "director",
        "executive", "intern", "lead", "full-stack", "full stack",
        "frontend", "backend", "devops", "data scientist", "analyst",
        "engineer", "developer", "administrator", "operator",
        "trainee", "officer", "specialist", "coordinator", "supervisor",
        "plant operator", "contact centre", "contact center",
        "financial analyst", "admin assistant",
    ]
    # Technology signals
    tech_signals = [
        "java", "python", "c#", ".net", "javascript", "react", "angular",
        "sql", "aws", "docker", "kubernetes", "excel", "word", "salesforce",
        "sap", "hipaa", "spring", "rest api", "microservice",
        "linux", "networking",
    ]
    # Assessment type / domain signals
    assessment_signals = [
        "cognitive", "personality", "aptitude", "numerical", "verbal",
        "reasoning", "situational", "simulation", "assessment battery",
        "knowledge test", "personality test", "aptitude test", "cognitive test",
        "situational judgement", "situational judgment",
        "safety", "dependability", "compliance", "leadership",
        "sales", "customer service", "medical", "accounting",
        "re-skill", "reskill", "development", "selection",
    ]

    all_signals = role_signals + tech_signals + assessment_signals
    matches = sum(1 for s in all_signals if s in text_lower)
    return matches >= 3  # Need at least 3 signals to be considered specific


def _validate_recs(recs: list) -> list:
    """Keep only recommendations whose URLs exist in the indexed catalog."""
    valid = []
    for r in recs:
        if not isinstance(r, dict):
            continue
        if not r.get("name") or not r.get("url"):
            continue
        # Ensure test_type exists
        if not r.get("test_type"):
            r["test_type"] = "K"
        # Validate URL against catalog
        if _catalog and _catalog.validate_url(r["url"]):
            valid.append(r)
        elif _catalog:
            # Try to find the assessment by name and fix the URL
            fixed = _catalog.find_by_name(r["name"])
            if fixed:
                r["url"] = fixed["url"]
                r["test_type"] = fixed.get("test_type", r["test_type"])
                valid.append(r)
            else:
                _logger.warning("Dropping recommendation with invalid URL: %s", r.get("url"))
    return valid[:10]


def output_node(state: GraphState) -> GraphState:
    """Terminal node — log outcome."""
    if state.get("error"):
        _logger.warning("Pipeline error: %s", state["error"])
    else:
        _logger.info("Pipeline complete")
    return state
