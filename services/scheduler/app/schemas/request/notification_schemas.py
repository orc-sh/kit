from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class CreateNotificationRequest(BaseModel):
    """Request schema for creating a new notification"""

    type: Literal["email", "slack", "discord", "webhook"] = Field(..., description="Notification type")
    name: str = Field(..., min_length=1, max_length=255, description="Notification channel name")
    enabled: bool = Field(True, description="Whether the notification is enabled")
    config: dict = Field(..., description="Notification configuration (email address or webhook URL)")

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: dict, info) -> dict:
        """Validate configuration based on notification type"""
        notification_type = info.data.get("type")

        if notification_type == "email":
            if "email" not in v or not v["email"]:
                raise ValueError("Email address is required for email notifications")
            # Validate email format (basic check)
            email = v["email"]
            if "@" not in email or "." not in email.split("@")[1]:
                raise ValueError("Invalid email address format")
        elif notification_type in ["slack", "discord", "webhook"]:
            if "webhook_url" not in v or not v["webhook_url"]:
                raise ValueError("Webhook URL is required for slack, discord, and webhook notifications")
            # Validate URL format (basic check)
            webhook_url = v["webhook_url"]
            if not webhook_url.startswith(("http://", "https://")):
                raise ValueError("Webhook URL must start with http:// or https://")

        return v


class UpdateNotificationRequest(BaseModel):
    """Request schema for updating an existing notification"""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated notification channel name")
    enabled: Optional[bool] = Field(None, description="Whether the notification is enabled")
    config: Optional[dict] = Field(None, description="Updated notification configuration")

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: Optional[dict]) -> Optional[dict]:
        """Validate configuration if provided"""
        if v is None:
            return v

        # Basic validation - full validation should be done in service layer
        # where we have access to the existing notification type
        if "email" in v:
            email = v["email"]
            if email and ("@" not in email or "." not in email.split("@")[1] if "@" in email else True):
                raise ValueError("Invalid email address format")
        if "webhook_url" in v:
            webhook_url = v["webhook_url"]
            if webhook_url and not webhook_url.startswith(("http://", "https://")):
                raise ValueError("Webhook URL must start with http:// or https://")

        return v
