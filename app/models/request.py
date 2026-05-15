"""Request schemas for API endpoints."""

from pydantic import Field

from app.models.base import BaseSchema


class ChatRequest(BaseSchema):
    """Payload for POST /chat."""

    session_id: str = Field(..., description="Unique session identifier", min_length=1)
    message: str = Field(..., description="User message text", min_length=1, max_length=4096)


class SessionRequest(BaseSchema):
    """Payload for POST /session."""

    user_id: str = Field(..., description="Caller's user identifier", min_length=1)
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Optional arbitrary session metadata",
    )
