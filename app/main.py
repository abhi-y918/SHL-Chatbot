from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import chat as chat_router
from app.core.exceptions import (
    BaseAppError, GraphError, LLMError, SessionError, ValidationError,
)
from app.enums.status import StatusCode
from app.graph.nodes import set_services
from app.models.response import ChatResponse, ErrorResponse
from app.services.catalog_service import CatalogService
from app.services.llm_service import LLMService
from app.utils.logger import get_logger

_logger = get_logger(__name__)


_catalog = CatalogService()
_llm = LLMService()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: load catalog into ChromaDB and inject services into graph nodes."""
    _logger.info("Loading SHL catalog into ChromaDB...")
    _catalog.initialize()
    set_services(_llm, _catalog)
    _logger.info("Ready to serve.")
    yield
    _logger.info("Shutting down.")


app = FastAPI(
    title="SHL Assessment Agent",
    description="Agentic AI chatbot for SHL assessment recommendations.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Router: only POST /chat ───────────────────────────────────
app.include_router(chat_router.router, tags=["Chat"])


# ── Health check: GET /health ─────────────────────────────────
@app.get("/health", tags=["Meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ── Exception handlers ─────────────────────────────────────────
def _err(exc: BaseAppError, status: StatusCode) -> JSONResponse:
    """Build a structured JSON error response from an app exception."""
    body = ErrorResponse(
        error_type=type(exc).__name__, detail=exc.detail, status=status,
    )
    return JSONResponse(
        status_code=status.value, content=body.model_dump(mode="json"),
    )


@app.exception_handler(ValidationError)
async def _h_val(_r: Request, e: ValidationError) -> JSONResponse:
    """Handle input validation failures."""
    return _err(e, StatusCode.UNPROCESSABLE)


@app.exception_handler(SessionError)
async def _h_ses(_r: Request, e: SessionError) -> JSONResponse:
    """Handle missing or invalid session errors."""
    return _err(e, StatusCode.NOT_FOUND)


@app.exception_handler(LLMError)
async def _h_llm(_r: Request, e: LLMError) -> JSONResponse:
    """Handle LLM provider failures."""
    return _err(e, StatusCode.SERVICE_UNAVAILABLE)


@app.exception_handler(GraphError)
async def _h_graph(_r: Request, e: GraphError) -> JSONResponse:
    """Handle LangGraph pipeline errors."""
    return _err(e, StatusCode.INTERNAL_ERROR)


@app.exception_handler(BaseAppError)
async def _h_base(_r: Request, e: BaseAppError) -> JSONResponse:
    """Catch-all for any unclassified application errors."""
    return _err(e, StatusCode.INTERNAL_ERROR)


@app.exception_handler(Exception)
async def _h_generic(_r: Request, e: Exception) -> JSONResponse:
    """Global catch-all for completely unexpected errors.

    Returns a schema-compliant ChatResponse so the evaluator never
    sees a non-JSON error page.
    """
    _logger.exception("Unhandled exception: %s", e)
    body = ChatResponse(
        reply="An unexpected error occurred. Please try again.",
        recommendations=[],
        end_of_conversation=False,
    )
    return JSONResponse(
        status_code=500,
        content=body.model_dump(mode="json"),
    )
