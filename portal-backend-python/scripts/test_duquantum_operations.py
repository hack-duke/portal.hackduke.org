import csv
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from scripts.import_event_registrations import (
    CONSENT_HEADER_PREFIXES,
    HEADER_AGE,
    HEADER_COUNTRY,
    HEADER_DEGREE,
    HEADER_EMAIL,
    HEADER_FIRST_NAME,
    HEADER_LAST_NAME,
    HEADER_PHONE,
    HEADER_TIMESTAMP,
    HEADER_UNIVERSITY,
    normalize_email,
    parse_csv,
)
from services.auth0_onboarding import (
    Auth0OnboardingClient,
    Auth0OnboardingSettings,
    generate_temporary_password,
)
from services.event_email_campaign import render_campaign
from services.event_email_campaign import (
    OptionalEmailDeliveryAudit,
    campaign_allows_registration,
    is_registration_eligible,
)
from scripts.onboard_event_auth0 import main as auth0_onboarding_main


def _write_synthetic_csv(path: Path) -> None:
    headers = [
        HEADER_TIMESTAMP,
        HEADER_FIRST_NAME,
        HEADER_LAST_NAME,
        HEADER_EMAIL,
        HEADER_PHONE,
        HEADER_AGE,
        HEADER_UNIVERSITY,
        HEADER_DEGREE,
        HEADER_COUNTRY,
        *CONSENT_HEADER_PREFIXES.values(),
    ]
    base = {
        HEADER_FIRST_NAME: "First",
        HEADER_LAST_NAME: "Last",
        HEADER_EMAIL: "Person@Example.edu ",
        HEADER_PHONE: "+1 555 0100",
        HEADER_AGE: "20",
        HEADER_UNIVERSITY: "Example University",
        HEADER_DEGREE: "Undergraduate",
        HEADER_COUNTRY: "United States",
        **{header: "I agree" for header in CONSENT_HEADER_PREFIXES.values()},
    }
    marketing_header = CONSENT_HEADER_PREFIXES["mlh_marketing_opt_in"]
    older = {**base, HEADER_TIMESTAMP: "10/01/2026 09:00:00"}
    newer = {
        **base,
        HEADER_TIMESTAMP: "10/02/2026 09:00:00",
        HEADER_FIRST_NAME: "Updated",
        marketing_header: "I do not agree",
    }
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=headers)
        writer.writeheader()
        writer.writerows([older, newer])


def test_csv_import_keeps_latest_and_preserves_marketing_opt_out(tmp_path):
    source = tmp_path / "responses.csv"
    _write_synthetic_csv(source)

    result = parse_csv(source)

    assert result.raw_rows == 2
    assert result.duplicate_groups == 1
    assert result.superseded_rows == 1
    assert result.invalid_rows == 0
    assert len(result.registrations) == 1
    registration = result.registrations[0]
    assert registration.first_name == "Updated"
    assert registration.mlh_marketing_opt_in is False
    assert registration.source_data["consents"]["mlh_marketing_opt_in"] is False


def test_email_normalization_does_not_rewrite_provider_specific_addressing():
    assert normalize_email(" Name+tag@Example.COM ") == "name+tag@example.com"


def test_generated_password_is_random_and_complex():
    first = generate_temporary_password()
    second = generate_temporary_password()
    assert first != second
    assert len(first) >= 64
    assert any(character.isupper() for character in first)
    assert any(character.islower() for character in first)
    assert any(character.isdigit() for character in first)
    assert "!" in first


def test_auth0_client_retries_rate_limits_without_exposing_lookup_data():
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path == "/oauth/token":
            return httpx.Response(
                200,
                request=request,
                json={"access_token": "management-token", "expires_in": 3600},
            )
        if len([item for item in requests if item.url.path.endswith("users-by-email")]) == 1:
            return httpx.Response(
                429,
                request=request,
                headers={"retry-after": "0"},
            )
        return httpx.Response(200, request=request, json=[])

    settings = Auth0OnboardingSettings(
        domain="tenant.example.org",
        management_client_id="client-id",
        management_client_secret="client-secret",
        database_connection="Username-Password-Authentication",
        invitation_return_url="https://portal.example.org/events/test",
    )
    sleeps = []
    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        with Auth0OnboardingClient(
            settings,
            http_client=http_client,
            sleep=sleeps.append,
        ) as client:
            assert client.find_users_by_email("attendee@example.org") == []

    lookup_requests = [
        request for request in requests if request.url.path.endswith("users-by-email")
    ]
    assert len(lookup_requests) == 2
    assert sleeps == [0.1]


def test_campaign_escapes_display_name_and_does_not_embed_a_pass():
    rendered = render_campaign(
        "pass-ready",
        first_name="<script>alert(1)</script>",
        portal_url="https://portal.example.org",
    )
    assert "<script>" not in rendered.html_body
    assert "&lt;script&gt;" in rendered.html_body
    assert "https://portal.example.org" in rendered.text_body
    assert "QR" not in rendered.text_body


def test_invitation_requires_secure_ticket_url():
    with pytest.raises(ValueError):
        render_campaign(
            "auth0-invitation",
            first_name="Test",
            portal_url="https://portal.example.org",
            password_ticket_url="http://example.org/ticket",
        )


def test_auth0_provisioning_requires_all_explicit_safety_flags():
    # The gate runs before database, Auth0, or SES objects are constructed.
    assert auth0_onboarding_main(["--create-missing"]) == 2
    assert auth0_onboarding_main(["--commit"]) == 2


def test_campaign_eligibility_keeps_marketing_consent_separate():
    event = SimpleNamespace(pass_eligibility="confirmed")
    registration = SimpleNamespace(
        admission_status="accepted",
        rsvp_status="confirmed",
        mlh_marketing_opt_in=False,
    )
    assert is_registration_eligible(registration, event)
    assert campaign_allows_registration(registration, marketing=False)
    assert not campaign_allows_registration(registration, marketing=True)


class _FakeField:
    def __eq__(self, _other):
        return self

    def in_(self, _values):
        return self


class _FakeDelivery:
    event_id = _FakeField()
    registration_id = _FakeField()
    campaign_key = _FakeField()
    status = _FakeField()

    def __init__(self, **values):
        for key, value in values.items():
            setattr(self, key, value)


class _FakeQuery:
    def __init__(self, row):
        self.row = row

    def filter(self, *_conditions):
        return self

    def one_or_none(self):
        return self.row

    def first(self):
        return self.row


class _FakeSession:
    def __init__(self, row=None):
        self.row = row
        self.added = []

    def query(self, _model):
        return _FakeQuery(self.row)

    def add(self, row):
        self.added.append(row)

    def flush(self):
        pass


def test_email_audit_reuses_failed_row_and_blocks_uncertain_queued_row():
    failed = _FakeDelivery(
        event_id="event",
        registration_id="registration",
        campaign_key="pass-ready",
        recipient_email="old@example.org",
        template_version="old",
        status="failed",
        provider_message_id="old-message",
        error="OldError",
        sent_at="old-time",
    )
    session = _FakeSession(failed)
    audit = OptionalEmailDeliveryAudit(session)
    audit.model = _FakeDelivery

    reused = audit.queued(
        event_id="event",
        registration_id="registration",
        campaign_key="pass-ready",
        recipient="new@example.org",
    )

    assert reused is failed
    assert reused.status == "queued"
    assert reused.provider_message_id is None
    assert reused.error is None
    assert reused.sent_at is None
    assert not session.added
    assert audit.already_sent(
        event_id="event",
        registration_id="registration",
        campaign_key="pass-ready",
    )
