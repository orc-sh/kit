"""
Notification service for managing CRUD operations on notifications.
"""

import json
import logging
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.notifications import Notification, NotificationType
from app.services.account_service import get_account_service

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
        Create a new notification for a user's account.

        Args:
            user_id: ID of the user creating the notification
            notification_type: Type of notification (email, slack, discord, webhook)
            name: Name of the notification channel
            enabled: Whether the notification is enabled
            config: Configuration dictionary (email address or webhook URL)

        Returns:
            Created Notification instance

        Raises:
            ValueError: If user has no accounts or other validation fails
        """
        # Get user's first account (or create one if needed)
        account_service = get_account_service(self.db)
        accounts = account_service.get_accounts(user_id=user_id, skip=0, limit=1)

        if not accounts:
            raise ValueError("User has no accounts. Please create a account first.")

        # Use the first account
        account = accounts[0]
        account_id = account.id

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
            account_id=account_id,
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
        self, user_id: str, account_id: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications for a user, optionally filtered by account.

        Args:
            user_id: ID of the user
            account_id: Optional account ID to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of Notification instances
        """
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if account_id:
            query = query.filter(Notification.account_id == account_id)
        return query.offset(skip).limit(limit).all()

    def get_notifications_paginated(
        self, user_id: str, account_id: Optional[str] = None, page: int = 1, page_size: int = 10
    ) -> tuple[List[Notification], dict]:
        """
        Get all notifications for a user with page-based pagination and metadata.

        Args:
            user_id: ID of the user
            account_id: Optional account ID to filter by
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
        if account_id:
            query = query.filter(Notification.account_id == account_id)

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

    def count_notifications(self, user_id: str, account_id: Optional[str] = None) -> int:
        """
        Count the total number of notifications for a user.

        Args:
            user_id: ID of the user
            account_id: Optional account ID to filter by

        Returns:
            Total count of notifications
        """
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if account_id:
            query = query.filter(Notification.account_id == account_id)
        return query.count()

    def has_email_notification(self, account_id: str, user_id: str) -> bool:
        """
        Check if an email notification already exists for the given account.

        Args:
            account_id: ID of the account
            user_id: ID of the user

        Returns:
            True if an email notification exists, False otherwise
        """
        existing = (
            self.db.query(Notification)
            .filter(
                Notification.account_id == account_id,
                Notification.user_id == user_id,
                Notification.type == NotificationType.EMAIL,
            )
            .first()
        )
        return existing is not None

    def create_email_notification_if_not_exists(
        self, account_id: str, user_id: str, email: str, name: str = "Default Email Channel"
    ) -> Optional[Notification]:
        """
        Create an email notification channel if it doesn't already exist for the account.
        This is a "soft" operation - it will not raise exceptions if creation fails.

        Args:
            account_id: ID of the account
            user_id: ID of the user
            email: Email address for the notification
            name: Name for the notification channel (default: "Default Email Channel")

        Returns:
            Created Notification instance if successful, None if it already exists or creation fails
        """
        try:
            # Check if email notification already exists
            if self.has_email_notification(account_id, user_id):
                logger.info(f"Email notification already exists for account {account_id}, skipping creation")
                return None

            # Validate email
            if not email or not email.strip():
                logger.warning(f"Cannot create email notification for account {account_id}: no email provided")
                return None

            # Create the notification
            notification = Notification(
                id=str(uuid.uuid4()),
                account_id=account_id,
                user_id=user_id,
                type=NotificationType.EMAIL,
                name=name,
                enabled="true",
                config=json.dumps({"email": email.strip()}),
            )
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            logger.info(f"Created email notification channel for account {account_id} with email {email}")
            return notification
        except Exception as e:
            # Soft failure - log error but don't raise
            logger.error(f"Failed to create email notification for account {account_id}: {str(e)}")
            # Rollback any partial changes
            try:
                self.db.rollback()
            except Exception:
                pass
            return None

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
