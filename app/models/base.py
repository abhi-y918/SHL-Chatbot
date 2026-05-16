"""Base Pydantic schema all models extend."""

from pydantic import BaseModel


class BaseSchema(BaseModel):
    """Root schema with shared Pydantic v2 config."""

    model_config = {"populate_by_name": True, "use_enum_values": True}
