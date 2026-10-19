from io import StringIO
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError

from scripts.remind_event_accounts import (
    load_recipient_emails,
    main,
    recipient_set_sha256,
    reminder_campaign_for,
    suppression_reason,
    validate_ses_delivery_posture,
)
from services.event_email_campaign import (
    CAMPAIGN_TEMPLATE_VERSIONS,
    SesSettings,
    render_campaign,
)


class _HealthySesClient:
    def __init__(self, *, suppressed_reason=None):
        self.suppressed_reason = suppressed_reason
        self.configuration_sets = []

    def get_account(self):
        return {
            "SendingEnabled": True,
            "ProductionAccessEnabled": True,
            "EnforcementStatus": "HEALTHY",
            "SuppressionAttributes": {
                "SuppressedReasons": ["BOUNCE", "COMPLAINT"]
            },
        }

    def get_email_identity(self, *, EmailIdentity):
        if EmailIdentity == "hackduke.org":
            return {
                "VerificationStatus": "SUCCESS",
                "DkimAttributes": {"SigningEnabled": True, "Status": "SUCCESS"},
                "MailFromAttributes": {
                    "MailFromDomain": "bounce.hackduke.org",
                    "MailFromDomainStatus": "SUCCESS",
                },
            }
        assert EmailIdentity == "hackers@hackduke.org"
        raise ClientError(
            {"Error": {"Code": "NotFoundException", "Message": "not found"}},
            "GetEmailIdentity",
        )

    def get_configuration_set(self, *, ConfigurationSetName):
        self.configuration_sets.append(ConfigurationSetName)
        return {"ConfigurationSetName": ConfigurationSetName}

    def get_configuration_set_event_destinations(self, *, ConfigurationSetName):
        assert ConfigurationSetName == "duquantum-transactional"
        return {
            "EventDestinations": [
                {
                    "Name": "delivery-events",
                    "Enabled": True,
                    "MatchingEventTypes": ["DELIVERY", "BOUNCE", "COMPLAINT"],
                }
            ]
        }

    def get_suppressed_destination(self, *, EmailAddress):
        if self.suppressed_reason:
            return {
                "SuppressedDestination": {
                    "EmailAddress": EmailAddress,
                    "Reason": self.suppressed_reason,
                }
            }
        raise ClientError(
            {"Error": {"Code": "NotFoundException", "Message": "not found"}},
            "GetSuppressedDestination",
        )


def test_exact_recipient_file_normalizes_and_rejects_duplicates():
    recipients = load_recipient_emails(
        StringIO("First.Person@Example.edu\n\nsecond@example.org\n")
    )
    assert recipients == ("first.person@example.edu", "second@example.org")

    with pytest.raises(ValueError, match="duplicates"):
        load_recipient_emails(StringIO("person@example.org\nPERSON@example.org\n"))


def test_recipient_fingerprint_is_order_independent_and_exact():
    first = recipient_set_sha256(["b@example.org", "a@example.org"])
    second = recipient_set_sha256(["a@example.org", "b@example.org"])
    changed = recipient_set_sha256(["a@example.org", "c@example.org"])
    assert first == second
    assert first != changed
    assert len(first) == 64


def test_reminder_split_uses_portal_claim_state_not_consumed_setup_state():
    unconnected = SimpleNamespace(user_id=None, claimed_at=None)
    connected_by_user = SimpleNamespace(user_id="portal-user", claimed_at=None)
    connected_by_timestamp = SimpleNamespace(user_id=None, claimed_at="timestamp")

    assert reminder_campaign_for(
        unconnected, {"email_verified": False, "setup_consumed": False}
    ) == "auth0-invitation-reminder"
    assert reminder_campaign_for(
        unconnected, {"email_verified": True, "setup_consumed": True}
    ) == "auth0-invitation-existing-reminder"
    assert reminder_campaign_for(
        connected_by_user, {"email_verified": False}
    ) is None
    assert reminder_campaign_for(
        connected_by_timestamp, {"email_verified": True}
    ) is None


def test_send_refuses_count_or_fingerprint_drift_before_database_access(tmp_path):
    recipients = tmp_path / "recipients.txt"
    recipients.write_text("person@example.org\n", encoding="utf-8")

    assert (
        main(
            [
                "--recipient-file",
                str(recipients),
                "--send-reminders",
                "--commit",
                "--confirm-event",
                "duquantum-2026",
                "--expected-recipient-count",
                "2",
                "--expected-setup-count",
                "1",
                "--expected-signin-count",
                "0",
                "--expected-recipient-sha256",
                recipient_set_sha256(["person@example.org"]),
            ]
        )
        == 2
    )
    assert (
        main(
            [
                "--recipient-file",
                str(recipients),
                "--send-reminders",
                "--commit",
                "--confirm-event",
                "duquantum-2026",
                "--expected-recipient-count",
                "1",
                "--expected-setup-count",
                "1",
                "--expected-signin-count",
                "0",
                "--expected-recipient-sha256",
                "0" * 64,
            ]
        )
        == 2
    )


def test_ses_preflight_requires_aligned_dkim_and_suppression_protection():
    client = _HealthySesClient()
    result = validate_ses_delivery_posture(
        client,
        SesSettings(
            region="us-east-2",
            sender="hackers@hackduke.org",
            portal_url="https://portal.hackduke.org",
            configuration_set="duquantum-transactional",
        ),
    )
    assert result == {
        "configuration_set": True,
        "enforcement_status": "HEALTHY",
    }
    assert client.configuration_sets == ["duquantum-transactional"]

    unhealthy_client = _HealthySesClient()
    healthy_domain_identity = unhealthy_client.get_email_identity

    def identity_with_unhealthy_address(*, EmailIdentity):
        if EmailIdentity == "hackduke.org":
            return healthy_domain_identity(EmailIdentity=EmailIdentity)
        return {
            "VerificationStatus": "SUCCESS",
            "DkimAttributes": {"SigningEnabled": False, "Status": "NOT_STARTED"},
            "MailFromAttributes": {
                "MailFromDomain": "bounce.hackduke.org",
                "MailFromDomainStatus": "SUCCESS",
            },
        }

    unhealthy_client.get_email_identity = identity_with_unhealthy_address
    with pytest.raises(RuntimeError, match="DKIM"):
        validate_ses_delivery_posture(
            unhealthy_client,
            SesSettings(
                region="us-east-2",
                sender="hackers@hackduke.org",
                portal_url="https://portal.hackduke.org",
            ),
        )


def test_suppression_lookup_distinguishes_clear_and_blocked_addresses():
    assert suppression_reason(_HealthySesClient(), "person@example.org") is None
    assert (
        suppression_reason(
            _HealthySesClient(suppressed_reason="BOUNCE"),
            "person@example.org",
        )
        == "BOUNCE"
    )


def test_account_reminder_uses_fresh_single_use_link_and_shared_brand():
    setup_url = (
        "https://portal.example.org/events/duquantum-2026/"
        "account-setup#token=fresh-single-use-token"
    )
    rendered = render_campaign(
        "auth0-invitation-reminder",
        first_name="Attendee",
        portal_url="https://portal.example.org",
        account_setup_url=setup_url,
        login_email="attendee@example.org",
    )

    assert rendered.subject == "Reminder: claim your DuQuantum 2026 portal account"
    assert setup_url in rendered.html_body
    assert setup_url in rendered.text_body
    assert "replaces the one in your earlier invitation" in rendered.html_body
    assert "No temporary password is sent or stored" in rendered.html_body
    assert "logo-email.png" in rendered.html_body
    assert "Claim my portal account" in rendered.text_body
    assert CAMPAIGN_TEMPLATE_VERSIONS["auth0-invitation-reminder"].endswith("-v1")


def test_account_reminder_rejects_an_insecure_setup_link():
    with pytest.raises(ValueError, match="HTTPS"):
        render_campaign(
            "auth0-invitation-reminder",
            first_name="Attendee",
            portal_url="https://portal.example.org",
            account_setup_url="http://portal.example.org/account-setup#token=secret",
            login_email="attendee@example.org",
        )


def test_existing_account_reminder_directs_user_to_sign_in_not_reset():
    rendered = render_campaign(
        "auth0-invitation-existing-reminder",
        first_name="Attendee",
        portal_url="https://portal.example.org",
        login_email="attendee@example.org",
    )

    assert rendered.subject == (
        "Reminder: sign in to your DuQuantum 2026 participant portal"
    )
    assert "Sign in and claim my registration" in rendered.text_body
    assert "Forgot password" in rendered.text_body
    assert "do not create a second account" in rendered.html_body
    assert "logo-email.png" in rendered.html_body
    assert CAMPAIGN_TEMPLATE_VERSIONS[
        "auth0-invitation-existing-reminder"
    ].endswith("-v1")
