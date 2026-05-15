"""FastAPI application entry point: router mount and exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1 import chat as chat_router
from app.api.v1 import session as session_router
from app.config import get_settings
from app.core.exceptions import (
    BaseAppError,
    GraphError,
    LLMError,
    SessionError,
    ValidationError,
)
from app.enums.status import StatusCode
from app.models.response import ErrorResponse
from app.utils.logger import get_logger

_logger = get_logger(__name__)
_settings = get_settings()

app = FastAPI(
    title="Agentic Chatbot API",
    description="Production-grade agentic AI chatbot backend with LangGraph and OpenRouter.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(chat_router.router, prefix="/v1", tags=["Chat"])
app.include_router(session_router.router, prefix="/v1", tags=["Session"])


# ── Exception handlers ─────────────────────────────────────────────────────────

def _error_response(exc: BaseAppError, status: StatusCode) -> JSONResponse:
    """Build a structured JSON error response from an application exception."""
    payload = ErrorResponse(
        error_type=type(exc).__name__,
        detail=exc.detail,
        status=status,
    )
    return JSONResponse(status_code=status.value, content=payload.model_dump(mode="json"))


@app.exception_handler(ValidationError)
async def validation_error_handler(_req: Request, exc: ValidationError) -> JSONResponse:
    """Handle input validation failures."""
    _logger.warning("ValidationError: %s", exc.detail)
    return _error_response(exc, StatusCode.UNPROCESSABLE)


@app.exception_handler(SessionError)
async def session_error_handler(_req: Request, exc: SessionError) -> JSONResponse:
    """Handle missing or invalid session errors."""
    _logger.warning("SessionError: %s", exc.detail)
    return _error_response(exc, StatusCode.NOT_FOUND)


@app.exception_handler(LLMError)
async def llm_error_handler(_req: Request, exc: LLMError) -> JSONResponse:
    """Handle LLM provider failures."""
    _logger.error("LLMError: %s", exc.detail)
    return _error_response(exc, StatusCode.SERVICE_UNAVAILABLE)


@app.exception_handler(GraphError)
async def graph_error_handler(_req: Request, exc: GraphError) -> JSONResponse:
    """Handle LangGraph pipeline errors."""
    _logger.error("GraphError: %s", exc.detail)
    return _error_response(exc, StatusCode.INTERNAL_ERROR)


@app.exception_handler(BaseAppError)
async def base_app_error_handler(_req: Request, exc: BaseAppError) -> JSONResponse:
    """Catch-all for any unclassified application errors."""
    _logger.error("BaseAppError: %s", exc.detail)
    return _error_response(exc, StatusCode.INTERNAL_ERROR)


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/health", tags=["Meta"])
async def health_check() -> dict[str, str]:
    """Return service liveness status."""
    return {"status": "ok", "env": _settings.app_env}
