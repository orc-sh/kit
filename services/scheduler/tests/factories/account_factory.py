"""
Account-specific test data factories and helpers.
"""

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.accounts import Account


class AccountFactory:
    """Factory for creating Account test objects."""

    @staticmethod
    def create(
        db: Session,
        user_id: str,
        name: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> Account:
        """
        Create a account in the database.
        """
        account = Account(
            id=account_id or str(uuid.uuid4()),
            user_id=user_id,
            name=name or f"Test Account {uuid.uuid4().hex[:8]}",
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def create_batch(
        db: Session,
        user_id: str,
        count: int = 5,
        name_prefix: Optional[str] = None,
    ) -> list[Account]:
        """
        Create multiple accounts in the database.
        """
        accounts: list[Account] = []
        for i in range(count):
            name = f"{name_prefix} {i + 1}" if name_prefix else f"Test Account {i + 1}"
            account = AccountFactory.create(db=db, user_id=user_id, name=name)
            accounts.append(account)
        return accounts

    @staticmethod
    def build(
        user_id: str,
        name: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> Account:
        """
        Build a account object without saving to database.
        """
        return Account(
            id=account_id or str(uuid.uuid4()),
            user_id=user_id,
            name=name or f"Test Account {uuid.uuid4().hex[:8]}",
        )


def create_test_account_data(count: int = 1) -> list[dict]:
    """
    Create raw account data dictionaries (not model instances).
    """
    return [
        {
            "name": f"Test Account {i + 1}",
        }
        for i in range(count)
    ]


def create_account_update_data(name: Optional[str] = None) -> dict:
    """
    Create account update data dictionary.
    """
    return {"name": name or f"Updated Account {uuid.uuid4().hex[:8]}"}
