"""
Webhook-specific test data factories and helpers.
"""

import uuid
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.webhooks import Webhook


class WebhookFactory:
    """Factory for creating Webhook test objects."""

    @staticmethod
    def create(
        db: Session,
        job_id: str,
        url: Optional[str] = None,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body_template: Optional[str] = None,
        content_type: str = "application/json",
        webhook_id: Optional[str] = None,
    ) -> Webhook:
        """
        Create a webhook in the database.

        Args:
            db: Database session
            job_id: ID of the job this webhook belongs to
            url: Webhook URL
            method: HTTP method
            headers: HTTP headers
            query_params: Query parameters
            body_template: Request body template
            content_type: Content type
            webhook_id: Optional specific webhook ID

        Returns:
            Created Webhook instance
        """
        webhook = Webhook(
            id=webhook_id or str(uuid.uuid4()),
            job_id=job_id,
            url=url or f"https://api.example.com/webhook/{uuid.uuid4().hex[:8]}",
            method=method,
            headers=headers,
            query_params=query_params,
            body_template=body_template,
            content_type=content_type,
        )
        db.add(webhook)
        db.commit()
        db.refresh(webhook)
        return webhook

    @staticmethod
    def create_batch(db: Session, job_id: str, count: int = 5, **kwargs) -> list[Webhook]:
        """
        Create multiple webhooks in the database.

        Args:
            db: Database session
            job_id: ID of the job
            count: Number of webhooks to create
            **kwargs: Additional webhook attributes

        Returns:
            List of created Webhook instances
        """
        webhooks: list[Webhook] = []
        for i in range(count):
            url = f"https://api.example.com/webhook-{i + 1}"
            webhook = WebhookFactory.create(db=db, job_id=job_id, url=url, **kwargs)
            webhooks.append(webhook)
        return webhooks

    @staticmethod
    def build(
        job_id: str,
        url: Optional[str] = None,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body_template: Optional[str] = None,
        content_type: str = "application/json",
        webhook_id: Optional[str] = None,
    ) -> Webhook:
        """
        Build a webhook object without saving to database.

        Args:
            job_id: ID of the job
            url: Webhook URL
            method: HTTP method
            headers: HTTP headers
            query_params: Query parameters
            body_template: Request body template
            content_type: Content type
            webhook_id: Optional specific webhook ID

        Returns:
            Webhook instance (not saved to DB)
        """
        return Webhook(
            id=webhook_id or str(uuid.uuid4()),
            job_id=job_id,
            url=url or f"https://api.example.com/webhook/{uuid.uuid4().hex[:8]}",
            method=method,
            headers=headers,
            query_params=query_params,
            body_template=body_template,
            content_type=content_type,
        )


def create_test_webhook_data(
    url: Optional[str] = None,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
    body_template: Optional[str] = None,
    content_type: str = "application/json",
) -> dict:
    """
    Create raw webhook data dictionary (not model instance).

    Args:
        url: Webhook URL
        method: HTTP method
        headers: HTTP headers
        query_params: Query parameters
        body_template: Request body template
        content_type: Content type

    Returns:
        Dictionary with webhook data
    """
    data = {
        "url": url or f"https://api.example.com/webhook/{uuid.uuid4().hex[:8]}",
        "method": method,
        "content_type": content_type,
    }
    if headers is not None:
        data["headers"] = headers
    if query_params is not None:
        data["query_params"] = query_params
    if body_template is not None:
        data["body_template"] = body_template
    return data


def create_webhook_update_data(
    url: Optional[str] = None,
    method: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
    body_template: Optional[str] = None,
    content_type: Optional[str] = None,
) -> dict:
    """
    Create webhook update data dictionary.

    Args:
        url: Optional new URL
        method: Optional new method
        headers: Optional new headers
        query_params: Optional new query params
        body_template: Optional new body template
        content_type: Optional new content type

    Returns:
        Dictionary with update data
    """
    data = {}
    if url is not None:
        data["url"] = url
    if method is not None:
        data["method"] = method
    if headers is not None:
        data["headers"] = headers
    if query_params is not None:
        data["query_params"] = query_params
    if body_template is not None:
        data["body_template"] = body_template
    if content_type is not None:
        data["content_type"] = content_type
    return data
