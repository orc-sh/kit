"""
User controller for managing user account operations.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services.user_service import get_user_service
from db.client import client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete the current user's account and all associated data.

    This endpoint:
    - Cancels all subscriptions in Chargebee
    - Deletes all accounts (which cascades to delete jobs, webhooks, urls, subscriptions, etc.)
    - Permanently removes all user data

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        No content on success

    Raises:
        HTTPException: 401 if not authenticated, 500 if deletion fails
    """
    try:
        user_service = get_user_service(db)
        deleted = user_service.delete_user_account(user_id=user.id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user account",
            )

        logger.info(f"Account deleted successfully for user {user.id}")
        return None

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error deleting account for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}",
        )
