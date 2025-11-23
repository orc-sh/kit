"""
Response schemas for job operations.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class JobResponse(BaseModel):
    """Schema for job response"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "project_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Daily Report Job",
                "schedule": "0 9 * * *",
                "type": 1,
                "timezone": "UTC",
                "enabled": True,
                "last_run_at": None,
                "next_run_at": "2024-01-02T09:00:00",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
        },
    )

    id: str = Field(..., description="Job ID")
    project_id: str = Field(..., description="Project ID this job belongs to")
    name: str = Field(..., description="Name of the job")
    schedule: str = Field(..., description="Cron expression for scheduling")
    type: int = Field(..., description="Job type identifier")
    timezone: str = Field(..., description="Timezone for the schedule")
    enabled: bool = Field(..., description="Whether the job is enabled")
    last_run_at: Optional[datetime] = Field(None, description="Last time the job ran")
    next_run_at: datetime = Field(..., description="Next scheduled run time")
    created_at: datetime = Field(..., description="When the job was created")
    updated_at: datetime = Field(..., description="When the job was last updated")
