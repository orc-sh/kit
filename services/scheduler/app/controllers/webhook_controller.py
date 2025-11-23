"""
Webhook controller for managing Crown webhook integrations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import require_user_from_context
from app.models.user import User
from app.schemas.request.webhook_schemas import CreateCrownWebhookRequest
from app.schemas.response.webhook_schemas import CrownWebhookResponse
from app.services.job_service import get_job_service
from app.services.project_service import get_project_service
from app.services.webhook_service import get_webhook_service
from db.client import client

router = APIRouter()


@router.post("", response_model=CrownWebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_crown_webhook(
    request: CreateCrownWebhookRequest,
    user: User = Depends(require_user_from_context),
    db: Session = Depends(client),
):
    """
    Create a webhook with associated job and project via Crown integration.

    This endpoint:
    1. Uses the authenticated user's name as the project name
    2. Gets or creates a project with that name
    3. Creates a job linked to the project
    4. Creates a webhook linked to the job

    Args:
        request: Crown webhook creation request containing job and webhook data
        user: Current authenticated user (automatically extracted from JWT)
        db: Database session

    Returns:
        Combined response with project, job, and webhook data

    Raises:
        HTTPException: 401 if not authenticated, 400 if validation fails
    """
    try:
        # Step 1: Get or create project using user's name
        project_service = get_project_service(db)
        project = project_service.get_or_create_project_by_name(user_id=user.id, project_name=user.name)

        # Step 2: Create job for the project
        job_service = get_job_service(db)
        job = job_service.create_job(
            project_id=project.id,
            name=request.job.name,
            schedule=request.job.schedule,
            job_type=request.job.type,
            timezone=request.job.timezone,
            enabled=request.job.enabled,
        )

        # Step 3: Create webhook for the job
        webhook_service = get_webhook_service(db)
        webhook = webhook_service.create_webhook(
            job_id=job.id,
            url=request.webhook.url,
            method=request.webhook.method,
            headers=request.webhook.headers,
            query_params=request.webhook.query_params,
            body_template=request.webhook.body_template,
            content_type=request.webhook.content_type,
        )

        # Return combined response
        return CrownWebhookResponse(
            project=project,
            job=job,
            webhook=webhook,
        )

    except ValueError as e:
        # Handle validation errors (e.g., invalid cron expression)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create webhook: {str(e)}",
        )
