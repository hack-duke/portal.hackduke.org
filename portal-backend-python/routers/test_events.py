from uuid import uuid4
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from db import get_db
from models.event import Event
from models.event_registration import EventRegistration
from models.event_push_subscription import EventPushSubscription
from models.event_account_setup import EventAccountSetup
from models.user import User
from models.user_role import RoleEnum, UserRole
from routers.events import auth, router
from services.account_setup import issue_account_setup_link
from services.auth0_onboarding import Auth0PasswordRejected


app = FastAPI()
app.include_router(prefix="/events", router=router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_dependency_overrides(test_session):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = lambda: (yield test_session)
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def event(test_session):
    item = Event(
        slug=f"duquantum-test-{uuid4()}",
        name="DuQuantum Test",
        state="active",
        pass_eligibility="confirmed",
    )
    test_session.add(item)
    test_session.flush()
    return item


@pytest.fixture
def registration(test_session, event):
    item = EventRegistration(
        event_id=event.id,
        email="Attendee@Example.com",
        normalized_email="attendee@example.com",
        first_name="Quantum",
        last_name="Hacker",
        phone="+15555550100",
        age=20,
        university="Duke University",
        degree_program="Undergraduate",
        country="United States",
        attendance_commitment=True,
        photo_release_consent=True,
        mlh_code_of_conduct_consent=True,
        data_sharing_consent=True,
        mlh_marketing_opt_in=False,
        admission_status="accepted",
        rsvp_status="confirmed",
        source="google_forms_csv",
        source_data={"form_response": {"example": "retained"}},
    )
    test_session.add(item)
    test_session.flush()
    return item


def set_token(payload):
    app.dependency_overrides[auth.verify] = lambda: payload


def claim(event):
    set_token(
        {
            "sub": "auth0|attendee",
            "https://portal.hackduke.org/email": "ATTENDEE@example.com",
            "https://portal.hackduke.org/email_verified": True,
        }
    )
    return client.post(f"/events/{event.slug}/claim")


def _issue_setup_token(test_session, event, registration):
    setup_url = issue_account_setup_link(
        test_session,
        event_id=event.id,
        event_slug=event.slug,
        registration_id=registration.id,
        auth0_user_id="auth0|attendee",
        portal_url="https://portal.example.org",
        ttl_seconds=3600,
    )
    # The real onboarding command commits the setup capability before SES
    # delivery; the API request always begins in a separate transaction.
    test_session.commit()
    token = parse_qs(urlparse(setup_url).fragment)["token"][0]
    return setup_url, token


def test_claim_requires_verified_token_email(event, registration):
    set_token(
        {
            "sub": "auth0|attendee",
            "email": "attendee@example.com",
            "email_verified": False,
        }
    )

    response = client.post(f"/events/{event.slug}/claim")

    assert response.status_code == 403
    assert registration.user_id is None


def test_account_setup_sets_password_marks_email_verified_and_is_single_use(
    event, registration, test_session, monkeypatch
):
    setup_url, token = _issue_setup_token(test_session, event, registration)
    setup = (
        test_session.query(EventAccountSetup)
        .filter(EventAccountSetup.registration_id == registration.id)
        .one()
    )

    assert token not in setup.token_digest
    assert setup_url.startswith(
        f"https://portal.example.org/events/{event.slug}/account-setup#token="
    )

    calls = []

    class FakeAuth0Client:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def set_initial_password(self, *, user_id, password):
            calls.append((user_id, password))

    monkeypatch.setattr(
        "routers.events.get_auth0_onboarding_client",
        lambda: FakeAuth0Client(),
    )
    response = client.post(
        f"/events/{event.slug}/account-setup",
        json={"token": token, "password": "A-strong-private-password-2026"},
    )

    assert response.status_code == 200
    assert response.json()["login_email"] == registration.email
    assert calls == [("auth0|attendee", "A-strong-private-password-2026")]
    test_session.refresh(setup)
    assert setup.consumed_at is not None

    repeated = client.post(
        f"/events/{event.slug}/account-setup",
        json={"token": token, "password": "Another-strong-password-2026"},
    )
    assert repeated.status_code == 410
    assert len(calls) == 1


def test_account_setup_keeps_token_available_when_auth0_rejects_password(
    event, registration, test_session, monkeypatch
):
    _, token = _issue_setup_token(test_session, event, registration)
    setup = (
        test_session.query(EventAccountSetup)
        .filter(EventAccountSetup.registration_id == registration.id)
        .one()
    )

    class RejectingAuth0Client:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def set_initial_password(self, **_kwargs):
            raise Auth0PasswordRejected

    monkeypatch.setattr(
        "routers.events.get_auth0_onboarding_client",
        lambda: RejectingAuth0Client(),
    )
    response = client.post(
        f"/events/{event.slug}/account-setup",
        json={"token": token, "password": "Rejected-password-2026"},
    )

    assert response.status_code == 422
    test_session.refresh(setup)
    assert setup.consumed_at is None


def test_claim_falls_back_to_auth0_management_email(event, registration, monkeypatch):
    class FakeManagementClient:
        def get_user_by_id(self, user_id):
            assert user_id == "auth0|attendee"
            return {"email": "attendee@example.com", "email_verified": True}

    monkeypatch.setattr(
        "routers.events.get_auth0_management_client",
        lambda: FakeManagementClient(),
    )
    set_token({"sub": "auth0|attendee"})

    response = client.post(f"/events/{event.slug}/claim")

    assert response.status_code == 200
    assert response.json()["claimed"] is True


def test_claim_uses_namespaced_claim_and_issues_opaque_pass(
    event, registration, test_session
):
    response = claim(event)

    assert response.status_code == 200
    body = response.json()
    assert body["claimed"] is True
    assert body["registration"]["phone"] == "+15555550100"
    assert body["registration"]["age"] == 20
    assert body["registration"]["university"] == "Duke University"
    assert body["registration"]["degree_program"] == "Undergraduate"
    assert body["registration"]["country"] == "United States"
    assert body["registration"]["attendance_commitment"] is True
    assert body["registration"]["photo_release_consent"] is True
    public_id = body["registration"]["event_pass"]["public_id"]
    assert public_id.startswith("evt_")

    test_session.refresh(registration)
    assert registration.user_id is not None
    assert public_id != str(registration.user_id)

    repeated = claim(event)
    assert repeated.status_code == 200
    assert repeated.json()["registration"]["event_pass"]["public_id"] == public_id


def test_admin_registration_list_is_role_protected_and_includes_private_fields(
    event, registration, test_session
):
    regular_user = User(auth0_id="auth0|regular")
    test_session.add(regular_user)
    test_session.flush()
    set_token({"sub": regular_user.auth0_id})

    denied = client.get(f"/events/{event.slug}/registrations")
    assert denied.status_code == 403

    admin = User(auth0_id="auth0|admin")
    test_session.add(admin)
    test_session.flush()
    test_session.add(UserRole(user_id=admin.id, role=RoleEnum.ADMIN))
    test_session.flush()
    set_token({"sub": admin.auth0_id})

    response = client.get(f"/events/{event.slug}/registrations")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["registrations"][0]["phone"] == "+15555550100"
    assert (
        body["registrations"][0]["source_data"]["form_response"]["example"]
        == "retained"
    )


@pytest.mark.parametrize("scanner_role", [RoleEnum.CHECK_IN, RoleEnum.ADMIN])
def test_check_in_is_event_scoped_and_prevents_duplicate_checkpoint(
    event, registration, test_session, scanner_role
):
    claim_response = claim(event)
    pass_id = claim_response.json()["registration"]["event_pass"]["public_id"]

    scanner = User(auth0_id=f"auth0|scanner-{scanner_role.value}")
    test_session.add(scanner)
    test_session.flush()
    test_session.add(UserRole(user_id=scanner.id, role=scanner_role))
    other_event = Event(
        slug=f"other-event-{uuid4()}",
        name="Other Event",
        state="active",
        pass_eligibility="confirmed",
    )
    test_session.add(other_event)
    test_session.flush()
    set_token({"sub": scanner.auth0_id})

    wrong_event = client.post(
        f"/events/{other_event.slug}/check-ins",
        json={"pass_id": pass_id, "checkpoint": "arrival"},
    )
    assert wrong_event.status_code == 404

    first = client.post(
        f"/events/{event.slug}/check-ins",
        json={"pass_id": pass_id, "checkpoint": "arrival"},
    )
    assert first.status_code == 200
    assert first.json()["registration_id"] == str(registration.id)

    duplicate = client.post(
        f"/events/{event.slug}/check-ins",
        json={"pass_id": pass_id, "checkpoint": "arrival"},
    )
    assert duplicate.status_code == 409

    listing = client.get(f"/events/{event.slug}/check-ins")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


def test_attendee_can_enable_and_disable_event_notifications(
    event, registration, test_session, monkeypatch
):
    monkeypatch.setattr("routers.events.NOTIFICATION_EVENT_SLUG", event.slug)
    claim_response = claim(event)
    assert claim_response.status_code == 200
    monkeypatch.setenv("EVENT_NOTIFICATIONS_ENABLED", "true")
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "public-test-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "private-test-key")
    monkeypatch.setenv("VAPID_SUBJECT", "mailto:organizers@duquantum.org")

    config = client.get(f"/events/{event.slug}/notifications")

    assert config.status_code == 200
    assert config.json()["enabled"] is True
    assert config.json()["subscribed"] is False
    assert config.json()["schedule_count"] == 14
    assert config.json()["public_key"] == "public-test-key"

    rejected = client.post(
        f"/events/{event.slug}/notifications/subscriptions",
        json={
            "endpoint": "http://push.example.test/subscription",
            "keys": {"p256dh": "a" * 88, "auth": "b" * 22},
        },
    )
    assert rejected.status_code == 422

    created = client.post(
        f"/events/{event.slug}/notifications/subscriptions",
        json={
            "endpoint": "https://fcm.googleapis.com/fcm/send/subscription",
            "keys": {"p256dh": "a" * 88, "auth": "b" * 22},
        },
        headers={"user-agent": "test-browser"},
    )
    assert created.status_code == 200
    assert created.json()["subscribed"] is True

    subscription = test_session.query(EventPushSubscription).one()
    assert subscription.registration_id == registration.id
    assert subscription.active is True
    assert subscription.endpoint_hash != subscription.endpoint

    disabled = client.request(
        "DELETE",
        f"/events/{event.slug}/notifications/subscriptions",
        json={"endpoint": "https://fcm.googleapis.com/fcm/send/subscription"},
    )
    assert disabled.status_code == 200
    assert disabled.json()["subscribed"] is False
    test_session.refresh(subscription)
    assert subscription.active is False


def make_check_in_admin(test_session, role=RoleEnum.ADMIN):
    staff = User(auth0_id=f"auth0|manual-check-in-{uuid4()}")
    test_session.add(staff)
    test_session.flush()
    if role is not None:
        test_session.add(UserRole(user_id=staff.id, role=role))
        test_session.flush()
    set_token({"sub": staff.auth0_id})
    return staff


def test_admin_can_check_in_by_registration_without_account_or_pass(event, registration, test_session):
    admin = make_check_in_admin(test_session)
    url = f"/events/{event.slug}/registrations/{registration.id}/check-ins"
    result = client.post(url, json={"checkpoint": "arrival"})
    assert result.status_code == 200
    assert result.json()["registration_id"] == str(registration.id)
    assert result.json()["checked_in_by"] == str(admin.id)
    assert registration.user_id is None
    assert registration.event_pass is None
    assert client.post(url, json={"checkpoint": "arrival"}).status_code == 409
    listing = client.get(f"/events/{event.slug}/check-ins").json()
    assert listing["total"] == 1


@pytest.mark.parametrize("role", [RoleEnum.CHECK_IN, None])
def test_manual_registration_check_in_requires_admin(event, registration, test_session, role):
    make_check_in_admin(test_session, role)
    result = client.post(f"/events/{event.slug}/registrations/{registration.id}/check-ins", json={})
    assert result.status_code == 403


def test_manual_check_in_rejects_wrong_event_ineligible_and_bad_checkpoint(event, registration, test_session):
    make_check_in_admin(test_session)
    other = Event(slug=f"other-{uuid4()}", name="Other", state="active", pass_eligibility="confirmed")
    test_session.add(other)
    test_session.flush()
    assert client.post(f"/events/{other.slug}/registrations/{registration.id}/check-ins", json={}).status_code == 404
    url = f"/events/{event.slug}/registrations/{registration.id}/check-ins"
    assert client.post(url, json={"checkpoint": "bad checkpoint"}).status_code == 422
    registration.admission_status = "revoked"
    test_session.flush()
    assert client.post(url, json={}).status_code == 403


@pytest.mark.parametrize("manual_first", [True, False])
def test_qr_and_manual_check_in_share_duplicate_protection(event, registration, test_session, manual_first):
    pass_id = claim(event).json()["registration"]["event_pass"]["public_id"]
    make_check_in_admin(test_session)
    manual = (f"/events/{event.slug}/registrations/{registration.id}/check-ins", {"checkpoint": "arrival"})
    qr = (f"/events/{event.slug}/check-ins", {"pass_id": pass_id, "checkpoint": "arrival"})
    first, second = (manual, qr) if manual_first else (qr, manual)
    assert client.post(first[0], json=first[1]).status_code == 200
    assert client.post(second[0], json=second[1]).status_code == 409
    assert client.get(f"/events/{event.slug}/check-ins").json()["total"] == 1
    registration.event_pass.state = "revoked"
    test_session.flush()
    assert client.post(manual[0], json={"checkpoint": "saturday_lunch"}).status_code == 403
    assert client.post(qr[0], json={"pass_id": pass_id, "checkpoint": "saturday_lunch"}).status_code == 404
