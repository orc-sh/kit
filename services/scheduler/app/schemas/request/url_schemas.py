"""
Request schemas for URL operations.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateUrlRequest(BaseModel):
    """Schema for creating a new URL"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account_id": "123e4567-e89b-12d3-a456-426614174001",
            }
        }
    )

    account_id: str = Field(..., description="Account ID to associate the URL with", min_length=1)


class UpdateUrlRequest(BaseModel):
    """Schema for updating an existing URL"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account_id": "123e4567-e89b-12d3-a456-426614174001",
            }
        }
    )

    account_id: Optional[str] = Field(None, description="Account ID to associate the URL with", min_length=1)
