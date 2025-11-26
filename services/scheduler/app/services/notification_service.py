"""
Notification service for managing CRUD operations on notifications.
"""

import json
import logging
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.notifications import Notification, NotificationType
from app.services.project_service import get_project_service

logger = logging.getLogger(__name__)


class NotificationService:
    """Service class for notification-related operations"""

    def __init__(self, db: Session):
        """
        Initialize the notification service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_notification(
        self,
        user_id: str,
        notification_type: str,
        name: str,
        enabled: bool,
        config: dict,
    ) -> Notification:
        """
        Create a new notification for a user's project.

        Args:
            user_id: ID of the user creating the notification
            notification_type: Type of notification (email, slack, discord, webhook)
            name: Name of the notification channel
            enabled: Whether the notification is enabled
            config: Configuration dictionary (email address or webhook URL)

        Returns:
            Created Notification instance

        Raises:
            ValueError: If user has no projects or other validation fails
        """
        # Get user's first project (or create one if needed)
        project_service = get_project_service(self.db)
        projects = project_service.get_projects(user_id=user_id, skip=0, limit=1)

        if not projects:
            raise ValueError("User has no projects. Please create a project first.")

        # Use the first project
        project = projects[0]
        project_id = project.id

        # Validate notification type
        if notification_type not in [
            NotificationType.EMAIL,
            NotificationType.SLACK,
            NotificationType.DISCORD,
            NotificationType.WEBHOOK,
        ]:
            raise ValueError(f"Invalid notification type: {notification_type}")

        # Validate config based on type
        if notification_type == NotificationType.EMAIL:
            if "email" not in config or not config["email"]:
                raise ValueError("Email address is required for email notifications")
        else:
            if "webhook_url" not in config or not config["webhook_url"]:
                raise ValueError("Webhook URL is required for slack, discord, and webhook notifications")

        notification = Notification(
            id=str(uuid.uuid4()),
            project_id=project_id,
            user_id=user_id,
            type=notification_type,
            name=name,
            enabled="true" if enabled else "false",
            config=json.dumps(config),
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_notification(self, notification_id: str, user_id: str) -> Optional[Notification]:
        """
        Get a specific notification by ID for a user.

        Args:
            notification_id: ID of the notification to retrieve
            user_id: ID of the user (for authorization)

        Returns:
            Notification instance if found and owned by user, None otherwise
        """
        return (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

    def get_notifications(
        self, user_id: str, project_id: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications for a user, optionally filtered by project.

        Args:
            user_id: ID of the user
            project_id: Optional project ID to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of Notification instances
        """
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if project_id:
            query = query.filter(Notification.project_id == project_id)
        return query.offset(skip).limit(limit).all()

    def get_notifications_paginated(
        self, user_id: str, project_id: Optional[str] = None, page: int = 1, page_size: int = 10
    ) -> tuple[List[Notification], dict]:
        """
        Get all notifications for a user with page-based pagination and metadata.

        Args:
            user_id: ID of the user
            project_id: Optional project ID to filter by
            page: Page number (1-indexed)
            page_size: Number of records per page

        Returns:
            Tuple of (List of Notification instances, pagination metadata dict)
        """
        # Ensure page is at least 1
        page = max(1, page)
        page_size = max(1, min(page_size, 100))  # Cap at 100 items per page

        # Build query
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if project_id:
            query = query.filter(Notification.project_id == project_id)

        # Get total count
        total_entries = query.count()

        # Calculate total pages
        total_pages = (total_entries + page_size - 1) // page_size if total_entries > 0 else 1

        # Ensure page doesn't exceed total pages
        page = min(page, total_pages)

        # Calculate offset
        skip = (page - 1) * page_size

        # Get notifications for current page
        notifications = query.offset(skip).limit(page_size).all()

        # Build pagination metadata
        has_next = page < total_pages
        has_previous = page > 1

        pagination_metadata = {
            "current_page": page,
            "total_pages": total_pages,
            "total_entries": total_entries,
            "page_size": page_size,
            "has_next": has_next,
            "has_previous": has_previous,
            "next_page": page + 1 if has_next else None,
            "previous_page": page - 1 if has_previous else None,
        }

        return notifications, pagination_metadata

    def update_notification(
        self,
        notification_id: str,
        user_id: str,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
        config: Optional[dict] = None,
    ) -> Optional[Notification]:
        """
        Update a notification.

        Args:
            notification_id: ID of the notification to update
            user_id: ID of the user (for authorization)
            name: New name for the notification (optional)
            enabled: New enabled status (optional)
            config: New configuration (optional)

        Returns:
            Updated Notification instance if found and owned by user, None otherwise
        """
        notification = self.get_notification(notification_id, user_id)
        if not notification:
            return None

        if name is not None:
            notification.name = name  # type: ignore[assignment]
        if enabled is not None:
            notification.enabled = "true" if enabled else "false"  # type: ignore[assignment]
        if config is not None:
            # Validate config based on notification type
            if notification.type == NotificationType.EMAIL:
                if "email" not in config or not config["email"]:
                    raise ValueError("Email address is required for email notifications")
            else:
                if "webhook_url" not in config or not config["webhook_url"]:
                    raise ValueError("Webhook URL is required for slack, discord, and webhook notifications")
            notification.config = json.dumps(config)  # type: ignore[assignment]

        self.db.commit()
        self.db.refresh(notification)
        return notification

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """
        Delete a notification.

        Args:
            notification_id: ID of the notification to delete
            user_id: ID of the user (for authorization)

        Returns:
            True if notification was deleted, False if not found or not owned by user
        """
        notification = self.get_notification(notification_id, user_id)
        if not notification:
            return False

        self.db.delete(notification)
        self.db.commit()
        return True

    def count_notifications(self, user_id: str, project_id: Optional[str] = None) -> int:
        """
        Count the total number of notifications for a user.

        Args:
            user_id: ID of the user
            project_id: Optional project ID to filter by

        Returns:
            Total count of notifications
        """
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if project_id:
            query = query.filter(Notification.project_id == project_id)
        return query.count()

    def _parse_config(self, notification: Notification) -> dict:
        """
        Parse the JSON config string from a notification.

        Args:
            notification: Notification instance

        Returns:
            Parsed configuration dictionary
        """
        try:
            return json.loads(notification.config) if notification.config else {}
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Failed to parse config for notification {notification.id}")
            return {}


def get_notification_service(db: Session) -> NotificationService:
    """
    Factory function to create a NotificationService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        NotificationService instance
    """
    return NotificationService(db)
