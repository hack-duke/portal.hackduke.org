"""Audit or resend a protected, explicit list of reported missing invitations.

Only request IDs and delivery metadata are logged, never addresses or links.
"""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone

from botocore.exceptions import ClientError


def choose_registration(addresses, registrations):
    matches = [row for row in registrations if row.normalized_email in addresses]
    if len(matches) != 1:
        return None, "missing_registration" if not matches else "ambiguous_registration"
    row = matches[0]
    if row.admission_status != "accepted" or row.rsvp_status != "confirmed":
        return None, "ineligible_registration"
    return row, None


def message_evidence(client, message_id):
    if not message_id:
        return {"insights": "no_provider_id"}
    try:
        time.sleep(1.05)
        result = client.get_message_insights(MessageId=message_id)
        return {"events": sorted({event["Type"] for item in result.get("Insights", []) for event in item.get("Events", [])})}
    except ClientError as error:
        return {"insights": error.response["Error"]["Code"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", choices=("inventory", "send"), required=True)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--expected-fingerprint")
    args = parser.parse_args()
    if not args.batch.isalnum() or len(args.batch) > 40:
        raise SystemExit("Invalid batch")
    from db import get_local_session
    from models import EmailDelivery, Event, EventRegistration, EventTeamMember
    from scripts.onboard_event_auth0 import database_users
    from scripts.remind_event_accounts import load_recipient_emails, suppression_reason, validate_ses_delivery_posture
    from services.account_setup import issue_account_setup_link
    from services.auth0_onboarding import Auth0OnboardingClient, Auth0OnboardingSettings
    from services.event_email_campaign import CAMPAIGN_TEMPLATE_VERSIONS, SesSettings, SesEmailSender, render_campaign
    from io import StringIO

    requests = json.load(sys.stdin)
    if not isinstance(requests, list) or not 1 <= len(requests) <= 20:
        raise SystemExit("Invalid request count")
    all_addresses = []
    for request in requests:
        request["emails"] = list(load_recipient_emails(StringIO("\n".join(request["emails"]))))
        all_addresses.extend(request["emails"])
    if len(set(all_addresses)) != len(all_addresses):
        raise SystemExit("Duplicate addresses across requests")

    session = get_local_session()
    try:
        event = session.query(Event).filter_by(slug="duquantum-2026").one()
        rows = session.query(EventRegistration).filter(EventRegistration.event_id == event.id, EventRegistration.normalized_email.in_(all_addresses)).all()
        settings = SesSettings.from_environment()
        mailer = SesEmailSender(settings)
        print("SES posture:", json.dumps(validate_ses_delivery_posture(mailer.client, settings)), flush=True)
        auth_settings = Auth0OnboardingSettings.from_environment()
        campaign = f"reported-invitation-{args.batch}"
        plan = []
        with Auth0OnboardingClient(auth_settings) as auth0:
            for index, request in enumerate(requests, 1):
                emails = request["emails"]
                registration, blocker = choose_registration(emails, rows)
                report = {"request": index, "blocker": blocker}
                report["matching_registrations"] = [{"address_index": emails.index(row.normalized_email), "admission_status": row.admission_status, "rsvp_status": row.rsvp_status, "source": row.source, "attendance_commitment": row.attendance_commitment, "photo_release_consent": row.photo_release_consent, "mlh_code_of_conduct_consent": row.mlh_code_of_conduct_consent, "mlh_privacy_policy_consent": row.mlh_privacy_policy_consent, "data_sharing_consent": row.data_sharing_consent, "marketing_opt_in": row.mlh_marketing_opt_in, "prior_message_count": len(row.email_deliveries)} for row in rows if row.normalized_email in emails]
                members = session.query(EventTeamMember).filter(EventTeamMember.event_id == event.id, EventTeamMember.normalized_email.in_(emails)).all()
                report["team_matches"] = [{"address_index": emails.index(member.normalized_email), "linked": member.registration_id is not None, "match_status": member.match_status} for member in members]
                if registration is None:
                    print("AUDIT", json.dumps(report), flush=True)
                    continue
                report["selected_address_index"] = emails.index(registration.normalized_email)
                report["portal_connected"] = registration.user_id is not None
                report["prior_messages"] = []
                deliveries = session.query(EmailDelivery).filter_by(event_id=event.id, registration_id=registration.id).order_by(EmailDelivery.created_at).all()
                for delivery in deliveries:
                    metadata = {"campaign": delivery.campaign_key, "status": delivery.status, "sent_at": str(delivery.sent_at), "recipient_matches_registered_address": delivery.recipient_email.strip().casefold() == registration.normalized_email}
                    if delivery.status == "sent":
                        metadata.update(message_evidence(mailer.client, delivery.provider_message_id))
                    report["prior_messages"].append(metadata)
                report["suppression"] = suppression_reason(mailer.client, registration.email)
                matches = database_users(auth0.find_users_by_email(registration.normalized_email), auth_settings.database_connection)
                report["auth0_matches"] = len(matches)
                report["auth0_verified"] = matches[0].get("email_verified") is True if len(matches) == 1 else None
                if report["suppression"]:
                    blocker = "suppressed"
                elif len(matches) > 1:
                    blocker = "ambiguous_auth0"
                elif not matches and registration.user_id is not None:
                    blocker = "linked_identity_missing"
                elif any(item.campaign_key == campaign and item.status in ("queued", "sent") for item in deliveries):
                    blocker = "batch_already_recorded"
                report["blocker"] = blocker
                if blocker is None:
                    action = "auth0-invitation-reminder" if not report["auth0_verified"] else "auth0-invitation-existing" if report["portal_connected"] else "auth0-invitation-existing-reminder"
                    report["planned_template"] = action
                    plan.append((index, registration, matches[0] if matches else None, action))
                print("AUDIT", json.dumps(report), flush=True)
            fingerprint = hashlib.sha256(json.dumps([(i, str(row.id), row.normalized_email, user.get("user_id") if user else None, action) for i, row, user, action in plan], separators=(",", ":")).encode()).hexdigest()
            print("PLAN", json.dumps({"recipients": len(plan), "fingerprint": fingerprint}), flush=True)
            if args.operation == "inventory":
                return 0
            if args.expected_count != len(plan) or args.expected_fingerprint != fingerprint:
                raise SystemExit("Recipient plan changed; no emails sent")
            failures = 0
            for index, row, user, action in plan:
                try:
                    user_id = user["user_id"] if user else auth0.create_user(email=row.normalized_email, first_name=row.first_name or "", last_name=row.last_name or "")
                    setup_url = None
                    if action == "auth0-invitation-reminder":
                        setup_url = issue_account_setup_link(session, event_id=event.id, event_slug=event.slug, registration_id=row.id, auth0_user_id=user_id, portal_url=settings.portal_url, ttl_seconds=auth_settings.account_setup_ttl_seconds)
                    rendered = render_campaign(action, first_name=row.first_name or "Attendee", portal_url=settings.portal_url, login_email=row.email, account_setup_url=setup_url)
                    delivery = EmailDelivery(event_id=event.id, registration_id=row.id, campaign_key=campaign, recipient_email=row.email, template_version=CAMPAIGN_TEMPLATE_VERSIONS[action], status="queued")
                    session.add(delivery)
                    session.commit()
                    try:
                        delivery.provider_message_id = mailer.send(recipient=row.email, rendered=rendered)
                        delivery.status = "sent"
                        delivery.sent_at = datetime.now(timezone.utc)
                        session.commit()
                        print("SENT", index, flush=True)
                    except Exception as error:
                        delivery.status = "failed"
                        delivery.error = type(error).__name__
                        session.commit()
                        raise
                except Exception as error:
                    session.rollback()
                    failures += 1
                    print("FAILED", index, type(error).__name__, flush=True)
            print("RESULT", json.dumps({"accepted_by_ses": len(plan) - failures, "failed": failures}), flush=True)
            return 1 if failures else 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
