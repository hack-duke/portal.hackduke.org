"""Issue and validate private, single-use portal account-setup links."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlparse

from sqlalchemy.orm import Session

from models.event_account_setup import EventAccountSetup


class InvalidAccountSetupToken(Exception):
    """Raised for missing, expired, consumed, or otherwise unusable tokens."""


def hash_account_setup_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_account_setup_link(
    session: Session,
    *,
    event_id,
    event_slug: str,
    registration_id,
    auth0_user_id: str,
    portal_url: str,
    ttl_seconds: int,
) -> str:
    """Rotate the registration's setup capability and return the raw link once."""

    base_url = portal_url.strip().rstrip("/")
    parsed_url = urlparse(base_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError("portal URL must be HTTPS")
    if not 300 <= ttl_seconds <= 604800:
        raise ValueError("account setup TTL must be between 5 minutes and 7 days")
    if not auth0_user_id:
        raise ValueError("Auth0 user ID is required")

    raw_token = secrets.token_urlsafe(48)
    token_digest = hash_account_setup_token(raw_token)
    now = datetime.now(timezone.utc)
    setup = (
        session.query(EventAccountSetup)
        .filter(
            EventAccountSetup.event_id == event_id,
            EventAccountSetup.registration_id == registration_id,
        )
        .with_for_update()
        .one_or_none()
    )
    if setup is None:
        setup = EventAccountSetup(
            event_id=event_id,
            registration_id=registration_id,
            auth0_user_id=auth0_user_id,
            token_digest=token_digest,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        session.add(setup)
    else:
        setup.auth0_user_id = auth0_user_id
        setup.token_digest = token_digest
        setup.expires_at = now + timedelta(seconds=ttl_seconds)
        setup.consumed_at = None
    session.flush()

    # A URL fragment is not sent in HTTP requests or Referer headers. The SPA
    # reads it locally and posts it in the encrypted request body.
    safe_token = quote(raw_token, safe="")
    return f"{base_url}/events/{event_slug}/account-setup#token={safe_token}"


def lock_valid_account_setup(
    session: Session,
    *,
    event_id,
    token: str,
) -> EventAccountSetup:
    if not token or len(token) > 256:
        raise InvalidAccountSetupToken

    setup = (
        session.query(EventAccountSetup)
        .filter(
            EventAccountSetup.event_id == event_id,
            EventAccountSetup.token_digest == hash_account_setup_token(token),
        )
        .with_for_update()
        .one_or_none()
    )
    now = datetime.now(timezone.utc)
    if setup is None or setup.consumed_at is not None or setup.expires_at <= now:
        raise InvalidAccountSetupToken
    return setup
