"""Inventory or explicitly provision Auth0 accounts for an event.

The safe default is a read-only inventory. Account creation and invitation
delivery require every confirmation flag plus the exact preflight recipient
count. Attendee values and one-time links are never printed.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from typing import Any

from services.account_setup import issue_account_setup_link
from services.auth0_onboarding import Auth0OnboardingClient, Auth0OnboardingSettings
from services.event_email_campaign import (
    OptionalEmailDeliveryAudit,
    SesEmailSender,
    SesSettings,
    render_campaign,
)


EVENT_SLUG = "duquantum-2026"
CAMPAIGN_KEY = "auth0-invitation"


@dataclass(frozen=True)
class PlannedInvitation:
    registration: Any
    auth0_user_id: str | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-missing", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--send-invitations", action="store_true")
    parser.add_argument("--confirm-event")
    parser.add_argument(
        "--expected-recipient-count",
        type=int,
        help="exact preflight invitation count required for a send",
    )
    return parser


def database_users(
    users: list[dict[str, Any]], connection: str
) -> list[dict[str, Any]]:
    """Return only identities owned by the configured Auth0 database."""

    return [
        user
        for user in users
        if any(
            identity.get("connection") == connection
            for identity in user.get("identities", [])
        )
    ]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    provisioning = args.create_missing or args.commit or args.send_invitations
    if provisioning and not (
        args.create_missing
        and args.commit
        and args.send_invitations
        and args.confirm_event == EVENT_SLUG
        and args.expected_recipient_count is not None
        and args.expected_recipient_count >= 0
    ):
        print(
            "Refusing provisioning: require --create-missing --commit "
            f"--send-invitations --confirm-event {EVENT_SLUG} and a nonnegative "
            "--expected-recipient-count"
        )
        return 2
    if not provisioning and args.expected_recipient_count is not None:
        print("--expected-recipient-count is only valid for a confirmed send")
        return 2

    from db import get_local_session
    from models import Event, EventRegistration

    session = get_local_session()
    counts: Counter[str] = Counter()
    try:
        event = session.query(Event).filter(Event.slug == EVENT_SLUG).one_or_none()
        if event is None:
            print("Event seed is missing; apply migrations first")
            return 1
        registrations = list(
            session.query(EventRegistration)
            .filter(
                EventRegistration.event_id == event.id,
                EventRegistration.admission_status == "accepted",
                EventRegistration.rsvp_status == "confirmed",
            )
            .order_by(EventRegistration.created_at, EventRegistration.id)
            .all()
        )

        auth_settings = Auth0OnboardingSettings.from_environment()
        audit = OptionalEmailDeliveryAudit(session)
        if provisioning and not audit.available:
            print("Refusing provisioning without database delivery auditing")
            return 2

        plan: list[PlannedInvitation] = []
        with Auth0OnboardingClient(auth_settings) as auth0:
            # Complete all read-only Auth0 checks before creating an account,
            # rotating a capability, or asking SES to send anything.
            for registration in registrations:
                try:
                    matches = database_users(
                        auth0.find_users_by_email(registration.normalized_email),
                        auth_settings.database_connection,
                    )
                except Exception:
                    counts["inventory_failed"] += 1
                    continue

                if len(matches) > 1:
                    counts["ambiguous"] += 1
                    continue
                if matches and matches[0].get("email_verified") is True:
                    counts["existing_verified"] += 1
                    continue
                if audit.already_sent(
                    event_id=event.id,
                    registration_id=registration.id,
                    campaign_key=CAMPAIGN_KEY,
                ):
                    counts["invitation_already_recorded"] += 1
                    continue

                if matches:
                    counts["existing_needs_invitation"] += 1
                    plan.append(
                        PlannedInvitation(
                            registration=registration,
                            auth0_user_id=str(matches[0]["user_id"]),
                        )
                    )
                else:
                    counts["missing"] += 1
                    plan.append(
                        PlannedInvitation(
                            registration=registration,
                            auth0_user_id=None,
                        )
                    )

            counts["planned_recipients"] = len(plan)
            if counts["inventory_failed"] or counts["ambiguous"]:
                print("Inventory could not be reconciled; no changes were made")
                _print_summary(len(registrations), counts, provisioning=False)
                return 1

            if not provisioning:
                _print_summary(len(registrations), counts, provisioning=False)
                return 0

            assert args.expected_recipient_count is not None
            if len(plan) != args.expected_recipient_count:
                print("Recipient count changed after preflight; no changes were made")
                _print_summary(len(registrations), counts, provisioning=False)
                return 2

            mail_settings = SesSettings.from_environment()
            mailer = SesEmailSender(mail_settings)
            for item in plan:
                registration = item.registration
                try:
                    auth0_user_id = item.auth0_user_id
                    if auth0_user_id is None:
                        auth0_user_id = auth0.create_user(
                            email=registration.email,
                            first_name=registration.first_name or "",
                            last_name=registration.last_name or "",
                        )
                        account_result = "created_and_invited"
                    else:
                        account_result = "existing_reinvited"

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
                        CAMPAIGN_KEY,
                        first_name=registration.first_name or "Attendee",
                        portal_url=mail_settings.portal_url,
                        account_setup_url=setup_url,
                        login_email=registration.email,
                    )
                    delivery = audit.queued(
                        event_id=event.id,
                        registration_id=registration.id,
                        campaign_key=CAMPAIGN_KEY,
                        recipient=registration.email,
                    )
                    # Persist the rotated single-use setup capability and queued
                    # audit before delivery. A queued row is never auto-retried.
                    session.commit()
                    try:
                        message_id = mailer.send(
                            recipient=registration.email,
                            rendered=rendered,
                        )
                        audit.mark_sent(delivery, message_id)
                        session.commit()
                    except Exception as exc:
                        audit.mark_failed(delivery, exc)
                        session.commit()
                        raise
                    counts[account_result] += 1
                except Exception:
                    # Never stringify exceptions: request payloads may contain
                    # attendee data or one-time invitation capabilities.
                    session.rollback()
                    counts["failed"] += 1

        _print_summary(len(registrations), counts, provisioning=True)
        return 1 if counts["failed"] else 0
    finally:
        session.close()


def _print_summary(
    eligible_registration_count: int,
    counts: Counter[str],
    *,
    provisioning: bool,
) -> None:
    print(f"Eligible registrations checked: {eligible_registration_count}")
    print(f"Existing verified database accounts: {counts['existing_verified']}")
    print(
        "Existing database accounts needing invitation: "
        f"{counts['existing_needs_invitation']}"
    )
    print(f"Missing database accounts: {counts['missing']}")
    print(f"Ambiguous database matches: {counts['ambiguous']}")
    print(f"Inventory failures: {counts['inventory_failed']}")
    print(
        "Existing queued or sent invitation audits skipped: "
        f"{counts['invitation_already_recorded']}"
    )
    print(f"Planned invitation recipients: {counts['planned_recipients']}")
    print(f"Accounts created and invitations sent: {counts['created_and_invited']}")
    print(f"Existing accounts re-invited: {counts['existing_reinvited']}")
    print(f"Provisioning failures: {counts['failed']}")
    if not provisioning:
        print("Inventory only; no accounts, setup links, or emails were created")


if __name__ == "__main__":
    raise SystemExit(main())
