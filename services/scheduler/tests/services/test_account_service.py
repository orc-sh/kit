"""
Unit tests for AccountService.

These tests verify the service layer logic for account CRUD operations
without making actual API requests.
"""

import pytest
from sqlalchemy.orm import Session

from app.services.account_service import AccountService, get_account_service
from tests.factories import AccountFactory


@pytest.mark.unit
class TestAccountServiceCreate:
    """Tests for account creation."""

    def test_create_account_success(self, db_session: Session, test_user):
        """Test creating a account successfully."""
        service = AccountService(db_session)

        account = service.create_account(user_id=test_user.id, name="My New Account")

        assert account.id is not None
        assert account.user_id == test_user.id
        assert account.name == "My New Account"
        assert account.created_at is not None

    def test_create_account_generates_uuid(self, db_session: Session, test_user):
        """Test that account ID is auto-generated as UUID."""
        service = AccountService(db_session)

        account = service.create_account(user_id=test_user.id, name="Test Account")

        # Check UUID format
        assert len(account.id) == 36  # UUID format: 8-4-4-4-12
        assert account.id.count("-") == 4

    def test_create_multiple_accounts(self, db_session: Session, test_user):
        """Test creating multiple accounts for the same user."""
        service = AccountService(db_session)

        account1 = service.create_account(test_user.id, "Account 1")
        account2 = service.create_account(test_user.id, "Account 2")

        assert account1.id != account2.id
        assert account1.name != account2.name
        assert account1.user_id == account2.user_id


@pytest.mark.unit
class TestAccountServiceGet:
    """Tests for retrieving accounts."""

    def test_get_account_by_id_success(self, db_session: Session, test_user):
        """Test retrieving a specific account by ID."""
        # Create a account
        created_account = AccountFactory.create(db_session, test_user.id, "Test Account")

        # Retrieve it
        service = AccountService(db_session)
        account = service.get_account(created_account.id, test_user.id)

        assert account is not None
        assert account.id == created_account.id
        assert account.name == "Test Account"

    def test_get_account_not_found(self, db_session: Session, test_user):
        """Test retrieving a non-existent account returns None."""
        service = AccountService(db_session)

        account = service.get_account("non-existent-id", test_user.id)

        assert account is None

    def test_get_account_wrong_user(self, db_session: Session, test_user, another_user):
        """Test that users can't access other users' accounts."""
        # Create account for test_user
        created_account = AccountFactory.create(db_session, test_user.id, "Test Account")

        # Try to access with another_user
        service = AccountService(db_session)
        account = service.get_account(created_account.id, another_user.id)

        assert account is None

    def test_get_accounts_empty_list(self, db_session: Session, test_user):
        """Test retrieving accounts when user has none."""
        service = AccountService(db_session)

        accounts = service.get_accounts(test_user.id)

        assert accounts == []

    def test_get_accounts_returns_all_user_accounts(self, db_session: Session, test_user):
        """Test retrieving all accounts for a user."""
        # Create multiple accounts
        AccountFactory.create_batch(db_session, test_user.id, count=3, name_prefix="Account")

        service = AccountService(db_session)
        accounts = service.get_accounts(test_user.id)

        assert len(accounts) == 3
        assert all(p.user_id == test_user.id for p in accounts)

    def test_get_accounts_filters_by_user(self, db_session: Session, test_user, another_user):
        """Test that get_accounts only returns the specified user's accounts."""
        # Create accounts for different users
        AccountFactory.create_batch(db_session, test_user.id, count=2)
        AccountFactory.create_batch(db_session, another_user.id, count=3)

        service = AccountService(db_session)
        accounts = service.get_accounts(test_user.id)

        assert len(accounts) == 2
        assert all(p.user_id == test_user.id for p in accounts)

    def test_get_accounts_with_pagination(self, db_session: Session, test_user):
        """Test retrieving accounts with skip and limit."""
        # Create 10 accounts
        AccountFactory.create_batch(db_session, test_user.id, count=10)

        service = AccountService(db_session)

        # Get first 5
        accounts_page1 = service.get_accounts(test_user.id, skip=0, limit=5)
        assert len(accounts_page1) == 5

        # Get next 5
        accounts_page2 = service.get_accounts(test_user.id, skip=5, limit=5)
        assert len(accounts_page2) == 5

        # Ensure they're different accounts
        page1_ids = {p.id for p in accounts_page1}
        page2_ids = {p.id for p in accounts_page2}
        assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.unit
class TestAccountServiceGetPaginated:
    """Tests for paginated account retrieval."""

    def test_get_accounts_paginated_first_page(self, db_session: Session, test_user):
        """Test getting first page of accounts."""
        # Create 25 accounts
        AccountFactory.create_batch(db_session, test_user.id, count=25)

        service = AccountService(db_session)
        accounts, metadata = service.get_accounts_paginated(test_user.id, page=1, page_size=10)

        assert len(accounts) == 10
        assert metadata["current_page"] == 1
        assert metadata["total_pages"] == 3
        assert metadata["total_entries"] == 25
        assert metadata["page_size"] == 10
        assert metadata["has_next"] is True
        assert metadata["has_previous"] is False
        assert metadata["next_page"] == 2
        assert metadata["previous_page"] is None

    def test_get_accounts_paginated_middle_page(self, db_session: Session, test_user):
        """Test getting middle page of accounts."""
        AccountFactory.create_batch(db_session, test_user.id, count=25)

        service = AccountService(db_session)
        accounts, metadata = service.get_accounts_paginated(test_user.id, page=2, page_size=10)

        assert len(accounts) == 10
        assert metadata["current_page"] == 2
        assert metadata["has_next"] is True
        assert metadata["has_previous"] is True
        assert metadata["next_page"] == 3
        assert metadata["previous_page"] == 1

    def test_get_accounts_paginated_last_page(self, db_session: Session, test_user):
        """Test getting last page of accounts."""
        AccountFactory.create_batch(db_session, test_user.id, count=25)

        service = AccountService(db_session)
        accounts, metadata = service.get_accounts_paginated(test_user.id, page=3, page_size=10)

        assert len(accounts) == 5  # Only 5 items on last page
        assert metadata["current_page"] == 3
        assert metadata["has_next"] is False
        assert metadata["has_previous"] is True
        assert metadata["next_page"] is None
        assert metadata["previous_page"] == 2

    def test_get_accounts_paginated_empty_results(self, db_session: Session, test_user):
        """Test pagination with no accounts."""
        service = AccountService(db_session)
        accounts, metadata = service.get_accounts_paginated(test_user.id, page=1, page_size=10)

        assert len(accounts) == 0
        assert metadata["total_entries"] == 0
        assert metadata["total_pages"] == 1
        assert metadata["current_page"] == 1
        assert metadata["has_next"] is False
        assert metadata["has_previous"] is False

    def test_get_accounts_paginated_page_exceeds_total(self, db_session: Session, test_user):
        """Test requesting page beyond available pages."""
        AccountFactory.create_batch(db_session, test_user.id, count=5)

        service = AccountService(db_session)
        accounts, metadata = service.get_accounts_paginated(test_user.id, page=10, page_size=10)

        # Should return last valid page
        assert metadata["current_page"] == 1
        assert len(accounts) == 5

    def test_get_accounts_paginated_caps_page_size(self, db_session: Session, test_user):
        """Test that page_size is capped at 100."""
        AccountFactory.create_batch(db_session, test_user.id, count=150)

        service = AccountService(db_session)
        accounts, metadata = service.get_accounts_paginated(test_user.id, page=1, page_size=200)

        assert metadata["page_size"] == 100
        assert len(accounts) == 100


@pytest.mark.unit
class TestAccountServiceUpdate:
    """Tests for account updates."""

    def test_update_account_success(self, db_session: Session, test_user):
        """Test updating a account successfully."""
        # Create account
        created_account = AccountFactory.create(db_session, test_user.id, "Original Name")

        # Update it
        service = AccountService(db_session)
        updated_account = service.update_account(created_account.id, test_user.id, "Updated Name")

        assert updated_account is not None
        assert updated_account.id == created_account.id
        assert updated_account.name == "Updated Name"

    def test_update_account_not_found(self, db_session: Session, test_user):
        """Test updating a non-existent account returns None."""
        service = AccountService(db_session)

        result = service.update_account("non-existent-id", test_user.id, "New Name")

        assert result is None

    def test_update_account_wrong_user(self, db_session: Session, test_user, another_user):
        """Test that users can't update other users' accounts."""
        # Create account for test_user
        created_account = AccountFactory.create(db_session, test_user.id, "Original Name")

        # Try to update with another_user
        service = AccountService(db_session)
        result = service.update_account(created_account.id, another_user.id, "Hacked Name")

        assert result is None

        # Verify original account unchanged
        db_session.refresh(created_account)
        assert created_account.name == "Original Name"


@pytest.mark.unit
class TestAccountServiceDelete:
    """Tests for account deletion."""

    def test_delete_account_success(self, db_session: Session, test_user):
        """Test deleting a account successfully."""
        # Create account
        created_account = AccountFactory.create(db_session, test_user.id, "To Delete")
        account_id = created_account.id

        # Delete it
        service = AccountService(db_session)
        result = service.delete_account(account_id, test_user.id)

        assert result is True

        # Verify it's gone
        deleted_account = service.get_account(account_id, test_user.id)
        assert deleted_account is None

    def test_delete_account_not_found(self, db_session: Session, test_user):
        """Test deleting a non-existent account returns False."""
        service = AccountService(db_session)

        result = service.delete_account("non-existent-id", test_user.id)

        assert result is False

    def test_delete_account_wrong_user(self, db_session: Session, test_user, another_user):
        """Test that users can't delete other users' accounts."""
        # Create account for test_user
        created_account = AccountFactory.create(db_session, test_user.id, "Protected")
        account_id = created_account.id

        # Try to delete with another_user
        service = AccountService(db_session)
        result = service.delete_account(account_id, another_user.id)

        assert result is False

        # Verify account still exists
        account = service.get_account(account_id, test_user.id)
        assert account is not None


@pytest.mark.unit
class TestAccountServiceCount:
    """Tests for counting accounts."""

    def test_count_accounts_zero(self, db_session: Session, test_user):
        """Test counting when user has no accounts."""
        service = AccountService(db_session)

        count = service.count_accounts(test_user.id)

        assert count == 0

    def test_count_accounts_multiple(self, db_session: Session, test_user):
        """Test counting multiple accounts."""
        AccountFactory.create_batch(db_session, test_user.id, count=7)

        service = AccountService(db_session)
        count = service.count_accounts(test_user.id)

        assert count == 7

    def test_count_accounts_filters_by_user(self, db_session: Session, test_user, another_user):
        """Test that count only includes the specified user's accounts."""
        AccountFactory.create_batch(db_session, test_user.id, count=3)
        AccountFactory.create_batch(db_session, another_user.id, count=5)

        service = AccountService(db_session)
        count = service.count_accounts(test_user.id)

        assert count == 3


@pytest.mark.unit
class TestAccountServiceGetOrCreate:
    """Tests for get_or_create_account_by_name method."""

    def test_get_or_create_account_creates_new(self, db_session: Session, test_user):
        """Test creating a new account when it doesn't exist."""
        service = AccountService(db_session)

        account = service.get_or_create_account_by_name(test_user.id, "New Account")

        assert account is not None
        assert account.user_id == test_user.id
        assert account.name == "New Account"
        assert account.id is not None
        assert account.created_at is not None

    def test_get_or_create_account_returns_existing(self, db_session: Session, test_user):
        """Test returning existing account when it already exists."""
        # Create a account first
        existing_account = AccountFactory.create(db_session, test_user.id, "Existing Account")
        existing_id = existing_account.id

        service = AccountService(db_session)
        account = service.get_or_create_account_by_name(test_user.id, "Existing Account")

        # Should return the same account
        assert account.id == existing_id
        assert account.name == "Existing Account"
        assert account.user_id == test_user.id

    def test_get_or_create_account_multiple_calls_same_result(self, db_session: Session, test_user):
        """Test that multiple calls with same parameters return the same account."""
        service = AccountService(db_session)

        account1 = service.get_or_create_account_by_name(test_user.id, "Test Account")
        account2 = service.get_or_create_account_by_name(test_user.id, "Test Account")

        # Should be the same account
        assert account1.id == account2.id
        assert account1.name == account2.name

    def test_get_or_create_account_different_users_different_accounts(
        self, db_session: Session, test_user, another_user
    ):
        """Test that same account name for different users creates separate accounts."""
        service = AccountService(db_session)

        account1 = service.get_or_create_account_by_name(test_user.id, "Shared Name")
        account2 = service.get_or_create_account_by_name(another_user.id, "Shared Name")

        # Should be different accounts
        assert account1.id != account2.id
        assert account1.user_id == test_user.id
        assert account2.user_id == another_user.id
        assert account1.name == account2.name == "Shared Name"

    def test_get_or_create_account_case_sensitive(self, db_session: Session, test_user):
        """Test that account names are case-sensitive."""
        service = AccountService(db_session)

        account1 = service.get_or_create_account_by_name(test_user.id, "MyAccount")
        account2 = service.get_or_create_account_by_name(test_user.id, "myaccount")

        # Should be different accounts (case-sensitive)
        assert account1.id != account2.id
        assert account1.name == "MyAccount"
        assert account2.name == "myaccount"

    def test_get_or_create_account_with_special_characters(self, db_session: Session, test_user):
        """Test creating/getting account with special characters in name."""
        service = AccountService(db_session)

        account_name = "Account-2024 (Test) #1"
        account = service.get_or_create_account_by_name(test_user.id, account_name)

        assert account.name == account_name
        assert account.user_id == test_user.id

        # Verify it's idempotent
        account2 = service.get_or_create_account_by_name(test_user.id, account_name)
        assert account.id == account2.id

    def test_get_or_create_account_doesnt_create_duplicates(self, db_session: Session, test_user):
        """Test that multiple parallel-like calls don't create duplicates."""
        service = AccountService(db_session)

        # Create account first time
        account1 = service.get_or_create_account_by_name(test_user.id, "Unique Account")

        # Get it multiple times
        for _ in range(5):
            account = service.get_or_create_account_by_name(test_user.id, "Unique Account")
            assert account.id == account1.id

        # Verify only one account was created
        all_accounts = service.get_accounts(test_user.id)
        matching_accounts = [p for p in all_accounts if p.name == "Unique Account"]
        assert len(matching_accounts) == 1


@pytest.mark.unit
class TestAccountServiceFactory:
    """Tests for the service factory function."""

    def test_get_account_service_returns_instance(self, db_session: Session):
        """Test that factory function returns AccountService instance."""
        service = get_account_service(db_session)

        assert isinstance(service, AccountService)
        assert service.db == db_session

    def test_get_account_service_creates_new_instances(self, db_session: Session):
        """Test that factory creates new instances each time."""
        service1 = get_account_service(db_session)
        service2 = get_account_service(db_session)

        # Should be different instances
        assert service1 is not service2
        # But should share the same db session
        assert service1.db is service2.db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
