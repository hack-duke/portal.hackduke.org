"""Auth0 Management API integration for user lookup."""
import os
from typing import Optional, Dict, Any, List
import httpx
from functools import lru_cache
from datetime import datetime, timedelta


class Auth0ManagementClient:
    """Client for Auth0 Management API operations."""

    def __init__(self):
        self.domain = os.environ.get("AUTH0_DOMAIN")
        self.client_id = os.environ.get("AUTH0_MGMT_CLIENT_ID")
        self.client_secret = os.environ.get("AUTH0_MGMT_CLIENT_SECRET")

        if not all([self.domain, self.client_id, self.client_secret]):
            raise ValueError(
                "AUTH0_DOMAIN, AUTH0_MGMT_CLIENT_ID, and AUTH0_MGMT_CLIENT_SECRET "
                "environment variables must be set"
            )

        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    def _get_management_token(self) -> str:
        """Get a valid Management API access token, refreshing if needed."""
        # Check if we have a valid cached token
        if self._token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return self._token

        # Request new token
        url = f"https://{self.domain}/oauth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": f"https://{self.domain}/api/v2/",
            "grant_type": "client_credentials"
        }

        with httpx.Client() as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        self._token = data["access_token"]
        # Token typically expires in 24 hours, but use the returned value
        expires_in = data.get("expires_in", 86400)
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        return self._token

    def search_users_by_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Search for users by email address.

        Args:
            email: The email address to search for

        Returns:
            List of user objects from Auth0
        """
        token = self._get_management_token()

        url = f"https://{self.domain}/api/v2/users-by-email"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"email": email.lower()}

        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by their Auth0 user ID.

        Args:
            user_id: The Auth0 user ID (e.g., "auth0|123456")

        Returns:
            User object from Auth0, or None if not found
        """
        token = self._get_management_token()

        url = f"https://{self.domain}/api/v2/users/{user_id}"
        headers = {"Authorization": f"Bearer {token}"}

        with httpx.Client() as client:
            response = client.get(url, headers=headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()


# Singleton instance
_client: Optional[Auth0ManagementClient] = None


def get_auth0_management_client() -> Auth0ManagementClient:
    """Get or create the Auth0 Management client singleton."""
    global _client
    if _client is None:
        _client = Auth0ManagementClient()
    return _client


def search_users_by_email(email: str) -> List[Dict[str, Any]]:
    """
    Search for Auth0 users by email.

    Args:
        email: The email address to search for

    Returns:
        List of matching users with their Auth0 info
    """
    client = get_auth0_management_client()
    return client.search_users_by_email(email)
