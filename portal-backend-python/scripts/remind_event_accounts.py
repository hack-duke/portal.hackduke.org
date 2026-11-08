"""Inventory or remind an exact allowlist of incomplete event accounts.

The safe default is a read-only preflight. Delivery requires an explicit event
confirmation, the exact preflight count, the exact preflight recipient-set
fingerprint, and a second send flag. Recipient addresses and one-time links are
never printed.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from dataclasses import dataclass
from email.utils import parseaddr
from pathlib import Path
from typing import Any, TextIO

from botocore.exceptions import ClientError

from services.account_setup import issue_account_setup_link
from services.auth0_onboarding import Auth0OnboardingClient, Auth0OnboardingSettings
from services.event_email_campaign import (
    OptionalEmailDeliveryAudit,
    SesEmailSender,
    SesSettings,
    render_campaign,
)
from scripts.onboard_event_auth0 import database_users


EVENT_SLUG = "duquantum-2026"
ORIGINAL_CAMPAIGN_KEY = "auth0-invitation"
ORIGINAL_EXISTING_CAMPAIGN_KEY = "auth0-invitation-existing"
REMINDER_CAMPAIGN_KEY = "auth0-invitation-reminder"
EXISTING_REMINDER_CAMPAIGN_KEY = "auth0-invitation-existing-reminder"
MAX_RECIPIENTS = 500


@dataclass(frozen=True)
class PlannedReminder:
    registration: Any
    auth0_user_id: str
    campaign_key: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recipient-file",
        required=True,
        help="UTF-8 file with one exact email per line; use - for standard input",
    )
    parser.add_argument("--send-reminders", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--confirm-event")
    parser.add_argument("--expected-recipient-count", type=int)
    parser.add_argument("--expected-setup-count", type=int)
    parser.add_argument("--expected-signin-count", type=int)
    parser.add_argument("--expected-recipient-sha256")
    return parser


def _validated_email(value: str, *, line_number: int) -> str:
    email = value.strip().casefold()
    parsed_name, parsed_email = parseaddr(email)
    if (
        not email
        or parsed_name
        or parsed_email != email
        or "@" not in email
        or len(email) > 320
    ):
        raise ValueError(f"recipient line {line_number} is not one plain email address")
    return email


def load_recipient_emails(source: TextIO) -> tuple[str, ...]:
    emails: list[str] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(source, start=1):
        if not raw_line.strip():
            continue
        email = _validated_email(raw_line, line_number=line_number)
        if email in seen:
            raise ValueError(
                f"recipient line {line_number} duplicates an earlier address"
            )
        seen.add(email)
        emails.append(email)
        if len(emails) > MAX_RECIPIENTS:
            raise ValueError(f"recipient file exceeds the {MAX_RECIPIENTS} address limit")
    if not emails:
        raise ValueError("recipient file is empty")
    return tuple(emails)


def recipient_set_sha256(emails: tuple[str, ...] | list[str]) -> str:
    canonical = "".join(f"{email.strip().casefold()}\n" for email in sorted(emails))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def reminder_campaign_for(registration: Any, auth0_user: dict[str, Any]) -> str | None:
    """Choose a reminder from portal claim state, not setup-token history.

    Consuming a setup capability proves that a password was chosen, but it does
    not connect the registration to the portal. Only the registration's user
    link/claim timestamp means the attendee completed the portal flow.
    """

    if registration.user_id is not None or registration.claimed_at is not None:
        return None
    if auth0_user.get("email_verified") is True:
        return EXISTING_REMINDER_CAMPAIGN_KEY
    return REMINDER_CAMPAIGN_KEY


def _client_error_code(error: ClientError) -> str:
    return str(error.response.get("Error", {}).get("Code", ""))


def _get_email_identity(client: Any, identity: str) -> dict[str, Any] | None:
    try:
        return dict(client.get_email_identity(EmailIdentity=identity))
    except ClientError as error:
        if _client_error_code(error) in {"NotFoundException", "NotFound"}:
            return None
        raise


def validate_ses_delivery_posture(client: Any, settings: SesSettings) -> dict[str, Any]:
    """Fail closed unless SES has aligned auth, suppression, and telemetry."""

    account = client.get_account()
    if account.get("SendingEnabled") is not True:
        raise RuntimeError("SES account sending is disabled")
    if account.get("ProductionAccessEnabled") is not True:
        raise RuntimeError("SES account is still in sandbox mode")
    suppressed_reasons = set(
        account.get("SuppressionAttributes", {}).get("SuppressedReasons", [])
    )
    if not {"BOUNCE", "COMPLAINT"}.issubset(suppressed_reasons):
        raise RuntimeError(
            "SES account-level bounce and complaint suppression must be enabled"
        )

    sender_domain = settings.sender.rpartition("@")[2].casefold()
    if not sender_domain:
        raise RuntimeError("SES sender domain is invalid")
    domain_identity = _get_email_identity(client, sender_domain)
    if (
        domain_identity is None
        or domain_identity.get("VerificationStatus") != "SUCCESS"
    ):
        raise RuntimeError("SES From domain is not verified")
    domain_dkim = domain_identity.get("DkimAttributes", {})
    if (
        domain_dkim.get("SigningEnabled") is not True
        or domain_dkim.get("Status") != "SUCCESS"
    ):
        raise RuntimeError("SES From domain DKIM is not healthy")

    # An explicitly verified address is more specific than its parent domain
    # and can override the domain's authentication settings. Validate the
    # effective identity so a legacy address identity cannot silently disable
    # the newly healthy domain DKIM configuration.
    sender_identity = _get_email_identity(client, settings.sender.casefold())
    effective_identity = sender_identity or domain_identity
    dkim = effective_identity.get("DkimAttributes", {})
    if dkim.get("SigningEnabled") is not True or dkim.get("Status") != "SUCCESS":
        raise RuntimeError("SES effective From identity DKIM is not healthy")

    mail_from = effective_identity.get("MailFromAttributes", {})
    mail_from_domain = str(mail_from.get("MailFromDomain") or "").casefold()
    if (
        mail_from.get("MailFromDomainStatus") != "SUCCESS"
        or not mail_from_domain.endswith(f".{sender_domain}")
    ):
        raise RuntimeError("SES custom MAIL FROM is not healthy or aligned")

    if not settings.configuration_set:
        raise RuntimeError("SES configuration set telemetry is required")
    configuration = client.get_configuration_set(
        ConfigurationSetName=settings.configuration_set
    )
    suppression_options = configuration.get("SuppressionOptions")
    if suppression_options is not None and not {
        "BOUNCE",
        "COMPLAINT",
    }.issubset(set(suppression_options.get("SuppressedReasons", []))):
        raise RuntimeError(
            "SES configuration set must not disable bounce or complaint suppression"
        )
    destinations = client.get_configuration_set_event_destinations(
        ConfigurationSetName=settings.configuration_set
    ).get("EventDestinations", [])
    enabled_events: set[str] = set()
    for destination in destinations:
        if destination.get("Enabled") is True:
            enabled_events.update(destination.get("MatchingEventTypes", []))
    if not {"DELIVERY", "BOUNCE", "COMPLAINT"}.issubset(enabled_events):
        raise RuntimeError(
            "SES configuration set must capture delivery, bounce, and complaint events"
        )

    return {
        "configuration_set": True,
        "enforcement_status": str(account.get("EnforcementStatus") or "unknown"),
    }


def suppression_reason(client: Any, email: str) -> str | None:
    try:
        response = client.get_suppressed_destination(EmailAddress=email)
    except ClientError as error:
        if _client_error_code(error) in {"NotFoundException", "NotFound"}:
            return None
        raise
    destination = response.get("SuppressedDestination", {})
    return str(destination.get("Reason") or "UNKNOWN")


def _open_recipient_file(path: str) -> tuple[TextIO, bool]:
    if path == "-":
        return sys.stdin, False
    return Path(path).open("r", encoding="utf-8"), True


def _send_requested(args: argparse.Namespace) -> bool:
    return bool(args.send_reminders or args.commit)


def _valid_send_confirmation(args: argparse.Namespace) -> bool:
    fingerprint = (args.expected_recipient_sha256 or "").strip().casefold()
    return bool(
        args.send_reminders
        and args.commit
        and args.confirm_event == EVENT_SLUG
        and args.expected_recipient_count is not None
        and args.expected_recipient_count >= 0
        and args.expected_setup_count is not None
        and args.expected_setup_count >= 0
        and args.expected_signin_count is not None
        and args.expected_signin_count >= 0
        and len(fingerprint) == 64
        and all(character in "0123456789abcdef" for character in fingerprint)
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if _send_requested(args) and not _valid_send_confirmation(args):
        print(
            "Refusing delivery: require --send-reminders --commit "
            f"--confirm-event {EVENT_SLUG}, the exact preflight count, and the "
            "exact setup/sign-in split plus preflight SHA-256"
        )
        return 2
    if not _send_requested(args) and any(
        value is not None
        for value in (
            args.confirm_event,
            args.expected_recipient_count,
            args.expected_setup_count,
            args.expected_signin_count,
            args.expected_recipient_sha256,
        )
    ):
        print("Confirmation inputs are only valid for a delivery run")
        return 2

    source, close_source = _open_recipient_file(args.recipient_file)
    try:
        try:
            requested_emails = load_recipient_emails(source)
        except ValueError as error:
            print(f"Invalid recipient file: {error}")
            return 2
    finally:
        if close_source:
            source.close()

    fingerprint = recipient_set_sha256(requested_emails)
    if _send_requested(args):
        if args.expected_recipient_count != len(requested_emails):
            print("Recipient count changed after preflight; no changes were made")
            return 2
        if args.expected_recipient_sha256.strip().casefold() != fingerprint:
            print("Recipient set changed after preflight; no changes were made")
            return 2

    from db import get_local_session
    from models import EmailDelivery, Event, EventRegistration

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
                EventRegistration.normalized_email.in_(requested_emails),
            )
            .all()
        )
        registration_by_email = {
            registration.normalized_email: registration
            for registration in registrations
        }

        auth_settings = Auth0OnboardingSettings.from_environment()
        mail_settings = SesSettings.from_environment()
        mailer = SesEmailSender(mail_settings)
        audit = OptionalEmailDeliveryAudit(session)
        if not audit.available:
            print("Refusing operation without database delivery auditing")
            return 2

        try:
            ses_posture = validate_ses_delivery_posture(mailer.client, mail_settings)
        except Exception:
            print("SES sender or suppression preflight failed; no changes were made")
            return 1

        plan: list[PlannedReminder] = []
        with Auth0OnboardingClient(auth_settings) as auth0:
            for email in requested_emails:
                registration = registration_by_email.get(email)
                if registration is None:
                    counts["unknown_registration"] += 1
                    continue
                if (
                    registration.admission_status != "accepted"
                    or registration.rsvp_status != "confirmed"
                ):
                    counts["ineligible"] += 1
                    continue

                try:
                    matches = database_users(
                        auth0.find_users_by_email(email),
                        auth_settings.database_connection,
                    )
                except Exception:
                    counts["auth0_inventory_failed"] += 1
                    continue
                if len(matches) != 1:
                    counts["missing_or_ambiguous_auth0"] += 1
                    continue

                auth0_user = matches[0]
                campaign_key = reminder_campaign_for(registration, auth0_user)
                if campaign_key is None:
                    counts["already_activated"] += 1
                    continue

                original_delivery = (
                    session.query(EmailDelivery)
                    .filter(
                        EmailDelivery.event_id == event.id,
                        EmailDelivery.registration_id == registration.id,
                        EmailDelivery.campaign_key.in_(
                            (
                                ORIGINAL_CAMPAIGN_KEY,
                                ORIGINAL_EXISTING_CAMPAIGN_KEY,
                            )
                        ),
                        EmailDelivery.status == "sent",
                    )
                    .first()
                )
                if original_delivery is None:
                    counts["original_delivery_not_sent"] += 1
                    continue
                if audit.already_sent(
                    event_id=event.id,
                    registration_id=registration.id,
                    campaign_key=campaign_key,
                ):
                    counts["reminder_already_recorded"] += 1
                    continue

                try:
                    reasons = {
                        suppression_reason(mailer.client, candidate)
                        for candidate in {
                            email,
                            registration.email,
                            original_delivery.recipient_email,
                        }
                    }
                    reasons.discard(None)
                except Exception:
                    counts["suppression_lookup_failed"] += 1
                    continue
                if reasons:
                    reason = sorted(reasons)[0]
                    counts[f"suppressed_{reason.casefold()}"] += 1
                    continue

                plan.append(
                    PlannedReminder(
                        registration=registration,
                        auth0_user_id=str(auth0_user["user_id"]),
                        campaign_key=campaign_key,
                    )
                )

        counts["planned"] = len(plan)
        counts["planned_setup"] = sum(
            item.campaign_key == REMINDER_CAMPAIGN_KEY for item in plan
        )
        counts["planned_signin"] = sum(
            item.campaign_key == EXISTING_REMINDER_CAMPAIGN_KEY for item in plan
        )
        blockers = sum(
            count
            for key, count in counts.items()
            if key
            not in {
                "planned",
                "planned_setup",
                "planned_signin",
                "sent",
                "failed",
            }
        )
        _print_preflight(
            requested_count=len(requested_emails),
            fingerprint=fingerprint,
            counts=counts,
            ses_posture=ses_posture,
        )
        if blockers:
            print("Recipient preflight has blockers; no changes were made")
            return 1
        if not _send_requested(args):
            print("Inventory only; no setup links or emails were created")
            return 0

        if len(plan) != args.expected_recipient_count:
            print("Eligible reminder count changed after preflight; no changes were made")
            return 2
        if counts["planned_setup"] != args.expected_setup_count:
            print("Setup-reminder count changed after preflight; no changes were made")
            return 2
        if counts["planned_signin"] != args.expected_signin_count:
            print("Sign-in-reminder count changed after preflight; no changes were made")
            return 2

        for item in plan:
            registration = item.registration
            try:
                if item.campaign_key == REMINDER_CAMPAIGN_KEY:
                    setup_url = issue_account_setup_link(
                        session,
                        event_id=event.id,
                        event_slug=event.slug,
                        registration_id=registration.id,
                        auth0_user_id=item.auth0_user_id,
                        portal_url=mail_settings.portal_url,
                        ttl_seconds=auth_settings.account_setup_ttl_seconds,
                    )
                    rendered = render_campaign(
                        item.campaign_key,
                        first_name=registration.first_name or "Attendee",
                        portal_url=mail_settings.portal_url,
                        account_setup_url=setup_url,
                        login_email=registration.email,
                    )
                else:
                    rendered = render_campaign(
                        item.campaign_key,
                        first_name=registration.first_name or "Attendee",
                        portal_url=mail_settings.portal_url,
                        login_email=registration.email,
                    )
                delivery = audit.queued(
                    event_id=event.id,
                    registration_id=registration.id,
                    campaign_key=item.campaign_key,
                    recipient=registration.email,
                )
                # Persist the rotated capability and idempotency row before SES.
                # A queued row is deliberately never retried automatically.
                session.commit()
                try:
                    message_id = mailer.send(
                        recipient=registration.email,
                        rendered=rendered,
                    )
                    audit.mark_sent(delivery, message_id)
                    session.commit()
                    counts["sent"] += 1
                except Exception as error:
                    audit.mark_failed(delivery, error)
                    session.commit()
                    counts["failed"] += 1
            except Exception:
                session.rollback()
                counts["failed"] += 1

        print(f"Reminder emails accepted by SES: {counts['sent']}")
        print(f"Reminder delivery failures: {counts['failed']}")
        return 1 if counts["failed"] else 0
    finally:
        session.close()


def _print_preflight(
    *,
    requested_count: int,
    fingerprint: str,
    counts: Counter[str],
    ses_posture: dict[str, Any],
) -> None:
    print(f"Exact recipients requested: {requested_count}")
    print(f"Recipient set SHA-256: {fingerprint}")
    print(f"Incomplete accounts eligible for reminder: {counts['planned']}")
    print(f"Fresh setup-link reminders planned: {counts['planned_setup']}")
    print(f"Existing-account sign-in reminders planned: {counts['planned_signin']}")
    print(f"Already activated accounts in list: {counts['already_activated']}")
    print(f"Unknown registrations in list: {counts['unknown_registration']}")
    print(f"Ineligible registrations in list: {counts['ineligible']}")
    print(
        "Missing or ambiguous Auth0 accounts in list: "
        f"{counts['missing_or_ambiguous_auth0']}"
    )
    print(f"Auth0 inventory failures: {counts['auth0_inventory_failed']}")
    print(
        "Recipients without a sent original invitation audit: "
        f"{counts['original_delivery_not_sent']}"
    )
    print(
        "Queued or sent reminder audits already present: "
        f"{counts['reminder_already_recorded']}"
    )
    print(f"Suppressed for bounce: {counts['suppressed_bounce']}")
    print(f"Suppressed for complaint: {counts['suppressed_complaint']}")
    print(f"Other suppressed recipients: {counts['suppressed_unknown']}")
    print(f"Suppression lookup failures: {counts['suppression_lookup_failed']}")
    print("SES From-domain DKIM: healthy")
    print(
        "SES configuration set attached: "
        f"{'yes' if ses_posture['configuration_set'] else 'no'}"
    )
    print(f"SES enforcement status: {ses_posture['enforcement_status']}")


if __name__ == "__main__":
    raise SystemExit(main())
