"""Async Auth0 Management API integration for user lookup."""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

import httpx2


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

        self._token: str | None = None
        self._token_expires_at: datetime | None = None
        self._token_lock = asyncio.Lock()

    async def _get_management_token(self, client: httpx2.AsyncClient) -> str:
        """Get a valid Management API access token, refreshing if needed."""
        now = datetime.now(timezone.utc)
        if (
            self._token
            and self._token_expires_at
            and now < self._token_expires_at - timedelta(minutes=5)
        ):
            return self._token

        async with self._token_lock:
            now = datetime.now(timezone.utc)
            if (
                self._token
                and self._token_expires_at
                and now < self._token_expires_at - timedelta(minutes=5)
            ):
                return self._token

            response = await client.post(
                f"https://{self.domain}/oauth/token",
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "audience": f"https://{self.domain}/api/v2/",
                    "grant_type": "client_credentials",
                },
            )
            response.raise_for_status()
            data = response.json()
            self._token = str(data["access_token"])
            self._token_expires_at = now + timedelta(
                seconds=int(data.get("expires_in", 86400))
            )
            return self._token

    async def search_users_by_email(self, email: str) -> list[dict[str, Any]]:
        """Search for users by email address."""
        async with httpx2.AsyncClient(timeout=20.0) as client:
            token = await self._get_management_token(client)
            response = await client.get(
                f"https://{self.domain}/api/v2/users-by-email",
                headers={"Authorization": f"Bearer {token}"},
                params={"email": email.lower()},
            )
            response.raise_for_status()
            return list(response.json())

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Get a user by Auth0 ID, returning ``None`` when it does not exist."""
        async with httpx2.AsyncClient(timeout=20.0) as client:
            token = await self._get_management_token(client)
            response = await client.get(
                f"https://{self.domain}/api/v2/users/{quote(user_id, safe='')}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()


_client: Auth0ManagementClient | None = None


def get_auth0_management_client() -> Auth0ManagementClient:
    """Get or create the Auth0 Management client singleton."""
    global _client
    if _client is None:
        _client = Auth0ManagementClient()
    return _client


async def search_users_by_email(email: str) -> list[dict[str, Any]]:
    """Search for users by email."""
    client = get_auth0_management_client()
    return await client.search_users_by_email(email)
