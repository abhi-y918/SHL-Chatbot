"""Pydantic models for the /chat API — schema is non-negotiable."""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    """POST /chat request body — full stateless conversation history."""

    messages: list[ChatMessage] = Field(
        ..., description="Complete conversation history", min_length=1
    )


class Recommendation(BaseModel):
    """A single assessment recommendation returned to the caller."""

    name: str = Field(..., description="Assessment name from the SHL catalog")
    url: str = Field(..., description="Catalog URL for the assessment")
    test_type: str = Field(..., description="Assessment type code (K, P, A, S, B, C, D)")


class ChatResponse(BaseModel):
    """POST /chat response — must match the evaluator's expected schema exactly."""

    reply: str = Field(..., description="Agent reply text")
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="Empty while gathering context; 1-10 items when committed",
    )
    end_of_conversation: bool = Field(
        default=False,
        description="True only when the agent considers the task complete",
    )
