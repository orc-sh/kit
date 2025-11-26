# Request schemas for scheduler service
# Add scheduler-specific request schemas here (e.g., CreateJobRequest, UpdateWebhookRequest, etc.)

from .notification_schemas import CreateNotificationRequest, UpdateNotificationRequest
from .project_schemas import CreateProjectRequest, UpdateProjectRequest
from .subscription_schemas import CancelSubscriptionRequest, UpdateSubscriptionRequest
from .url_schemas import CreateUrlRequest, UpdateUrlRequest

__all__ = [
    "CreateNotificationRequest",
    "UpdateNotificationRequest",
    "CreateProjectRequest",
    "UpdateProjectRequest",
    "UpdateSubscriptionRequest",
    "CancelSubscriptionRequest",
    "CreateUrlRequest",
    "UpdateUrlRequest",
]
