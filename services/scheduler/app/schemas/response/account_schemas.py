from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AccountResponse(BaseModel):
    """Response schema for account data"""

    model_config = ConfigDict(from_attributes=True)  # Enables ORM mode for SQLAlchemy models

    id: str = Field(..., description="Account unique identifier")
    user_id: str = Field(..., description="User ID who owns the account")
    name: str = Field(..., description="Account name")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
