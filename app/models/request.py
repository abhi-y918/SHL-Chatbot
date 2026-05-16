"""Request schemas — matches the evaluator's non-negotiable spec."""

from pydantic import Field

from app.models.base import BaseSchema


class ChatMessage(BaseSchema):
    """A single message in the conversation history."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseSchema):
    """POST /chat request body — full stateless conversation history."""

    messages: list[ChatMessage] = Field(
        ..., description="Complete conversation history", min_length=1
    )
