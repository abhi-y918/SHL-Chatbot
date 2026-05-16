"""Response schemas — matches the evaluator's non-negotiable spec."""

from pydantic import Field

from app.enums.status import StatusCode
from app.models.base import BaseSchema


class Recommendation(BaseSchema):
    """A single assessment recommendation."""

    name: str = Field(..., description="Assessment name from SHL catalog")
    url: str = Field(..., description="Catalog URL for the assessment")
    test_type: str = Field(..., description="Type code: K, P, A, S, B, C, D")


class ChatResponse(BaseSchema):
    """POST /chat response — evaluator schema."""

    reply: str = Field(..., description="Agent reply text")
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="1-10 items when committed, else empty"
    )
    end_of_conversation: bool = Field(
        default=False, description="True only when task is complete"
    )


class ErrorResponse(BaseSchema):
    """Structured error payload."""

    error_type: str = Field(..., description="Exception class name")
    detail: str = Field(..., description="Human-readable error description")
    status: StatusCode = Field(..., description="HTTP status code")
