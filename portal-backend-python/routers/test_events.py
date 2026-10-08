from uuid import uuid4
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from db import get_db
from models.event import Event
from models.event_registration import EventRegistration
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


def test_claim_falls_back_to_auth0_management_email(
    event, registration, monkeypatch
):
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
    assert body["registrations"][0]["source_data"]["form_response"]["example"] == "retained"


def test_check_in_is_event_scoped_and_prevents_duplicate_checkpoint(
    event, registration, test_session
):
    claim_response = claim(event)
    pass_id = claim_response.json()["registration"]["event_pass"]["public_id"]

    scanner = User(auth0_id="auth0|scanner")
    test_session.add(scanner)
    test_session.flush()
    test_session.add(UserRole(user_id=scanner.id, role=RoleEnum.CHECK_IN))
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
