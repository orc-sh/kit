"""
Request schemas for URL operations.
"""

from pydantic import BaseModel, ConfigDict


class CreateUrlRequest(BaseModel):
    """Schema for creating a new URL"""

    model_config = ConfigDict(json_schema_extra={"example": {}})


class UpdateUrlRequest(BaseModel):
    """Schema for updating an existing URL"""

    model_config = ConfigDict(json_schema_extra={"example": {}})
