# SHL Assessment Recommendation Agent

An agentic AI chatbot that helps hiring managers and recruiters discover the right SHL assessments through natural conversation. Instead of requiring users to know exact product names or filter categories, the agent takes a vague hiring intent and refines it into a grounded shortlist drawn entirely from the SHL product catalog.

**Live API**: [https://shl.abhinav-yadav.me](https://shl.abhinav-yadav.me)  
**Frontend**: [https://f-shl.abhinav-yadav.me](https://f-shl.abhinav-yadav.me)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [API Specification](#api-specification)
- [Conversational Behaviors](#conversational-behaviors)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running Locally](#running-locally)
- [Testing](#testing)
- [Design Decisions](#design-decisions)
- [Guardrails & Edge Cases](#guardrails--edge-cases)

---

## Overview

The agent supports four core conversational behaviors:

| Behavior | Description |
|---|---|
| **Clarify** | Asks focused questions when the user's request is too vague to act on |
| **Recommend** | Returns 1-10 assessments with exact catalog names, URLs, and type codes |
| **Refine** | Updates the shortlist when the user adds or removes constraints mid-conversation |
| **Compare** | Provides grounded side-by-side comparisons using only catalog data |

The agent stays strictly in scope -- it only discusses SHL assessments, refuses general hiring advice or legal questions, and never returns URLs that don't exist in the catalog.

---

## Architecture

```
User Request (POST /chat)
        |
        v
+------------------+
|  Input Validator  |  -- sanitize, truncate, validate
+------------------+
        |
        v
+--------------------+
| Intent Classifier  |  -- keyword-based: "chat" or "summary" (comparison)
+--------------------+
        |
        v
+------------------+
|   Agent Router   |  -- ChromaDB semantic search, build catalog context
+------------------+
        |
        v
+------------------+
|    LLM Caller    |  -- OpenRouter (Llama 3.3 70B) with system prompt + history
+------------------+
        |
        v
+---------------------+
| Response Formatter  |  -- JSON parsing, URL validation, structural guardrails
+---------------------+
        |
        v
+------------------+
|   Output Node    |  -- logging, final state
+------------------+
```

The pipeline is implemented as a **LangGraph StateGraph** with conditional edges for error short-circuiting. The API is fully **stateless** -- every `POST /chat` call carries the complete conversation history.

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| **API Framework** | FastAPI | Async-ready, auto-generated OpenAPI docs, Pydantic validation |
| **Pipeline Orchestration** | LangGraph | Declarative state machine with conditional routing and error handling |
| **LLM Provider** | OpenRouter (Llama 3.3 70B Instruct) | Free tier, strong instruction following, fast inference |
| **Vector Store** | ChromaDB (in-memory) | Zero-config, cosine similarity, built-in sentence-transformer embeddings |
| **Catalog Source** | SHL Product Catalog JSON API | Live fetch at startup, filtered to Individual Test Solutions only |
| **Frontend** | Streamlit | Rapid prototyping for conversational UI |
| **Deployment** | Render (API) + Streamlit Cloud (Frontend) | Free tier hosting with auto-deploy from GitHub |

---

## API Specification

### `GET /health`

Returns readiness status. Cold-start services have up to 2 minutes.

```json
{ "status": "ok" }
```

### `POST /chat`

Stateless conversation endpoint. Full history is passed every call.

**Request:**
```json
{
  "messages": [
    { "role": "user", "content": "Hiring a Java developer who works with stakeholders" },
    { "role": "assistant", "content": "Sure. What is seniority level?" },
    { "role": "user", "content": "Mid-level, around 4 years" }
  ]
}
```

**Response:**
```json
{
  "reply": "Got it. Here are 5 assessments that fit a mid-level Java dev.",
  "recommendations": [
    {
      "name": "Core Java (Advanced Level) (New)",
      "url": "https://www.shl.com/products/product-catalog/view/core-java-advanced-level-new/",
      "test_type": "K"
    }
  ],
  "end_of_conversation": false
}
```

**Field Rules:**

| Field | Type | Rule |
|---|---|---|
| `reply` | `string` | Always non-empty. Natural language response. |
| `recommendations` | `array` | Empty `[]` when gathering context or refusing. 1-10 items when committed. |
| `end_of_conversation` | `boolean` | `true` only when user explicitly confirms the shortlist is final. |

**Assessment Type Codes:**

| Code | Meaning |
|---|---|
| K | Knowledge & Skills |
| P | Personality & Behavior |
| A | Ability & Aptitude |
| S | Simulations |
| B | Biodata & Situational Judgment |
| C | Competencies |
| D | Development & 360 |
| E | Assessment Exercises |

---

## Conversational Behaviors

### 1. Clarify

When the user's request is vague (e.g., *"I need an assessment"*), the agent asks **one focused clarifying question** instead of guessing. It needs at least a role plus one of: seniority, specific skills, or purpose.

### 2. Recommend

Once it has enough context, the agent retrieves relevant assessments via semantic search over ChromaDB and selects 1-10 items. Every recommendation uses the **exact name and URL** from the SHL catalog.

### 3. Refine

When the user says *"add AWS"* or *"drop the Java test"*, the agent **updates** the existing shortlist. It preserves items the user didn't ask to remove and adds only items that exist in the catalog. It never starts over from scratch.

### 4. Compare

When asked *"What's the difference between OPQ and Verify G+?"*, the agent produces a grounded comparison using catalog data (type, duration, job levels, description). It preserves the existing shortlist in the response unless the user asks to change it.

### Scope Guard

The agent refuses off-topic requests (salary advice, legal questions, interview tips) and prompt injection attempts. It politely redirects to SHL assessment selection.

---

## Project Structure

```
agentic-chatbot/
|-- app/
|   |-- main.py                  # FastAPI app, lifespan, CORS, exception handlers
|   |-- config.py                # Pydantic settings (env vars)
|   |-- api/v1/
|   |   |-- chat.py              # POST /chat endpoint, graph invocation, timeout
|   |-- agents/
|   |   |-- chat_agent.py        # ChatAgent (OOP wrapper)
|   |   |-- summary_agent.py     # SummaryAgent (OOP wrapper)
|   |-- core/
|   |   |-- base_agent.py        # Abstract base class for agents
|   |   |-- decorators.py        # @retry, @log_execution, @validate_session
|   |   |-- exceptions.py        # Custom exception hierarchy
|   |-- enums/
|   |   |-- agent_types.py       # AgentType: CHAT, SUMMARY
|   |   |-- node_names.py        # LangGraph node name constants
|   |   |-- status.py            # HTTP status code enum
|   |-- graph/
|   |   |-- builder.py           # StateGraph assembly and compilation
|   |   |-- edges.py             # Conditional routing functions
|   |   |-- nodes.py             # Pipeline node functions + guardrails
|   |   |-- state.py             # GraphState TypedDict definition
|   |-- models/
|   |   |-- base.py              # BaseSchema (Pydantic v2 config)
|   |   |-- request.py           # ChatRequest, ChatMessage
|   |   |-- response.py          # ChatResponse, Recommendation, ErrorResponse
|   |-- prompts/
|   |   |-- base_prompt.py       # Abstract prompt builder
|   |   |-- chat_prompt.py       # Main agent system prompt with turn awareness
|   |   |-- summary_prompt.py    # Comparison agent system prompt
|   |-- services/
|   |   |-- catalog_service.py   # Catalog fetch, ChromaDB indexing, search, URL validation
|   |   |-- llm_service.py       # OpenRouter client (OpenAI SDK)
|   |-- utils/
|       |-- helpers.py           # JSON parsing, input sanitization
|       |-- logger.py            # Colored logging setup
|-- streamlit_app.py             # Streamlit chat frontend
|-- test_all_cases.py            # Comprehensive 32-check test suite
|-- test_chat.py                 # Quick manual test script
|-- pyproject.toml               # Dependencies and project metadata
|-- .env                         # Environment variables (API keys, model config)
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

### Install

```bash
# Clone the repository
git clone https://github.com/abhi-y918/SHL-Chatbot.git
cd SHL-Chatbot

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
openrouter_api_key=sk-or-v1-your-key-here

# Optional (defaults shown)
openrouter_base_url=https://openrouter.ai/api/v1
llm_model=meta-llama/llama-3.3-70b-instruct
llm_temperature=0.4
llm_max_tokens=2048
retrieval_top_k=20
catalog_url=https://tcp-us-prod-rnd.shl.com/voiceRater/shl-ai-hiring/shl_product_catalog.json
```

---

## Running Locally

### API Server

```bash
uv run uvicorn app.main:app --reload --port 8000
```

The server will:
1. Fetch the SHL catalog JSON from the remote API
2. Index all assessments into an in-memory ChromaDB collection
3. Start serving on `http://localhost:8000`

### Streamlit Frontend

```bash
uv run streamlit run streamlit_app.py
```

Opens a chat interface at `http://localhost:8501` that connects to the local API.

### Verify

```bash
# Health check
curl http://localhost:8000/health

# Quick chat test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "I need an assessment for a mid-level Java developer"}]}'
```

---

## Testing

### Full Test Suite (32 checks)

```bash
# Start the server first, then:
uv run python test_all_cases.py
```

Covers:
- Health endpoint
- Schema compliance (all response fields present and correctly typed)
- Vague query guardrail (3 variants)
- Specific first-turn recommendations
- Multi-turn conversation with recommendations
- Off-topic refusal
- Prompt injection resistance
- `end_of_conversation` guardrail
- Comparison requests
- Edge cases (empty messages, no user messages, very long input)

### Quick Manual Tests

```bash
uv run python test_chat.py
```

---

## Design Decisions

### Why LangGraph over plain function calls?

LangGraph provides a declarative state machine with conditional edges, making it easy to short-circuit on validation errors and route between chat/comparison flows. Each node is a pure function that transforms state, making the pipeline testable and debuggable.

### Why ChromaDB in-memory?

The SHL catalog is small enough (~400 entries) to fit in memory. No external database needed, zero cold-start latency after initial fetch, and cosine similarity search with sentence-transformer embeddings provides strong semantic matching.

### Why structural guardrails on top of prompt instructions?

LLMs don't always follow instructions perfectly. The `response_formatter` node adds hard guardrails:
- **First-turn vagueness**: Blocks recommendations when `< 15 words` and `< 3 specificity signals`
- **end_of_conversation**: Forces `false` when recommendations are empty
- **URL validation**: Drops any recommendation whose URL isn't in the catalog, with fuzzy name-matching fallback
- **Recommendation cap**: Hard limit of 10 items

### Why combine all user messages for search?

When a user says *"Add AWS and Docker"* on turn 4, searching only that message would miss the base context (Java, Spring, SQL). Combining all user messages into a single search query ensures the retrieval covers both the original need and the refinement.

### Why 25s timeout instead of 30s?

The evaluator caps at 30s. Using 25s for the graph execution leaves 5s headroom for network latency, JSON serialization, and FastAPI overhead.

---

## Guardrails & Edge Cases

| Edge Case | How It's Handled |
|---|---|
| Empty input | `ValidationError` raised in `input_validator` |
| Input > 4000 chars | Truncated to 4000 chars |
| `recommendations: null` from LLM | Coerced to `[]` in `safe_json_parse` and `response_formatter` |
| `end_of_conversation` non-boolean | Coerced to `false` |
| LLM returns markdown fences | Stripped by `extract_json` |
| LLM returns trailing commas | Fixed by `safe_json_parse` regex |
| LLM returns non-JSON text | Treated as plain reply with empty recs |
| LLM hallucinates URL but correct name | Fixed via `find_by_name` fallback |
| URL trailing slash mismatch | Both variants checked via normalized URL set |
| Duplicate catalog entries | Deduplicated by `entity_id` |
| LLM timeout | 25s cap with graceful fallback message |
| Unhandled exception | Schema-compliant JSON 500 response |
| Off-topic / legal questions | Prompt refuses, no recommendations |
| Prompt injection | Prompt refuses, no recommendations |
| `end_of_conversation: true` with no recs | Forced to `false` by structural guardrail |
| First-turn vague query with recs | Blocked by word-count + signal-count guardrail |

---

## License

This project was built as part of the SHL GenAI Assessment.