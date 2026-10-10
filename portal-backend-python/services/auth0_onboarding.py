"""Conservative Auth0 account onboarding for event registrations.

Predictable passwords derived from names, phone numbers, or other personal data
are intentionally unsupported. New accounts receive an unguessable internal
password and a single-use portal setup capability; the internal password is
never returned, logged, stored by the portal, or sent to the attendee.
"""

from __future__ import annotations

import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import quote, urlparse

import httpx


@dataclass(frozen=True)
class Auth0OnboardingSettings:
    domain: str
    management_client_id: str
    management_client_secret: str
    database_connection: str
    account_setup_ttl_seconds: int = 604800

    @classmethod
    def from_environment(cls) -> "Auth0OnboardingSettings":
        settings = cls(
            domain=os.getenv("AUTH0_DOMAIN", "")
            .strip()
            .removeprefix("https://")
            .rstrip("/"),
            management_client_id=os.getenv("AUTH0_MGMT_CLIENT_ID", "").strip(),
            management_client_secret=os.getenv("AUTH0_MGMT_CLIENT_SECRET", "").strip(),
            database_connection=os.getenv("AUTH0_DB_CONNECTION", "").strip(),
            account_setup_ttl_seconds=int(
                os.getenv(
                    "ACCOUNT_SETUP_TTL_SECONDS",
                    os.getenv("AUTH0_INVITATION_TTL_SECONDS", "604800"),
                )
            ),
        )
        if not all(
            (
                settings.domain,
                settings.management_client_id,
                settings.management_client_secret,
                settings.database_connection,
            )
        ):
            raise ValueError(
                "required Auth0 onboarding environment variables are missing"
            )
        if not 300 <= settings.account_setup_ttl_seconds <= 604800:
            raise ValueError("account setup TTL must be between 5 minutes and 7 days")
        return settings


def generate_temporary_password() -> str:
    """Return a random Auth0-policy-friendly password with >256 bits entropy."""

    # token_urlsafe provides upper/lower case and digits. Appending punctuation
    # satisfies common Auth0 complexity policies without reducing entropy.
    return f"{secrets.token_urlsafe(48)}!aA7"


class Auth0PasswordRejected(Exception):
    """Auth0 rejected a proposed password under the connection policy."""


class Auth0OnboardingClient:
    def __init__(
        self,
        settings: Auth0OnboardingSettings,
        *,
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
    ):
        self.settings = settings
        self.http = http_client or httpx.Client(timeout=20.0)
        self._owns_client = http_client is None
        self._sleep = sleep
        self._clock = clock
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

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Retry Auth0 rate limits without logging request or attendee data."""

        for attempt in range(5):
            response = self.http.request(method, url, **kwargs)
            if response.status_code != 429 or attempt == 4:
                return response

            retry_after = response.headers.get("retry-after")
            reset_at = response.headers.get("x-ratelimit-reset")
            try:
                delay = float(retry_after) if retry_after is not None else None
            except ValueError:
                delay = None
            if delay is None and reset_at is not None:
                try:
                    delay = float(reset_at) - self._clock()
                except ValueError:
                    delay = None
            if delay is None:
                delay = 0.5 * (2**attempt)
            self._sleep(max(0.1, min(delay + 0.1, 10.0)))

        raise AssertionError("unreachable")

    def _management_token(self) -> str:
        now = datetime.now(timezone.utc)
        if self._token and self._token_expires_at and now < self._token_expires_at:
            return self._token
        response = self._request(
            "POST",
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
        response = self._request(
            "GET",
            f"{self.base_url}/api/v2/users-by-email",
            headers=self._headers(),
            params={"email": email.strip().casefold()},
        )
        response.raise_for_status()
        return list(response.json())

    def create_user(self, *, email: str, first_name: str, last_name: str) -> str:
        response = self._request(
            "POST",
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

    def create_password_change_ticket(
        self,
        *,
        user_id: str,
        result_url: str,
        ttl_seconds: int = 604800,
    ) -> str:
        """Create a single-use Auth0 password ticket without logging its URL."""

        parsed_result = urlparse(result_url)
        if parsed_result.scheme != "https" or not parsed_result.netloc:
            raise ValueError("password ticket result URL must be HTTPS")
        if not 300 <= ttl_seconds <= 604800:
            raise ValueError("password ticket TTL must be between 5 minutes and 7 days")
        if not user_id:
            raise ValueError("Auth0 user ID is required")

        response = self._request(
            "POST",
            f"{self.base_url}/api/v2/tickets/password-change",
            headers=self._headers(),
            json={
                "user_id": user_id,
                "result_url": result_url,
                "ttl_sec": ttl_seconds,
                "mark_email_as_verified": True,
                "includeEmailInRedirect": False,
            },
        )
        response.raise_for_status()
        ticket = str(response.json().get("ticket") or "")
        parsed_ticket = urlparse(ticket)
        if parsed_ticket.scheme != "https" or not parsed_ticket.netloc:
            raise RuntimeError("Auth0 returned an invalid password ticket")
        return ticket

    def set_initial_password(self, *, user_id: str, password: str) -> None:
        """Set a database user's chosen password without logging either value."""

        password_response = self._request(
            "PATCH",
            f"{self.base_url}/api/v2/users/{quote(user_id, safe='')}",
            headers=self._headers(),
            json={
                "password": password,
                "connection": self.settings.database_connection,
            },
        )
        if password_response.status_code == 400:
            try:
                payload = password_response.json()
            except ValueError:
                payload = {}
            error_code = str(
                payload.get("code") or payload.get("errorCode") or ""
            ).casefold()
            message = str(payload.get("message") or "").casefold()
            password_error_codes = {
                "invalid_password",
                "password_dictionary_error",
                "password_no_user_info_error",
                "password_strength_error",
                "passwordhistoryerror",
            }
            if error_code in password_error_codes or any(
                marker in message
                for marker in (
                    "passwordstrengtherror",
                    "password is too weak",
                    "password has previously been used",
                )
            ):
                raise Auth0PasswordRejected
        password_response.raise_for_status()

        # Auth0 rejects password and email_verified in the same PATCH. The
        # setup capability was delivered to the registration mailbox, so mark
        # it verified only after the password update succeeds.
        verification_response = self._request(
            "PATCH",
            f"{self.base_url}/api/v2/users/{quote(user_id, safe='')}",
            headers=self._headers(),
            json={"email_verified": True},
        )
        verification_response.raise_for_status()
