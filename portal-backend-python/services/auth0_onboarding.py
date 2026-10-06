"""Conservative Auth0 account onboarding for event registrations.

Predictable passwords derived from names, phone numbers, or other personal data
are intentionally unsupported. New accounts receive an unguessable temporary
password and a single-use password-change ticket; the temporary password is
never returned, logged, or stored.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import httpx


@dataclass(frozen=True)
class Auth0OnboardingSettings:
    domain: str
    management_client_id: str
    management_client_secret: str
    database_connection: str
    invitation_return_url: str
    ticket_ttl_seconds: int = 604800

    @classmethod
    def from_environment(cls) -> "Auth0OnboardingSettings":
        settings = cls(
            domain=os.getenv("AUTH0_DOMAIN", "").strip().removeprefix("https://").rstrip("/"),
            management_client_id=os.getenv("AUTH0_MGMT_CLIENT_ID", "").strip(),
            management_client_secret=os.getenv("AUTH0_MGMT_CLIENT_SECRET", "").strip(),
            database_connection=os.getenv("AUTH0_DB_CONNECTION", "").strip(),
            invitation_return_url=os.getenv("AUTH0_INVITATION_RETURN_URL", "").strip(),
            ticket_ttl_seconds=int(os.getenv("AUTH0_INVITATION_TTL_SECONDS", "604800")),
        )
        if not all(
            (
                settings.domain,
                settings.management_client_id,
                settings.management_client_secret,
                settings.database_connection,
                settings.invitation_return_url,
            )
        ):
            raise ValueError("required Auth0 onboarding environment variables are missing")
        return_url = urlparse(settings.invitation_return_url)
        if return_url.scheme != "https" or not return_url.netloc:
            raise ValueError("AUTH0_INVITATION_RETURN_URL must be HTTPS")
        if not 300 <= settings.ticket_ttl_seconds <= 604800:
            raise ValueError("Auth0 invitation TTL must be between 5 minutes and 7 days")
        return settings


def generate_temporary_password() -> str:
    """Return a random Auth0-policy-friendly password with >256 bits entropy."""

    # token_urlsafe provides upper/lower case and digits. Appending punctuation
    # satisfies common Auth0 complexity policies without reducing entropy.
    return f"{secrets.token_urlsafe(48)}!aA7"


class Auth0OnboardingClient:
    def __init__(
        self,
        settings: Auth0OnboardingSettings,
        *,
        http_client: httpx.Client | None = None,
    ):
        self.settings = settings
        self.http = http_client or httpx.Client(timeout=20.0)
        self._owns_client = http_client is None
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    def close(self) -> None:
        if self._owns_client:
            self.http.close()

    def __enter__(self) -> "Auth0OnboardingClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    @property
    def base_url(self) -> str:
        return f"https://{self.settings.domain}"

    def _management_token(self) -> str:
        now = datetime.now(timezone.utc)
        if self._token and self._token_expires_at and now < self._token_expires_at:
            return self._token
        response = self.http.post(
            f"{self.base_url}/oauth/token",
            json={
                "client_id": self.settings.management_client_id,
                "client_secret": self.settings.management_client_secret,
                "audience": f"{self.base_url}/api/v2/",
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()
        payload = response.json()
        self._token = str(payload["access_token"])
        expires_in = max(60, int(payload.get("expires_in", 86400)) - 300)
        self._token_expires_at = now + timedelta(seconds=expires_in)
        return self._token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._management_token()}"}

    def find_users_by_email(self, email: str) -> list[dict[str, Any]]:
        response = self.http.get(
            f"{self.base_url}/api/v2/users-by-email",
            headers=self._headers(),
            params={"email": email.strip().casefold()},
        )
        response.raise_for_status()
        return list(response.json())

    def create_user(self, *, email: str, first_name: str, last_name: str) -> str:
        response = self.http.post(
            f"{self.base_url}/api/v2/users",
            headers=self._headers(),
            json={
                "connection": self.settings.database_connection,
                "email": email,
                "password": generate_temporary_password(),
                "email_verified": False,
                "verify_email": False,
                "given_name": first_name,
                "family_name": last_name,
                "name": " ".join(part for part in (first_name, last_name) if part),
                "app_metadata": {"provisioned_for_event": "duquantum-2026"},
            },
        )
        response.raise_for_status()
        return str(response.json()["user_id"])

    def create_password_ticket(self, *, user_id: str) -> str:
        response = self.http.post(
            f"{self.base_url}/api/v2/tickets/password-change",
            headers=self._headers(),
            json={
                "user_id": user_id,
                "result_url": self.settings.invitation_return_url,
                "ttl_sec": self.settings.ticket_ttl_seconds,
                # Clicking the emailed, single-use link proves control of the
                # mailbox before the registration can be claimed.
                "mark_email_as_verified": True,
                "includeEmailInRedirect": False,
            },
        )
        response.raise_for_status()
        ticket = str(response.json()["ticket"])
        parsed = urlparse(ticket)
        if parsed.scheme != "https" or not parsed.netloc:
            raise RuntimeError("Auth0 returned an invalid password ticket")
        return ticket
