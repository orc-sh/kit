"""
Notification controller for managing notification CRUD operations.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.request.notification_schemas import CreateNotificationRequest, UpdateNotificationRequest
from app.schemas.response.notification_schemas import NotificationResponse
from app.schemas.response.pagination_schemas import PaginatedResponse, PaginationMetadata
from app.services.notification_service import get_notification_service
from db.client import client

router = APIRouter()


def _notification_to_response(notification) -> NotificationResponse:
    """
    Convert a Notification model instance to a NotificationResponse.

    Args:
        notification: Notification model instance

    Returns:
        NotificationResponse with parsed config
    """
    try:
        config = json.loads(notification.config) if notification.config else {}
    except (json.JSONDecodeError, TypeError):
        config = {}

    enabled = notification.enabled.lower() == "true" if notification.enabled else False

    return NotificationResponse(
        id=notification.id,
        account_id=notification.account_id,
        user_id=notification.user_id,
        type=notification.type,
        name=notification.name,
        enabled=enabled,
        config=config,
        created_at=notification.created_at,
        updated_at=notification.updated_at,
    )


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    request: CreateNotificationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a new notification for the authenticated user.

    Args:
        request: Notification creation request
        user: Current authenticated user
        db: Database session

    Returns:
        Created notification data

    Raises:
        HTTPException: 401 if not authenticated, 400 if validation fails, 404 if account not found
    """
    notification_service = get_notification_service(db)
    try:
        notification = notification_service.create_notification(
            user_id=user.id,
            notification_type=request.type,
            name=request.name,
            enabled=request.enabled,
            config=request.config,
        )
        return _notification_to_response(notification)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=PaginatedResponse[NotificationResponse])
async def get_notifications(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (max: 100)"),
    account_id: str = Query(None, description="Optional account ID to filter by"),
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all notifications for the authenticated user with pagination.

    Args:
        page: Page number (default: 1, min: 1)
        page_size: Number of items per page (default: 10, max: 100)
        account_id: Optional account ID to filter by
        user: Current authenticated user
        db: Database session

    Returns:
        Paginated response with notifications and pagination metadata

    Raises:
        HTTPException: 401 if not authenticated
    """
    notification_service = get_notification_service(db)
    notifications, pagination_metadata = notification_service.get_notifications_paginated(
        user_id=user.id, account_id=account_id, page=page, page_size=page_size
    )

    # Convert notifications to response models
    notification_responses = [_notification_to_response(notification) for notification in notifications]

    return PaginatedResponse(
        data=notification_responses,
        pagination=PaginationMetadata(**pagination_metadata),
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a specific notification by ID.

    Args:
        notification_id: ID of the notification to retrieve
        user: Current authenticated user
        db: Database session

    Returns:
        Notification data

    Raises:
        HTTPException: 401 if not authenticated, 404 if notification not found or not owned by user
    """
    notification_service = get_notification_service(db)
    notification = notification_service.get_notification(notification_id=notification_id, user_id=user.id)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID '{notification_id}' not found",
        )

    return _notification_to_response(notification)


@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    request: UpdateNotificationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Update an existing notification.

    Args:
        notification_id: ID of the notification to update
        request: Notification update request
        user: Current authenticated user
        db: Database session

    Returns:
        Updated notification data

    Raises:
        HTTPException: 401 if not authenticated, 404 if notification not found or not owned by user,
            400 if validation fails
    """
    notification_service = get_notification_service(db)
    try:
        notification = notification_service.update_notification(
            notification_id=notification_id,
            user_id=user.id,
            name=request.name,
            enabled=request.enabled,
            config=request.config,
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification with ID '{notification_id}' not found",
            )

        return _notification_to_response(notification)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete a notification.

    Args:
        notification_id: ID of the notification to delete
        user: Current authenticated user
        db: Database session

    Returns:
        No content on success

    Raises:
        HTTPException: 401 if not authenticated, 404 if notification not found or not owned by user
    """
    notification_service = get_notification_service(db)
    deleted = notification_service.delete_notification(notification_id=notification_id, user_id=user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID '{notification_id}' not found",
        )

    return None
