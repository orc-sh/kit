"""
Subscription client for communicating with Chargebee API.

This client handles all direct Chargebee API interactions, similar to how
AuthServiceClient handles communication with the auth service.
"""

import logging
from typing import Dict, Optional

import chargebee

from config.environment import get_chargebee_api_key, get_chargebee_site

logger = logging.getLogger(__name__)


class SubscriptionClient:
    """Client for communicating with Chargebee subscription API."""

    _instance = None
    _initialized = False

    def __init__(self):
        """Initialize the Chargebee client."""
        if not SubscriptionClient._initialized:
            try:
                api_key = get_chargebee_api_key()
                site = get_chargebee_site()
                chargebee.configure(api_key, site)
                SubscriptionClient._initialized = True
                logger.info("Chargebee client initialized successfully")
            except ValueError as e:
                logger.warning(f"Chargebee configuration not set: {str(e)}")
                # Don't raise - will fail when actually using Chargebee

    def create_customer(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Dict:
        """
        Create a customer in Chargebee.

        Args:
            email: Customer email address
            first_name: Customer first name (optional)
            last_name: Customer last name (optional)

        Returns:
            Chargebee customer object

        Raises:
            ValueError: If customer creation fails
        """
        try:
            customer_result = chargebee.Customer.create(
                {
                    "email": email,
                    "first_name": first_name or "",
                    "last_name": last_name or "",
                }
            )
            customer = customer_result.customer  # type: ignore[attr-defined]
            if not customer:
                raise ValueError("Failed to create customer in Chargebee")
            return customer
        except Exception as e:
            logger.error(f"Failed to create customer in Chargebee: {str(e)}")
            raise ValueError(f"Failed to create customer in Chargebee: {str(e)}")

    def create_subscription(self, plan_id: str, customer_id: str) -> Dict:
        """
        Create a subscription in Chargebee.

        Args:
            plan_id: Chargebee plan ID
            customer_id: Chargebee customer ID

        Returns:
            Chargebee subscription object

        Raises:
            ValueError: If subscription creation fails
        """
        try:
            subscription_result = chargebee.Subscription.create(
                {
                    "plan_id": plan_id,
                    "customer": {"id": customer_id},
                }
            )
            cb_subscription = subscription_result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Failed to create subscription in Chargebee")
            return cb_subscription
        except Exception as e:
            logger.error(f"Failed to create subscription in Chargebee: {str(e)}")
            raise ValueError(f"Failed to create subscription in Chargebee: {str(e)}")

    def update_subscription(self, chargebee_subscription_id: str, plan_id: Optional[str] = None) -> Dict:
        """
        Update a subscription in Chargebee.

        Args:
            chargebee_subscription_id: Chargebee subscription ID
            plan_id: New plan ID (optional)

        Returns:
            Updated Chargebee subscription object

        Raises:
            ValueError: If update fails
        """
        try:
            update_params = {}
            if plan_id:
                update_params["plan_id"] = plan_id

            if not update_params:
                raise ValueError("No update parameters provided")

            result = chargebee.Subscription.update(chargebee_subscription_id, update_params)
            cb_subscription = result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Failed to update subscription in Chargebee")
            return cb_subscription
        except Exception as e:
            logger.error(f"Failed to update subscription in Chargebee: {str(e)}")
            raise ValueError(f"Failed to update subscription in Chargebee: {str(e)}")

    def cancel_subscription(self, chargebee_subscription_id: str, cancel_reason: Optional[str] = None) -> Dict:
        """
        Cancel a subscription in Chargebee.

        Args:
            chargebee_subscription_id: Chargebee subscription ID
            cancel_reason: Reason for cancellation (optional)

        Returns:
            Cancelled Chargebee subscription object

        Raises:
            ValueError: If cancellation fails
        """
        try:
            cancel_params = {}
            if cancel_reason:
                cancel_params["cancel_reason"] = cancel_reason

            result = chargebee.Subscription.cancel(chargebee_subscription_id, cancel_params)
            cb_subscription = result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Failed to cancel subscription in Chargebee")
            return cb_subscription
        except Exception as e:
            logger.error(f"Failed to cancel subscription in Chargebee: {str(e)}")
            raise ValueError(f"Failed to cancel subscription in Chargebee: {str(e)}")

    def get_subscription(self, chargebee_subscription_id: str) -> Dict:
        """
        Retrieve a subscription from Chargebee.

        Args:
            chargebee_subscription_id: Chargebee subscription ID

        Returns:
            Chargebee subscription object

        Raises:
            ValueError: If subscription not found or retrieval fails
        """
        try:
            result = chargebee.Subscription.retrieve(chargebee_subscription_id)
            cb_subscription = result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Subscription not found in Chargebee")
            return cb_subscription
        except Exception as e:
            logger.error(f"Failed to retrieve subscription from Chargebee: {str(e)}")
            raise ValueError(f"Failed to retrieve subscription from Chargebee: {str(e)}")

    def sync_subscription(self, chargebee_subscription_id: str) -> Dict:
        """
        Sync subscription data from Chargebee.

        This is an alias for get_subscription for consistency.

        Args:
            chargebee_subscription_id: Chargebee subscription ID

        Returns:
            Chargebee subscription object
        """
        return self.get_subscription(chargebee_subscription_id)


# Singleton instance
_subscription_client_instance: Optional[SubscriptionClient] = None


def get_subscription_client() -> SubscriptionClient:
    """
    Get or create the singleton SubscriptionClient instance.

    Returns:
        SubscriptionClient instance
    """
    global _subscription_client_instance
    if _subscription_client_instance is None:
        _subscription_client_instance = SubscriptionClient()
    return _subscription_client_instance
