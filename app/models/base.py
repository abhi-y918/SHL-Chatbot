"""Base Pydantic schema all models extend."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """Root schema providing common fields for all request/response models."""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of object creation",
    )

    model_config = {"populate_by_name": True, "use_enum_values": True}
