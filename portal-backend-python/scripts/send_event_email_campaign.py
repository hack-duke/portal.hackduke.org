"""Preview, test, or send a DuQuantum operational SES email campaign.

Dry-run is the default. A production send requires an exact recipient-count
confirmation and refuses to run without a database delivery-audit model.
"""

from __future__ import annotations

import argparse
from collections import Counter

from services.event_email_campaign import (
    OptionalEmailDeliveryAudit,
    SesEmailSender,
    SesSettings,
    campaign_allows_registration,
    is_registration_eligible,
    render_campaign,
)


EVENT_SLUG = "duquantum-2026"
CAMPAIGNS = ("pass-ready", "event-reminder")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", choices=CAMPAIGNS, required=True)
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--confirm-event")
    parser.add_argument("--confirm-recipient-count", type=int)
    parser.add_argument(
        "--test-email",
        help="send one synthetic preview to this address; never uses attendee data",
    )
    parser.add_argument("--limit", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.limit is not None and args.limit < 1:
        print("--limit must be a positive integer")
        return 2

    settings = SesSettings.from_environment()
    if args.test_email:
        if not args.send or args.confirm_event != EVENT_SLUG:
            print(
                "A test send requires --send and "
                f"--confirm-event {EVENT_SLUG}"
            )
            return 2
        rendered = render_campaign(
            args.campaign,
            first_name="Test Attendee",
            portal_url=settings.portal_url,
        )
        try:
            SesEmailSender(settings).send(
                recipient=args.test_email, rendered=rendered
            )
        except Exception as exc:
            print(f"Test send failed ({type(exc).__name__})")
            return 1
        print("One synthetic test email sent")
        return 0

    from db import get_local_session
    from models import Event, EventRegistration

    session = get_local_session()
    try:
        event = session.query(Event).filter(Event.slug == EVENT_SLUG).one_or_none()
        if event is None:
            print("Event seed is missing; apply migrations first")
            return 1
        registrations = list(
            session.query(EventRegistration)
            .filter(EventRegistration.event_id == event.id)
            .order_by(EventRegistration.created_at, EventRegistration.id)
            .all()
        )
        # These built-in campaigns are operational, not marketing. The helper
        # remains explicit so a future marketing campaign cannot omit consent.
        eligible = [
            registration
            for registration in registrations
            if is_registration_eligible(registration, event)
            and campaign_allows_registration(registration, marketing=False)
        ]
        if args.limit:
            eligible = eligible[: args.limit]

        audit = OptionalEmailDeliveryAudit(session)
        pending = [
            registration
            for registration in eligible
            if not audit.already_sent(
                event_id=event.id,
                registration_id=registration.id,
                campaign_key=args.campaign,
            )
        ]

        print(f"Eligible recipients: {len(eligible)}")
        print(f"Previously sent or queued and skipped: {len(eligible) - len(pending)}")
        print(f"Pending recipients: {len(pending)}")
        print(f"Database delivery audit available: {'yes' if audit.available else 'no'}")
        if not args.send:
            print("Dry run only; no email was sent")
            return 0
        if args.confirm_event != EVENT_SLUG:
            print(f"Refusing send: pass --confirm-event {EVENT_SLUG}")
            return 2
        if args.confirm_recipient_count != len(pending):
            print("Refusing send: confirmed recipient count does not match pending count")
            return 2
        if not audit.available:
            print("Refusing production send without database delivery auditing")
            return 2

        sender = SesEmailSender(settings)
        counts: Counter[str] = Counter()
        for registration in pending:
            delivery = audit.queued(
                event_id=event.id,
                registration_id=registration.id,
                campaign_key=args.campaign,
                recipient=registration.email,
            )
            # Persist the idempotency claim before talking to SES. A queued row
            # left by a crash is intentionally not retried until an operator
            # reconciles it with SES delivery events.
            session.commit()
            try:
                rendered = render_campaign(
                    args.campaign,
                    first_name=registration.first_name or "Attendee",
                    portal_url=settings.portal_url,
                )
                message_id = sender.send(
                    recipient=registration.email, rendered=rendered
                )
                audit.mark_sent(delivery, message_id)
                session.commit()
                counts["sent"] += 1
            except Exception as exc:
                audit.mark_failed(delivery, exc)
                try:
                    session.commit()
                except Exception:
                    session.rollback()
                counts["failed"] += 1
        print(f"Sent: {counts['sent']}")
        print(f"Failed: {counts['failed']}")
        return 1 if counts["failed"] else 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
