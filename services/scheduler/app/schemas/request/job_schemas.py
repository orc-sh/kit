"""
Request schemas for job operations.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateJobRequest(BaseModel):
    """Schema for creating a new job"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Daily Report Job",
                "schedule": "0 9 * * *",
                "type": 1,
                "timezone": "UTC",
                "enabled": True,
            }
        }
    )

    name: str = Field(..., description="Name of the job", min_length=1, max_length=255)
    schedule: str = Field(..., description="Cron expression for scheduling", min_length=1, max_length=50)
    type: int = Field(..., description="Job type identifier")
    timezone: str = Field(default="UTC", description="Timezone for the schedule", max_length=50)
    enabled: bool = Field(default=True, description="Whether the job is enabled")


class UpdateJobRequest(BaseModel):
    """Schema for updating an existing job"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Daily Report Job",
                "schedule": "0 10 * * *",
                "enabled": False,
            }
        }
    )

    name: Optional[str] = Field(None, description="Name of the job", min_length=1, max_length=255)
    schedule: Optional[str] = Field(None, description="Cron expression for scheduling", min_length=1, max_length=50)
    type: Optional[int] = Field(None, description="Job type identifier")
    timezone: Optional[str] = Field(None, description="Timezone for the schedule", max_length=50)
    enabled: Optional[bool] = Field(None, description="Whether the job is enabled")
