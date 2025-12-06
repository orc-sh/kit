"""
Subscription middleware for verifying subscription status and plan access.

This middleware provides dependency functions for FastAPI endpoints to check
subscription status and enforce plan-based access control.
"""

import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import get_current_user
from app.models.subscriptions import Subscription
from app.models.user import User
from app.services.subscription_service import get_subscription_service
from db.client import client

logger = logging.getLogger(__name__)

# Active subscription statuses that allow access
ACTIVE_STATUSES = ["active", "trialing", "in_trial"]


def verify_subscription_status(subscription: Subscription) -> bool:
    """
    Verify if a subscription has an active status.

    Args:
        subscription: Subscription instance to check

    Returns:
        True if subscription is active, False otherwise
    """
    if not subscription:
        return False
    return subscription.status.lower() in [s.lower() for s in ACTIVE_STATUSES]


def get_subscription_for_user(
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
) -> Optional[Subscription]:
    """
    Get the user's subscription(s).

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        First active subscription if found, otherwise first subscription, or None
    """
    subscription_service = get_subscription_service(db)
    subscriptions = subscription_service.get_subscriptions_by_user(user_id=user.id)

    if not subscriptions:
        return None

    # Prefer active subscription
    active_subscription = next((sub for sub in subscriptions if verify_subscription_status(sub)), None)
    if active_subscription:
        return active_subscription

    # Fall back to first subscription
    return subscriptions[0]


def get_all_subscriptions_for_user(
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
) -> List[Subscription]:
    """
    Get all subscriptions for the current user.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        List of Subscription instances
    """
    subscription_service = get_subscription_service(db)
    return subscription_service.get_subscriptions_by_user(user_id=user.id)


def require_active_subscription(
    subscription: Optional[Subscription] = Depends(get_subscription_for_user),
) -> Subscription:
    """
    Dependency function that requires an active subscription.

    Use this as a FastAPI dependency to ensure the user has an active subscription.

    Example:
        @router.get("/premium-feature")
        async def premium_feature(
            subscription: Subscription = Depends(require_active_subscription)
        ):
            # This endpoint requires an active subscription
            pass

    Args:
        subscription: Subscription from get_subscription_for_user dependency

    Returns:
        Subscription instance

    Raises:
        HTTPException: 403 if no active subscription found
    """
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No subscription found. Please create a account to get a subscription.",
        )

    if not verify_subscription_status(subscription):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Subscription is not active. Current status: {subscription.status}",
        )

    return subscription


def require_plan(required_plan_id: str):
    """
    Create a dependency function that requires a specific plan.

    Use this as a FastAPI dependency factory to ensure the user has a specific plan.

    Example:
        @router.get("/pro-feature")
        async def pro_feature(
            subscription: Subscription = Depends(require_plan("pro-plan"))
        ):
            # This endpoint requires pro plan
            pass

    Args:
        required_plan_id: Plan ID required to access the endpoint

    Returns:
        Dependency function that checks for the required plan
    """

    def _require_plan_dependency(
        subscription: Subscription = Depends(require_active_subscription),
    ) -> Subscription:
        """
        Dependency function that requires a specific plan.

        Args:
            subscription: Active subscription from require_active_subscription

        Returns:
            Subscription instance

        Raises:
            HTTPException: 403 if subscription doesn't have the required plan
        """
        if subscription.plan_id != required_plan_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_plan_id} plan. Current plan: {subscription.plan_id}",
            )
        return subscription

    return _require_plan_dependency


class SubscriptionMiddleware:
    """Middleware class for subscription verification (similar to AuthMiddleware pattern)."""

    @staticmethod
    async def verify_subscription(request: Request) -> Optional[Subscription]:
        """
        Verify subscription from request context.

        This method can be used as middleware or in request handlers.

        Args:
            request: FastAPI request object

        Returns:
            Subscription instance if found and active, None otherwise
        """
        # Get user from request state (set by auth middleware)
        user: Optional[User] = getattr(request.state, "user", None)
        if not user:
            return None

        # Get database session using dependency injection pattern
        # Note: This is a simplified version - in practice, use Depends(client) in route handlers
        try:
            from db.client import client

            db_gen = client()
            db = next(db_gen, None)
            if not db:
                return None

            try:
                subscription_service = get_subscription_service(db)
                subscriptions = subscription_service.get_subscriptions_by_user(user_id=user.id)

                if not subscriptions:
                    return None

                # Prefer active subscription
                active_subscription = next((sub for sub in subscriptions if verify_subscription_status(sub)), None)
                if active_subscription:
                    return active_subscription

                return subscriptions[0]
            finally:
                try:
                    next(db_gen, None)  # Complete the generator to trigger cleanup
                except StopIteration:
                    pass
        except Exception as e:
            logger.error(f"Error verifying subscription: {str(e)}")
            return None


# Singleton instance
_subscription_middleware_instance: Optional[SubscriptionMiddleware] = None


def get_subscription_middleware() -> SubscriptionMiddleware:
    """
    Get or create the singleton SubscriptionMiddleware instance.

    Returns:
        SubscriptionMiddleware instance
    """
    global _subscription_middleware_instance
    if _subscription_middleware_instance is None:
        _subscription_middleware_instance = SubscriptionMiddleware()
    return _subscription_middleware_instance
