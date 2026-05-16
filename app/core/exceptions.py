"""Custom application exception hierarchy."""


class BaseAppError(Exception):
    """Root exception for all application-level errors."""

    def __init__(self, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or message


class LLMError(BaseAppError):
    """Raised when the LLM provider fails."""


class ValidationError(BaseAppError):
    """Raised when request input fails validation."""


class SessionError(BaseAppError):
    """Raised on session issues."""


class GraphError(BaseAppError):
    """Raised on LangGraph pipeline errors."""
