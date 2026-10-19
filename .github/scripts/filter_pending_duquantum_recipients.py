"""Refresh a protected reminder allowlist without printing recipient details."""

from __future__ import annotations

import sys


def pending_emails(requested, registrations, already_reminded):
    by_email = {row.normalized_email: row for row in registrations}
    if len(by_email) != len(registrations) or set(requested) != set(by_email):
        raise ValueError("Protected reminder recipients do not match unique registrations")
    return [
        email
        for email in requested
        if by_email[email].admission_status == "accepted"
        and by_email[email].rsvp_status == "confirmed"
        and by_email[email].user_id is None
        and by_email[email].claimed_at is None
        and email not in already_reminded
    ]


def main():
    from db import get_local_session
    from models import EmailDelivery, Event, EventRegistration
    from scripts.remind_event_accounts import (
        EVENT_SLUG,
        EXISTING_REMINDER_CAMPAIGN_KEY,
        REMINDER_CAMPAIGN_KEY,
        load_recipient_emails,
    )

    requested = load_recipient_emails(sys.stdin)
    session = get_local_session()
    try:
        event = session.query(Event).filter(Event.slug == EVENT_SLUG).one()
        registrations = session.query(EventRegistration).filter(
            EventRegistration.event_id == event.id,
            EventRegistration.normalized_email.in_(requested),
        ).all()
        deliveries = session.query(EmailDelivery).filter(
            EmailDelivery.event_id == event.id,
            EmailDelivery.campaign_key.in_((REMINDER_CAMPAIGN_KEY, EXISTING_REMINDER_CAMPAIGN_KEY)),
            EmailDelivery.status.in_(("queued", "sent")),
        ).all()
        reminded_ids = {delivery.registration_id for delivery in deliveries}
        previous = {row.normalized_email for row in registrations if row.id in reminded_ids}
        pending = pending_emails(requested, registrations, previous)
        print(f"Protected cohort size: {len(requested)}", file=sys.stderr)
        print(f"Current pending recipients: {len(pending)}", file=sys.stderr)
        print(f"Completed, ineligible, or previously reminded accounts excluded: {len(requested) - len(pending)}", file=sys.stderr)
        for email in pending:
            print(email)
    finally:
        session.close()


if __name__ == "__main__":
    main()
