"""
Account service for managing CRUD operations on accounts.
"""

import logging
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.accounts import Account

logger = logging.getLogger(__name__)


class AccountService:
    """Service class for account-related operations"""

    def __init__(self, db: Session):
        """
        Initialize the account service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_account(self, user_id: str, name: str, user=None) -> Account:
        """
        Create a new account for a user.
        Automatically creates a free tier subscription for the account.

        Args:
            user_id: ID of the user creating the account
            name: Name of the account
            user: User instance (optional, needed for subscription creation)

        Returns:
            Created Account instance
        """
        account = Account(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        # Automatically create a free tier subscription for the new account
        if user:
            try:
                from app.services.subscription_service import get_subscription_service

                subscription_service = get_subscription_service(self.db)

                # Get user email for subscription
                customer_email = user.email or f"{user_id}@example.com"
                customer_first_name = None
                customer_last_name = None

                # Try to extract name from user metadata
                if user.user_metadata:
                    if "name" in user.user_metadata:
                        name_parts = str(user.user_metadata["name"]).split(" ", 1)
                        customer_first_name = name_parts[0] if len(name_parts) > 0 else None
                        customer_last_name = name_parts[1] if len(name_parts) > 1 else None
                    elif "full_name" in user.user_metadata:
                        name_parts = str(user.user_metadata["full_name"]).split(" ", 1)
                        customer_first_name = name_parts[0] if len(name_parts) > 0 else None
                        customer_last_name = name_parts[1] if len(name_parts) > 1 else None

                # Create subscription with free plan
                subscription_service.create_subscription(
                    account_id=str(account.id),
                    plan_id="free-plan",
                    customer_email=customer_email,
                    customer_first_name=customer_first_name,
                    customer_last_name=customer_last_name,
                )
                logger.info(f"Created free tier subscription for account {account.id}")
            except ValueError as e:
                # Subscription already exists or account not found - log but don't fail
                logger.warning(f"Could not create subscription for account {account.id}: {str(e)}")
            except Exception as e:
                # Log other errors but don't fail account creation
                logger.error(f"Failed to create subscription for account {account.id}: {str(e)}")

        return account

    def get_account(self, account_id: str, user_id: str) -> Optional[Account]:
        """
        Get a specific account by ID for a user.

        Args:
            account_id: ID of the account to retrieve
            user_id: ID of the user (for authorization)

        Returns:
            Account instance if found and owned by user, None otherwise
        """
        return self.db.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()

    def get_accounts(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Account]:
        """
        Get all accounts for a user with pagination.

        Args:
            user_id: ID of the user
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of Account instances
        """
        return self.db.query(Account).filter(Account.user_id == user_id).offset(skip).limit(limit).all()

    def get_accounts_paginated(self, user_id: str, page: int = 1, page_size: int = 10) -> tuple[List[Account], dict]:
        """
        Get all accounts for a user with page-based pagination and metadata.

        Args:
            user_id: ID of the user
            page: Page number (1-indexed)
            page_size: Number of records per page

        Returns:
            Tuple of (List of Account instances, pagination metadata dict)
        """
        # Ensure page is at least 1
        page = max(1, page)
        page_size = max(1, min(page_size, 100))  # Cap at 100 items per page

        # Get total count
        total_entries = self.count_accounts(user_id)

        # Calculate total pages
        total_pages = (total_entries + page_size - 1) // page_size if total_entries > 0 else 1

        # Ensure page doesn't exceed total pages
        page = min(page, total_pages)

        # Calculate offset
        skip = (page - 1) * page_size

        # Get accounts for current page
        accounts = self.db.query(Account).filter(Account.user_id == user_id).offset(skip).limit(page_size).all()

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

        return accounts, pagination_metadata

    def update_account(self, account_id: str, user_id: str, name: str) -> Optional[Account]:
        """
        Update a account's name.

        Args:
            account_id: ID of the account to update
            user_id: ID of the user (for authorization)
            name: New name for the account

        Returns:
            Updated Account instance if found and owned by user, None otherwise
        """
        account = self.get_account(account_id, user_id)
        if not account:
            return None

        account.name = name  # type: ignore[assignment]
        self.db.commit()
        self.db.refresh(account)
        return account

    def delete_account(self, account_id: str, user_id: str) -> bool:
        """
        Delete a account.

        Args:
            account_id: ID of the account to delete
            user_id: ID of the user (for authorization)

        Returns:
            True if account was deleted, False if not found or not owned by user
        """
        account = self.get_account(account_id, user_id)
        if not account:
            return False

        self.db.delete(account)
        self.db.commit()
        return True

    def count_accounts(self, user_id: str) -> int:
        """
        Count the total number of accounts for a user.

        Args:
            user_id: ID of the user

        Returns:
            Total count of accounts
        """
        return self.db.query(Account).filter(Account.user_id == user_id).count()

    def get_or_create_account_by_name(
        self, user_id: str, account_name: str, user=None, default_plan_id: str = "free-plan"
    ) -> Account:
        """
        Get an existing account by name or create it if it doesn't exist.
        Automatically creates a free tier subscription for new accounts via create_account.

        Args:
            user_id: ID of the user
            account_name: Name of the account to find or create
            user: User instance (optional, needed for subscription creation)
            default_plan_id: Default plan ID for new subscriptions (default: "free-plan")
                Note: This parameter is kept for backward compatibility but subscriptions
                are now always created with "free-plan" via create_account.

        Returns:
            Account instance (either existing or newly created)
        """
        # Try to find existing account
        account = self.db.query(Account).filter(Account.user_id == user_id, Account.name == account_name).first()

        # If not found, create new account (which will automatically create subscription)
        if not account:
            account = self.create_account(user_id, account_name, user=user)

        return account


def get_account_service(db: Session) -> AccountService:
    """
    Factory function to create a AccountService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        AccountService instance
    """
    return AccountService(db)
