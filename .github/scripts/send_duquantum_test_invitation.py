"""Send one explicitly confirmed DuQuantum test account invitation.

This operator-only script is streamed into the running production backend by
the manual GitHub Actions workflow. It never prints the recipient, setup URL,
Auth0 identifier, or SES message identifier.
"""

from __future__ import annotations

import argparse
import secrets
from datetime import datetime, timezone
from email.utils import parseaddr

from db import get_local_session
from models import EmailDelivery, Event, EventRegistration
from services.account_setup import issue_account_setup_link
from services.auth0_onboarding import Auth0OnboardingClient, Auth0OnboardingSettings
from services.event_email_campaign import (
    CAMPAIGN_TEMPLATE_VERSIONS,
    SesEmailSender,
    SesSettings,
    render_campaign,
)


EVENT_SLUG = "duquantum-2026"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipient-email", required=True)
    parser.add_argument("--recipient-name", required=True)
    parser.add_argument("--confirm-event", required=True)
    return parser


def _validated_email(value: str) -> str:
    email = value.strip().casefold()
    parsed_name, parsed_email = parseaddr(email)
    if parsed_name or parsed_email != email or "@" not in email or len(email) > 320:
        raise ValueError("a single valid recipient email is required")
    return email


def _split_name(value: str) -> tuple[str, str]:
    name = " ".join(value.split())
    if not name or len(name) > 255:
        raise ValueError("a recipient name is required")
    first_name, separator, last_name = name.partition(" ")
    return first_name, last_name if separator else ""


def _database_user(users, connection: str):
    matches = [
        user
        for user in users
        if any(
            identity.get("connection") == connection
            for identity in user.get("identities", [])
        )
    ]
    if len(matches) > 1:
        raise RuntimeError("multiple Auth0 database accounts match the test recipient")
    return matches[0] if matches else None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.confirm_event != EVENT_SLUG:
        raise ValueError(f"confirmation must exactly match {EVENT_SLUG}")

    email = _validated_email(args.recipient_email)
    display_name = " ".join(args.recipient_name.split())
    first_name, last_name = _split_name(display_name)
    auth_settings = Auth0OnboardingSettings.from_environment()
    mail_settings = SesSettings.from_environment()
    session = get_local_session()

    try:
        event = session.query(Event).filter(Event.slug == EVENT_SLUG).one_or_none()
        if event is None:
            raise RuntimeError("the DuQuantum event seed is missing")

        registration = (
            session.query(EventRegistration)
            .filter(
                EventRegistration.event_id == event.id,
                EventRegistration.normalized_email == email,
            )
            .one_or_none()
        )
        if registration is None:
            registration = EventRegistration(
                event_id=event.id,
                email=email,
                normalized_email=email,
                first_name=first_name,
                last_name=last_name,
                admission_status="accepted",
                rsvp_status="confirmed",
                source="manual_test_invitation",
                source_data={"purpose": "operator_test_invitation"},
            )
            session.add(registration)
            session.flush()

        with Auth0OnboardingClient(auth_settings) as auth0:
            users = auth0.find_users_by_email(email)
            database_user = _database_user(users, auth_settings.database_connection)
            if database_user is None:
                auth0_user_id = auth0.create_user(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                )
                account_result = "created"
            else:
                auth0_user_id = str(database_user["user_id"])
                account_result = "reused"

        setup_url = issue_account_setup_link(
            session,
            event_id=event.id,
            event_slug=event.slug,
            registration_id=registration.id,
            auth0_user_id=auth0_user_id,
            portal_url=mail_settings.portal_url,
            ttl_seconds=auth_settings.account_setup_ttl_seconds,
        )
        rendered = render_campaign(
            "auth0-invitation",
            first_name=display_name,
            portal_url=mail_settings.portal_url,
            account_setup_url=setup_url,
            login_email=email,
        )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        campaign_key = f"auth0-invitation-test-{timestamp}-{secrets.token_hex(3)}"
        delivery = EmailDelivery(
            event_id=event.id,
            registration_id=registration.id,
            campaign_key=campaign_key,
            recipient_email=email,
            template_version=CAMPAIGN_TEMPLATE_VERSIONS["auth0-invitation"],
            status="queued",
        )
        session.add(delivery)
        # Persist both the rotated capability and the idempotency record before
        # asking SES to accept the message.
        session.commit()

        try:
            message_id = SesEmailSender(mail_settings).send(
                recipient=email,
                rendered=rendered,
            )
            delivery.status = "sent"
            delivery.provider_message_id = message_id
            delivery.sent_at = datetime.now(timezone.utc)
            session.commit()
        except Exception as exc:
            delivery.status = "failed"
            delivery.error = type(exc).__name__
            session.commit()
            raise

        print("One DuQuantum test invitation was accepted by SES")
        print(f"Auth0 database account: {account_result}")
        print("A fresh seven-day single-use account setup link was issued")
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
