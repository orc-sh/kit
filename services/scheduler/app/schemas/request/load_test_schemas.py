"""
Request schemas for load test operations.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateLoadTestConfigurationRequest(BaseModel):
    """Schema for creating a new load test configuration"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "API Benchmark Configuration",
                "url": "https://api.example.com/api/users",
                "method": "GET",
                "concurrent_users": 50,
                "duration_seconds": 120,
                "requests_per_second": 100,
                "headers": {"Authorization": "Bearer token"},
            }
        }
    )

    project_id: Optional[str] = Field(
        None, description="Project ID (optional, will use user's first project if not provided)", min_length=1
    )
    name: str = Field(..., description="Name of the load test configuration", min_length=1, max_length=255)
    url: str = Field(..., description="Full endpoint URL to test", min_length=1, max_length=2048)
    method: str = Field(..., description="HTTP method", max_length=10)

    # Load test parameters
    concurrent_users: int = Field(10, description="Number of concurrent users", ge=1, le=1000)
    duration_seconds: int = Field(60, description="Duration of test in seconds", ge=1, le=3600)
    requests_per_second: Optional[int] = Field(None, description="Optional rate limit (requests per second)", ge=1)

    # Request configuration
    headers: Optional[Dict[str, Any]] = Field(None, description="Request headers")
    query_params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    body_template: Optional[str] = Field(None, description="Request body template")
    content_type: Optional[str] = Field(None, description="Content type (default: application/json)", max_length=100)


class UpdateLoadTestConfigurationRequest(BaseModel):
    """Schema for updating an existing load test configuration"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated API Benchmark Configuration",
                "concurrent_users": 100,
            }
        }
    )

    name: Optional[str] = Field(None, description="Name of the load test configuration", min_length=1, max_length=255)
    concurrent_users: Optional[int] = Field(None, description="Number of concurrent users", ge=1, le=1000)
    duration_seconds: Optional[int] = Field(None, description="Duration of test in seconds", ge=1, le=3600)
    requests_per_second: Optional[int] = Field(None, description="Optional rate limit (requests per second)", ge=1)


class CreateLoadTestRunRequest(BaseModel):
    """Schema for creating a new load test run from a configuration"""

    configuration_id: str = Field(..., description="ID of the load test configuration")


class CreateLoadTestReportRequest(BaseModel):
    """Schema for creating a new load test report"""

    run_id: str = Field(..., description="ID of the load test run")
    name: Optional[str] = Field(None, description="Optional report name", max_length=255)
    notes: Optional[str] = Field(None, description="Optional notes about the report")
