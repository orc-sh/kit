from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    """Response schema for notification data"""

    model_config = ConfigDict(from_attributes=True)  # Enables ORM mode for SQLAlchemy models

    id: str = Field(..., description="Notification unique identifier")
    project_id: str = Field(..., description="Project ID the notification is associated with")
    user_id: str = Field(..., description="User ID who owns the notification")
    type: str = Field(..., description="Notification type (email, slack, discord, webhook)")
    name: str = Field(..., description="Notification channel name")
    enabled: bool = Field(..., description="Whether the notification is enabled")
    config: dict = Field(..., description="Notification configuration")
    created_at: Optional[datetime] = Field(None, description="Notification creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Notification last update timestamp")
