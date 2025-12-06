"""
Account dependencies for FastAPI dependency injection.

These dependencies allow accessing the current account
from the context without needing to pass the request object.
"""

from typing import Optional

from fastapi import HTTPException, status

from app.context.account_context import get_current_account_context, require_current_account_context
from app.models.accounts import Account


def get_current_account_from_context() -> Optional[Account]:
    """
    FastAPI dependency to get the current account from context.

    Returns:
        Current Account instance, or None if not set

    Example:
        ```python
        from fastapi import APIRouter, Depends
        from app.dependencies.account import get_current_account_from_context
        from app.models.accounts import Account

        router = APIRouter()

        @router.get("/endpoint")
        async def my_endpoint(account: Account = Depends(get_current_account_from_context)):
            if account:
                return {"account_id": account.id, "name": account.name}
            return {"message": "No account set"}
        ```
    """
    return get_current_account_context()


def require_account_from_context() -> Account:
    """
    FastAPI dependency to get the current account from context, with required check.

    Returns:
        Current Account instance

    Raises:
        HTTPException: 500 if no account is in context

    Example:
        ```python
        from fastapi import APIRouter, Depends
        from app.dependencies.account import require_account_from_context
        from app.models.accounts import Account

        router = APIRouter()

        @router.get("/endpoint")
        async def my_endpoint(account: Account = Depends(require_account_from_context)):
            # This endpoint requires a account to be set
            return {"account_id": account.id, "name": account.name}
        ```
    """
    try:
        return require_current_account_context()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
