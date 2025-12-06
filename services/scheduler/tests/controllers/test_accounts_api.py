"""
Integration tests for Accounts API endpoints.

These tests verify the complete API functionality including
request/response handling, authentication, and database interactions.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.context.user_context import set_current_user_context
from app.models.user import User
from tests.factories import AccountFactory


@pytest.mark.integration
class TestCreateAccountAPI:
    """Tests for POST /accounts endpoint."""

    def test_create_account_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test creating a account successfully."""
        set_current_user_context(test_user)

        response = client.post(
            "/accounts",
            json={"name": "My Test Account"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Test Account"
        assert data["user_id"] == test_user.id
        assert "id" in data
        assert "created_at" in data

    def test_create_account_without_auth(self, client: TestClient):
        """Test creating a account without authentication fails."""
        response = client.post(
            "/accounts",
            json={"name": "Test Account"},
        )

        assert response.status_code == 401

    def test_create_account_empty_name(self, client: TestClient, test_user: User):
        """Test creating a account with empty name fails validation."""
        set_current_user_context(test_user)

        response = client.post(
            "/accounts",
            json={"name": ""},
        )

        assert response.status_code == 422

    def test_create_account_missing_name(self, client: TestClient, test_user: User):
        """Test creating a account without name field fails."""
        set_current_user_context(test_user)

        response = client.post(
            "/accounts",
            json={},
        )

        assert response.status_code == 422

    def test_create_account_name_too_long(self, client: TestClient, test_user: User):
        """Test creating a account with name exceeding max length."""
        set_current_user_context(test_user)

        response = client.post(
            "/accounts",
            json={"name": "x" * 256},  # Max is 255
        )

        assert response.status_code == 422

    def test_create_multiple_accounts_different_users(
        self, client: TestClient, db_session: Session, test_user: User, another_user: User
    ):
        """Test that different users can create accounts with the same name."""
        # User 1 creates account
        set_current_user_context(test_user)
        response1 = client.post("/accounts", json={"name": "Shared Name"})
        assert response1.status_code == 201

        # User 2 creates account with same name
        set_current_user_context(another_user)
        response2 = client.post("/accounts", json={"name": "Shared Name"})
        assert response2.status_code == 201

        # Should be different accounts
        assert response1.json()["id"] != response2.json()["id"]
        assert response1.json()["user_id"] != response2.json()["user_id"]


@pytest.mark.integration
class TestGetAccountsAPI:
    """Tests for GET /accounts endpoint (list all accounts)."""

    def test_get_accounts_empty_list(self, client: TestClient, test_user: User):
        """Test getting accounts when user has none."""
        set_current_user_context(test_user)

        response = client.get("/accounts")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["total_entries"] == 0
        assert data["pagination"]["total_pages"] == 1

    def test_get_accounts_with_data(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting accounts with pagination."""
        # Create accounts
        AccountFactory.create_batch(db_session, test_user.id, count=5)
        set_current_user_context(test_user)

        response = client.get("/accounts")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["total_entries"] == 5
        assert data["pagination"]["current_page"] == 1
        assert data["pagination"]["has_next"] is False

    def test_get_accounts_pagination_first_page(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting first page of accounts."""
        # Create 25 accounts
        AccountFactory.create_batch(db_session, test_user.id, count=25)
        set_current_user_context(test_user)

        response = client.get("/accounts?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["pagination"]["current_page"] == 1
        assert data["pagination"]["total_pages"] == 3
        assert data["pagination"]["total_entries"] == 25
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_previous"] is False
        assert data["pagination"]["next_page"] == 2
        assert data["pagination"]["previous_page"] is None

    def test_get_accounts_pagination_middle_page(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting middle page of accounts."""
        AccountFactory.create_batch(db_session, test_user.id, count=25)
        set_current_user_context(test_user)

        response = client.get("/accounts?page=2&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["pagination"]["current_page"] == 2
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_previous"] is True
        assert data["pagination"]["next_page"] == 3
        assert data["pagination"]["previous_page"] == 1

    def test_get_accounts_pagination_last_page(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting last page of accounts."""
        AccountFactory.create_batch(db_session, test_user.id, count=25)
        set_current_user_context(test_user)

        response = client.get("/accounts?page=3&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["current_page"] == 3
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["next_page"] is None

    def test_get_accounts_custom_page_size(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting accounts with custom page size."""
        AccountFactory.create_batch(db_session, test_user.id, count=20)
        set_current_user_context(test_user)

        response = client.get("/accounts?page=1&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["page_size"] == 5
        assert data["pagination"]["total_pages"] == 4

    def test_get_accounts_filters_by_user(
        self, client: TestClient, db_session: Session, test_user: User, another_user: User
    ):
        """Test that users only see their own accounts."""
        # Create accounts for different users
        AccountFactory.create_batch(db_session, test_user.id, count=3)
        AccountFactory.create_batch(db_session, another_user.id, count=5)

        set_current_user_context(test_user)
        response = client.get("/accounts")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        assert all(p["user_id"] == test_user.id for p in data["data"])

    def test_get_accounts_without_auth(self, client: TestClient):
        """Test getting accounts without authentication fails."""
        response = client.get("/accounts")

        assert response.status_code == 401

    def test_get_accounts_invalid_page_number(self, client: TestClient, test_user: User):
        """Test that invalid page numbers are handled."""
        set_current_user_context(test_user)

        response = client.get("/accounts?page=0")

        # Should use minimum page of 1
        assert response.status_code == 422  # Validation error

    def test_get_accounts_page_size_too_large(self, client: TestClient, db_session: Session, test_user: User):
        """Test that page_size is capped at maximum."""
        AccountFactory.create_batch(db_session, test_user.id, count=150)
        set_current_user_context(test_user)

        response = client.get("/accounts?page=1&page_size=200")

        # Should be capped at 100
        assert response.status_code == 422  # Validation error for exceeding max


@pytest.mark.integration
class TestGetAccountAPI:
    """Tests for GET /accounts/{account_id} endpoint."""

    def test_get_account_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting a specific account by ID."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        set_current_user_context(test_user)

        response = client.get(f"/accounts/{account.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == account.id
        assert data["name"] == "Test Account"
        assert data["user_id"] == test_user.id

    def test_get_account_not_found(self, client: TestClient, test_user: User):
        """Test getting a non-existent account returns 404."""
        set_current_user_context(test_user)

        response = client.get("/accounts/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_account_wrong_user(self, client: TestClient, db_session: Session, test_user: User, another_user: User):
        """Test that users can't access other users' accounts."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        set_current_user_context(another_user)

        response = client.get(f"/accounts/{account.id}")

        assert response.status_code == 404

    def test_get_account_without_auth(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting a account without authentication fails."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")

        response = client.get(f"/accounts/{account.id}")

        assert response.status_code == 401


@pytest.mark.integration
class TestUpdateAccountAPI:
    """Tests for PUT /accounts/{account_id} endpoint."""

    def test_update_account_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test updating a account successfully."""
        account = AccountFactory.create(db_session, test_user.id, "Original Name")
        set_current_user_context(test_user)

        response = client.put(
            f"/accounts/{account.id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == account.id
        assert data["name"] == "Updated Name"
        assert data["user_id"] == test_user.id

    def test_update_account_not_found(self, client: TestClient, test_user: User):
        """Test updating a non-existent account returns 404."""
        set_current_user_context(test_user)

        response = client.put(
            "/accounts/non-existent-id",
            json={"name": "New Name"},
        )

        assert response.status_code == 404

    def test_update_account_wrong_user(
        self, client: TestClient, db_session: Session, test_user: User, another_user: User
    ):
        """Test that users can't update other users' accounts."""
        account = AccountFactory.create(db_session, test_user.id, "Original Name")
        set_current_user_context(another_user)

        response = client.put(
            f"/accounts/{account.id}",
            json={"name": "Hacked Name"},
        )

        assert response.status_code == 404

        # Verify account unchanged
        db_session.refresh(account)
        assert account.name == "Original Name"

    def test_update_account_empty_name(self, client: TestClient, db_session: Session, test_user: User):
        """Test updating with empty name fails validation."""
        account = AccountFactory.create(db_session, test_user.id, "Original Name")
        set_current_user_context(test_user)

        response = client.put(
            f"/accounts/{account.id}",
            json={"name": ""},
        )

        assert response.status_code == 422

    def test_update_account_missing_name(self, client: TestClient, db_session: Session, test_user: User):
        """Test updating without name field fails."""
        account = AccountFactory.create(db_session, test_user.id, "Original Name")
        set_current_user_context(test_user)

        response = client.put(
            f"/accounts/{account.id}",
            json={},
        )

        assert response.status_code == 422

    def test_update_account_without_auth(self, client: TestClient, db_session: Session, test_user: User):
        """Test updating a account without authentication fails."""
        account = AccountFactory.create(db_session, test_user.id, "Original Name")

        response = client.put(
            f"/accounts/{account.id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestDeleteAccountAPI:
    """Tests for DELETE /accounts/{account_id} endpoint."""

    def test_delete_account_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test deleting a account successfully."""
        account = AccountFactory.create(db_session, test_user.id, "To Delete")
        account_id = account.id
        set_current_user_context(test_user)

        response = client.delete(f"/accounts/{account_id}")

        assert response.status_code == 204
        assert response.content == b""

        # Verify account is deleted
        verify_response = client.get(f"/accounts/{account_id}")
        assert verify_response.status_code == 404

    def test_delete_account_not_found(self, client: TestClient, test_user: User):
        """Test deleting a non-existent account returns 404."""
        set_current_user_context(test_user)

        response = client.delete("/accounts/non-existent-id")

        assert response.status_code == 404

    def test_delete_account_wrong_user(
        self, client: TestClient, db_session: Session, test_user: User, another_user: User
    ):
        """Test that users can't delete other users' accounts."""
        account = AccountFactory.create(db_session, test_user.id, "Protected")
        account_id = account.id
        set_current_user_context(another_user)

        response = client.delete(f"/accounts/{account_id}")

        assert response.status_code == 404

        # Verify account still exists
        set_current_user_context(test_user)
        verify_response = client.get(f"/accounts/{account_id}")
        assert verify_response.status_code == 200

    def test_delete_account_without_auth(self, client: TestClient, db_session: Session, test_user: User):
        """Test deleting a account without authentication fails."""
        account = AccountFactory.create(db_session, test_user.id, "To Delete")

        response = client.delete(f"/accounts/{account.id}")

        assert response.status_code == 401


@pytest.mark.integration
class TestAccountsAPIWorkflow:
    """End-to-end workflow tests for accounts API."""

    def test_complete_crud_workflow(self, client: TestClient, test_user: User):
        """Test complete CRUD workflow: create, read, update, delete."""
        set_current_user_context(test_user)

        # 1. Create a account
        create_response = client.post("/accounts", json={"name": "Workflow Account"})
        assert create_response.status_code == 201
        account_id = create_response.json()["id"]

        # 2. Read the account
        get_response = client.get(f"/accounts/{account_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Workflow Account"

        # 3. Update the account
        update_response = client.put(
            f"/accounts/{account_id}",
            json={"name": "Updated Workflow Account"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Workflow Account"

        # 4. Delete the account
        delete_response = client.delete(f"/accounts/{account_id}")
        assert delete_response.status_code == 204

        # 5. Verify it's gone
        verify_response = client.get(f"/accounts/{account_id}")
        assert verify_response.status_code == 404

    def test_multi_user_isolation(self, client: TestClient, test_user: User, another_user: User):
        """Test that users' accounts are properly isolated."""
        # User 1 creates accounts
        set_current_user_context(test_user)
        client.post("/accounts", json={"name": "User 1 Account 1"})
        client.post("/accounts", json={"name": "User 1 Account 2"})

        user1_accounts = client.get("/accounts").json()
        assert len(user1_accounts["data"]) == 2

        # User 2 creates accounts
        set_current_user_context(another_user)
        client.post("/accounts", json={"name": "User 2 Account 1"})

        user2_accounts = client.get("/accounts").json()
        assert len(user2_accounts["data"]) == 1

        # Verify isolation
        assert user1_accounts["data"][0]["id"] != user2_accounts["data"][0]["id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
