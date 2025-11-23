"""
Authentication service client for communicating with the auth service.

This client can be used if the scheduler service needs to interact with
the auth service for operations beyond local JWT validation.
"""

from typing import Dict, Optional

import httpx

from config.environment import get_auth_service_url


class AuthServiceClient:
    """Client for communicating with the authentication service."""

    def __init__(self):
        """Initialize the auth service client."""
        self.base_url = get_auth_service_url()
        self.timeout = 10.0

    async def get_oauth_providers(self) -> list:
        """
        Get list of available OAuth providers from auth service.

        Returns:
            List of OAuth provider information
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/oauth/providers")
            response.raise_for_status()
            return response.json()

    async def get_oauth_url(self, provider: str) -> Dict[str, str]:
        """
        Get OAuth authorization URL from auth service.

        Args:
            provider: OAuth provider name (google, github)

        Returns:
            Dictionary with url and provider
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/oauth/{provider}")
            response.raise_for_status()
            return response.json()

    async def exchange_code_for_session(self, code: str) -> Dict:
        """
        Exchange OAuth code for session tokens.

        Args:
            code: OAuth authorization code

        Returns:
            Dictionary with access_token, refresh_token, and user info
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/oauth/callback",
                json={"code": code},
            )
            response.raise_for_status()
            return response.json()

    async def refresh_token(self, refresh_token: str) -> Dict:
        """
        Refresh an access token.

        Args:
            refresh_token: The refresh token

        Returns:
            Dictionary with new access_token and refresh_token
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Get user information from auth service.

        Args:
            access_token: User's access token

        Returns:
            User information dictionary or None if request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/auth/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return None

    async def health_check(self) -> Dict[str, str]:
        """
        Check if the auth service is healthy.

        Returns:
            Health status dictionary
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()


# Singleton instance
_auth_client_instance: Optional[AuthServiceClient] = None


def get_auth_client() -> AuthServiceClient:
    """Get or create the singleton AuthServiceClient instance."""
    global _auth_client_instance
    if _auth_client_instance is None:
        _auth_client_instance = AuthServiceClient()
    return _auth_client_instance
