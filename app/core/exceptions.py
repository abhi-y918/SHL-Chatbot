"""Custom application exception hierarchy."""


class BaseAppError(Exception):
    """Root exception for all application-level errors."""

    def __init__(self, message: str, detail: str = "") -> None:
        """Initialize with a human-readable message and optional detail."""
        super().__init__(message)
        self.message = message
        self.detail = detail or message


class LLMError(BaseAppError):
    """Raised when the LLM provider returns an error or times out."""


class ValidationError(BaseAppError):
    """Raised when request input fails validation checks."""


class SessionError(BaseAppError):
    """Raised when session lookup, creation, or deletion fails."""


class GraphError(BaseAppError):
    """Raised when the LangGraph pipeline encounters an unrecoverable state."""
