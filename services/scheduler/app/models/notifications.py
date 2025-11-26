"""
Notification model for managing project notifications.
"""

from sqlalchemy import TIMESTAMP, Column, Enum, ForeignKey, Index, String, Text
from sqlalchemy.sql import func

from .base import Base


class NotificationType:
    """Notification type constants"""

    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), nullable=False)
    type = Column(
        Enum(
            NotificationType.EMAIL,
            NotificationType.SLACK,
            NotificationType.DISCORD,
            NotificationType.WEBHOOK,
            name="notification_type",
            create_constraint=True,
        ),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    enabled = Column(String(10), nullable=False, default="true")  # Store as string for MySQL compatibility
    # Configuration stored as JSON string
    # For email: {"email": "user@example.com"}
    # For slack/discord/webhook: {"webhook_url": "https://..."}
    config = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        Index("idx_notifications_project_id", "project_id"),
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_type", "type"),
    )
