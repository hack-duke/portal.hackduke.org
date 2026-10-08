"""Inventory or explicitly provision Auth0 accounts for an event.

The safe default is claim-only inventory: no accounts, setup links, or emails are
created. Account creation requires all of ``--create-missing``, ``--commit``,
``--send-invitations``, and the exact event confirmation. Never pass attendee
data on the command line.
"""

from __future__ import annotations

import argparse
from collections import Counter

from services.auth0_onboarding import Auth0OnboardingClient, Auth0OnboardingSettings
from services.account_setup import issue_account_setup_link
from services.event_email_campaign import (
    OptionalEmailDeliveryAudit,
    SesEmailSender,
    SesSettings,
    render_campaign,
)


EVENT_SLUG = "duquantum-2026"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-missing", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--send-invitations", action="store_true")
    parser.add_argument("--confirm-event")
    parser.add_argument(
        "--limit",
        type=int,
        help="limit the number processed for a controlled staged batch",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    provisioning = args.create_missing or args.commit or args.send_invitations
    if provisioning and not (
        args.create_missing
        and args.commit
        and args.send_invitations
        and args.confirm_event == EVENT_SLUG
    ):
        print(
            "Refusing provisioning: require --create-missing --commit "
            f"--send-invitations --confirm-event {EVENT_SLUG}"
        )
        return 2
    if args.limit is not None and args.limit < 1:
        print("--limit must be a positive integer")
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
        query = (
            session.query(EventRegistration)
            .filter(
                EventRegistration.event_id == event.id,
                EventRegistration.admission_status == "accepted",
                EventRegistration.rsvp_status == "confirmed",
            )
            .order_by(EventRegistration.created_at, EventRegistration.id)
        )
        if args.limit:
            query = query.limit(args.limit)
        registrations = list(query.all())

        auth_settings = Auth0OnboardingSettings.from_environment()
        mailer = None
        mail_settings = None
        audit = OptionalEmailDeliveryAudit(session)
        if args.create_missing:
            if not audit.available:
                print("Refusing provisioning without database delivery auditing")
                return 2
            mail_settings = SesSettings.from_environment()
            mailer = SesEmailSender(mail_settings)

        with Auth0OnboardingClient(auth_settings) as auth0:
            for registration in registrations:
                try:
                    users = auth0.find_users_by_email(registration.normalized_email)
                    if len(users) == 1:
                        counts["existing"] += 1
                        existing = users[0]
                        provisioned_for = (existing.get("app_metadata") or {}).get(
                            "provisioned_for_event"
                        )
                        if (
                            args.create_missing
                            and provisioned_for == EVENT_SLUG
                            and not existing.get("email_verified", False)
                        ):
                            if audit.already_sent(
                                event_id=event.id,
                                registration_id=registration.id,
                                campaign_key="auth0-invitation",
                            ):
                                counts["invitation_already_recorded"] += 1
                                continue
                            account_setup_url = issue_account_setup_link(
                                session,
                                event_id=event.id,
                                event_slug=event.slug,
                                registration_id=registration.id,
                                auth0_user_id=str(existing["user_id"]),
                                portal_url=mail_settings.portal_url,
                                ttl_seconds=auth_settings.account_setup_ttl_seconds,
                            )
                            assert mailer is not None and mail_settings is not None
                            rendered = render_campaign(
                                "auth0-invitation",
                                first_name=registration.first_name or "Attendee",
                                portal_url=mail_settings.portal_url,
                                account_setup_url=account_setup_url,
                                login_email=registration.email,
                            )
                            delivery = audit.queued(
                                event_id=event.id,
                                registration_id=registration.id,
                                campaign_key="auth0-invitation",
                                recipient=registration.email,
                            )
                            session.commit()
                            try:
                                message_id = mailer.send(
                                    recipient=registration.email, rendered=rendered
                                )
                                audit.mark_sent(delivery, message_id)
                                session.commit()
                            except Exception as exc:
                                audit.mark_failed(delivery, exc)
                                session.commit()
                                raise
                            counts["existing_reinvited"] += 1
                        continue
                    if len(users) > 1:
                        counts["ambiguous"] += 1
                        continue
                    counts["missing"] += 1
                    if not args.create_missing:
                        continue

                    user_id = auth0.create_user(
                        email=registration.email,
                        first_name=registration.first_name or "",
                        last_name=registration.last_name or "",
                    )
                    if audit.already_sent(
                        event_id=event.id,
                        registration_id=registration.id,
                        campaign_key="auth0-invitation",
                    ):
                        counts["invitation_already_recorded"] += 1
                        continue
                    account_setup_url = issue_account_setup_link(
                        session,
                        event_id=event.id,
                        event_slug=event.slug,
                        registration_id=registration.id,
                        auth0_user_id=user_id,
                        portal_url=mail_settings.portal_url,
                        ttl_seconds=auth_settings.account_setup_ttl_seconds,
                    )
                    rendered = render_campaign(
                        "auth0-invitation",
                        first_name=registration.first_name or "Attendee",
                        portal_url=mail_settings.portal_url,
                        account_setup_url=account_setup_url,
                        login_email=registration.email,
                    )
                    assert mailer is not None
                    delivery = audit.queued(
                        event_id=event.id,
                        registration_id=registration.id,
                        campaign_key="auth0-invitation",
                        recipient=registration.email,
                    )
                    session.commit()
                    try:
                        message_id = mailer.send(
                            recipient=registration.email, rendered=rendered
                        )
                        audit.mark_sent(delivery, message_id)
                        session.commit()
                    except Exception as exc:
                        audit.mark_failed(delivery, exc)
                        session.commit()
                        raise
                    counts["created_and_invited"] += 1
                except Exception:
                    # Never stringify HTTP/SES exceptions; request payloads can
                    # contain attendee data or one-time invitation URLs.
                    session.rollback()
                    counts["failed"] += 1

        print(f"Eligible registrations checked: {len(registrations)}")
        print(f"Existing Auth0 accounts: {counts['existing']}")
        print(f"Missing Auth0 accounts: {counts['missing']}")
        print(f"Ambiguous Auth0 matches: {counts['ambiguous']}")
        print(f"Accounts created and invitations sent: {counts['created_and_invited']}")
        print(f"Previously provisioned accounts re-invited: {counts['existing_reinvited']}")
        print(f"Existing invitation audits skipped: {counts['invitation_already_recorded']}")
        print(f"Failures: {counts['failed']}")
        if not args.create_missing:
            print("Inventory only; no accounts, setup links, or emails were created")
        return 1 if counts["failed"] or counts["ambiguous"] else 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
