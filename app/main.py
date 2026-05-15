"""FastAPI application — only two endpoints: GET /health and POST /chat."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.agent import SHLAgent
from app.models import ChatRequest, ChatResponse
from app.retriever import AssessmentRetriever

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Global singletons initialized at startup
retriever = AssessmentRetriever()
agent = SHLAgent(retriever)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: fetch catalog and build ChromaDB index."""
    logger.info("Starting up — loading SHL catalog into ChromaDB...")
    retriever.initialize()
    logger.info("Catalog indexed. Ready to serve.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="SHL Assessment Agent",
    description="RAG-powered conversational agent for SHL assessment recommendations.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Readiness check — returns 200 with {\"status\": \"ok\"}."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a stateless conversation and return the agent's next reply.

    The full conversation history is passed in every request.
    """
    try:
        return agent.handle(request.messages)
    except Exception as exc:
        logger.exception("Chat handler error: %s", exc)
        return ChatResponse(
            reply="I encountered an error processing your request. Please try again.",
            recommendations=[],
            end_of_conversation=False,
        )
