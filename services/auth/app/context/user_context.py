"""
User context management using contextvars for thread-safe access.

This module provides thread-safe context storage for the current authenticated user.
The user context is set during middleware authentication and can be accessed
throughout the application request lifecycle.
"""

from contextvars import ContextVar
from typing import Optional

from app.models.user import User

# Thread-safe context variable for storing the current user
_current_user: ContextVar[Optional[User]] = ContextVar("current_user", default=None)


def set_current_user_context(user: Optional[User]) -> None:
    """
    Set the current user in the context.

    This should be called by the authentication middleware after
    successfully authenticating the user.

    Args:
        user: User instance to store in context, or None to clear

    Example:
        ```python
        # In middleware
        user = User.from_jwt_payload(jwt_payload)
        set_current_user_context(user)
        ```
    """
    _current_user.set(user)


def get_current_user_context() -> Optional[User]:
    """
    Get the current user from the context.

    Returns:
        Current authenticated User instance, or None if not set

    Example:
        ```python
        # In any part of the application
        user = get_current_user_context()
        if user:
            print(f"Current user: {user.email}")
        ```
    """
    return _current_user.get()


def clear_current_user_context() -> None:
    """
    Clear the current user from the context.

    This can be used to explicitly clear the user context,
    though it typically clears automatically after the request completes.
    """
    _current_user.set(None)


def require_current_user_context() -> User:
    """
    Get the current user from the context, raising an exception if not set.

    Returns:
        Current authenticated User instance

    Raises:
        RuntimeError: If no user is set in the context

    Example:
        ```python
        # In a function that requires an authenticated user
        try:
            user = require_current_user_context()
            print(f"Processing request for {user.email}")
        except RuntimeError:
            # Handle unauthenticated request
            pass
        ```
    """
    user = _current_user.get()
    if user is None:
        raise RuntimeError(
            "No user found in context. Ensure the request is authenticated "
            "and the authentication middleware has been applied."
        )
    return user

