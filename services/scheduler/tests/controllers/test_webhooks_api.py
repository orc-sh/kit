"""
Integration tests for Webhooks API endpoints.

These tests verify the complete API functionality including
request/response handling, authentication, and database interactions.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.context.user_context import set_current_user_context
from app.models.user import User
from tests.factories import ProjectFactory


@pytest.mark.integration
class TestCreateCrownWebhookAPI:
    """Tests for POST /webhooks endpoint."""

    def test_create_webhook_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test creating a webhook with job and project successfully."""
        set_current_user_context(test_user)

        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                    "timezone": "UTC",
                    "enabled": True,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer token"},
                    "query_params": {"key": "value"},
                    "body_template": '{"event": "test"}',
                    "content_type": "application/json",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify project (created with user's name)
        assert "project" in data
        assert data["project"]["user_id"] == test_user.id
        assert data["project"]["name"] == test_user.name
        assert "id" in data["project"]

        # Verify job
        assert "job" in data
        assert data["job"]["project_id"] == data["project"]["id"]
        assert data["job"]["name"] == "Test Job"
        assert data["job"]["schedule"] == "0 9 * * *"
        assert data["job"]["type"] == 1
        assert data["job"]["enabled"] is True
        assert "next_run_at" in data["job"]

        # Verify webhook
        assert "webhook" in data
        assert data["webhook"]["job_id"] == data["job"]["id"]
        assert data["webhook"]["url"] == "https://api.example.com/webhook"
        assert data["webhook"]["method"] == "POST"

    def test_create_webhook_reuses_existing_project(self, client: TestClient, db_session: Session, test_user: User):
        """Test that webhook creation reuses existing project with user's name."""
        # Create project with user's name first
        existing_project = ProjectFactory.create(db_session, test_user.id, test_user.name)
        set_current_user_context(test_user)

        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "method": "POST",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Should reuse existing project
        assert data["project"]["id"] == existing_project.id
        assert data["project"]["name"] == test_user.name

    def test_create_webhook_without_auth(self, client: TestClient):
        """Test creating a webhook without authentication fails."""
        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                },
            },
        )

        assert response.status_code == 401

    def test_create_webhook_invalid_cron_schedule(self, client: TestClient, test_user: User):
        """Test creating a webhook with invalid cron schedule fails."""
        set_current_user_context(test_user)

        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "invalid cron",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                },
            },
        )

        assert response.status_code == 400
        assert "cron" in response.json()["detail"].lower()

    def test_create_webhook_missing_job_fields(self, client: TestClient, test_user: User):
        """Test creating webhook with missing required job fields fails."""
        set_current_user_context(test_user)

        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    # Missing schedule and type
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                },
            },
        )

        assert response.status_code == 422

    def test_create_webhook_missing_webhook_url(self, client: TestClient, test_user: User):
        """Test creating webhook with missing URL fails."""
        set_current_user_context(test_user)

        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    # Missing url
                    "method": "POST",
                },
            },
        )

        assert response.status_code == 422

    def test_create_webhook_with_custom_timezone(self, client: TestClient, test_user: User):
        """Test creating webhook with custom timezone."""
        set_current_user_context(test_user)

        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                    "timezone": "America/New_York",
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["job"]["timezone"] == "America/New_York"

    def test_create_webhook_disabled_job(self, client: TestClient, test_user: User):
        """Test creating webhook with disabled job."""
        set_current_user_context(test_user)

        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                    "enabled": False,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["job"]["enabled"] is False

    def test_create_webhook_with_different_http_methods(self, client: TestClient, test_user: User):
        """Test creating webhooks with different HTTP methods."""
        set_current_user_context(test_user)

        for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            response = client.post(
                "/webhooks",
                json={
                    "job": {
                        "name": f"Test Job {method}",
                        "schedule": "0 9 * * *",
                        "type": 1,
                    },
                    "webhook": {
                        "url": f"https://api.example.com/{method.lower()}",
                        "method": method,
                    },
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["webhook"]["method"] == method

    def test_create_webhook_with_headers(self, client: TestClient, test_user: User):
        """Test creating webhook with custom headers."""
        set_current_user_context(test_user)

        headers = {
            "Authorization": "Bearer secret-token",
            "X-Custom-Header": "custom-value",
            "Content-Type": "application/json",
        }

        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "headers": headers,
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["webhook"]["headers"] == headers

    def test_create_webhook_with_query_params(self, client: TestClient, test_user: User):
        """Test creating webhook with query parameters."""
        set_current_user_context(test_user)

        query_params = {"api_key": "12345", "format": "json", "version": "v2"}

        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "query_params": query_params,
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["webhook"]["query_params"] == query_params

    def test_create_webhook_with_body_template(self, client: TestClient, test_user: User):
        """Test creating webhook with body template."""
        set_current_user_context(test_user)

        body_template = '{"event": "scheduled", "timestamp": "{{timestamp}}", "data": "{{data}}"}'

        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "body_template": body_template,
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["webhook"]["body_template"] == body_template

    def test_create_webhook_with_custom_content_type(self, client: TestClient, test_user: User):
        """Test creating webhook with custom content type."""
        set_current_user_context(test_user)

        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "content_type": "application/xml",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["webhook"]["content_type"] == "application/xml"

    def test_create_multiple_webhooks_same_user(self, client: TestClient, db_session: Session, test_user: User):
        """Test creating multiple webhooks for the same user."""
        set_current_user_context(test_user)

        # Create first webhook
        response1 = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Job 1",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook1",
                },
            },
        )
        assert response1.status_code == 201
        project_id_1 = response1.json()["project"]["id"]

        # Create second webhook
        response2 = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Job 2",
                    "schedule": "0 10 * * *",
                    "type": 2,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook2",
                },
            },
        )
        assert response2.status_code == 201
        project_id_2 = response2.json()["project"]["id"]

        # Should reuse the same project
        assert project_id_1 == project_id_2

        # Jobs should be different
        assert response1.json()["job"]["id"] != response2.json()["job"]["id"]

    def test_create_webhooks_different_users(self, client: TestClient, test_user: User, another_user: User):
        """Test creating webhooks for different users creates separate projects."""
        # User 1 creates webhook
        set_current_user_context(test_user)
        response1 = client.post(
            "/webhooks",
            json={
                "job": {"name": "Job 1", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook1"},
            },
        )
        assert response1.status_code == 201

        # User 2 creates webhook
        set_current_user_context(another_user)
        response2 = client.post(
            "/webhooks",
            json={
                "job": {"name": "Job 2", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook2"},
            },
        )
        assert response2.status_code == 201

        # Projects should be different
        assert response1.json()["project"]["id"] != response2.json()["project"]["id"]
        assert response1.json()["project"]["user_id"] == test_user.id
        assert response2.json()["project"]["user_id"] == another_user.id


@pytest.mark.integration
class TestWebhookAPIWorkflow:
    """End-to-end workflow tests for webhooks API."""

    def test_complete_webhook_creation_workflow(self, client: TestClient, db_session: Session, test_user: User):
        """Test complete workflow: create webhook, verify all entities."""
        set_current_user_context(test_user)

        # Create webhook
        response = client.post(
            "/webhooks",
            json={
                "job": {
                    "name": "Daily Report",
                    "schedule": "0 9 * * *",
                    "type": 1,
                    "timezone": "UTC",
                    "enabled": True,
                },
                "webhook": {
                    "url": "https://api.example.com/daily-report",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer token"},
                    "content_type": "application/json",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify project exists in database
        from app.services.project_service import get_project_service

        project_service = get_project_service(db_session)
        project = project_service.get_project(data["project"]["id"], test_user.id)
        assert project is not None
        assert project.name == test_user.name

        # Verify job exists in database
        from app.services.job_service import get_job_service

        job_service = get_job_service(db_session)
        job = job_service.get_job(data["job"]["id"])
        assert job is not None
        assert job.name == "Daily Report"
        assert job.project_id == project.id

        # Verify webhook exists in database
        from app.services.webhook_service import get_webhook_service

        webhook_service = get_webhook_service(db_session)
        webhook = webhook_service.get_webhook(data["webhook"]["id"])
        assert webhook is not None
        assert webhook.url == "https://api.example.com/daily-report"
        assert webhook.job_id == job.id

    def test_idempotent_project_creation(self, client: TestClient, test_user: User):
        """Test that multiple webhook creations reuse the same project."""
        set_current_user_context(test_user)

        project_ids = set()

        # Create 5 webhooks
        for i in range(5):
            response = client.post(
                "/webhooks",
                json={
                    "job": {
                        "name": f"Job {i}",
                        "schedule": "0 9 * * *",
                        "type": 1,
                    },
                    "webhook": {
                        "url": f"https://api.example.com/webhook{i}",
                    },
                },
            )
            assert response.status_code == 201
            project_ids.add(response.json()["project"]["id"])

        # All should use the same project
        assert len(project_ids) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
