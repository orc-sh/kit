from pydantic import BaseModel, Field


class CreateAccountRequest(BaseModel):
    """Request schema for creating a new account"""

    name: str = Field(..., min_length=1, max_length=255, description="Account name")


class UpdateAccountRequest(BaseModel):
    """Request schema for updating an existing account"""

    name: str = Field(..., min_length=1, max_length=255, description="Updated account name")
