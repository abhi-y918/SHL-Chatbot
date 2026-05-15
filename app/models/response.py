"""Response schemas for API endpoints."""

from pydantic import Field

from app.enums.agent_types import AgentType
from app.enums.status import StatusCode
from app.models.base import BaseSchema


class ChatResponse(BaseSchema):
    """Successful chat response payload."""

    session_id: str = Field(..., description="Session that produced this response")
    message: str = Field(..., description="Assistant reply text")
    agent_type: AgentType = Field(..., description="Agent that handled the request")
    status: StatusCode = Field(default=StatusCode.OK, description="HTTP status code")


class SessionResponse(BaseSchema):
    """Successful session creation payload."""

    session_id: str = Field(..., description="Newly created session ID")
    status: StatusCode = Field(default=StatusCode.CREATED, description="HTTP status code")


class ErrorResponse(BaseSchema):
    """Structured error payload returned on exceptions."""

    error_type: str = Field(..., description="Exception class name")
    detail: str = Field(..., description="Human-readable error description")
    status: StatusCode = Field(..., description="HTTP status code")
