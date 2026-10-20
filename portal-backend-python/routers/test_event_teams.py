from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest
import routers.events as events_module
from fastapi import FastAPI
from fastapi.testclient import TestClient

from db import get_db
from models import (
    Event,
    EventCheckIn,
    EventRegistration,
    EventTeam,
    EventTeamMember,
    RoleEnum,
    User,
    UserRole,
)
from routers.events import auth, router


app = FastAPI()
app.include_router(prefix="/events", router=router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_dependency_overrides(test_session):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = lambda: (yield test_session)
    yield
    app.dependency_overrides.clear()


def _set_token(auth0_id):
    app.dependency_overrides[auth.verify] = lambda: {"sub": auth0_id}


def _add_team(test_session, *, event, registration, name, row_number):
    team = EventTeam(
        event_id=event.id,
        name=name,
        normalized_name=name.casefold(),
        team_number=str(row_number - 1),
        track_preference="Introductory Track",
        assigned_track="Introductory",
        assigned_challenge="Sponsor One",
        sponsor_name="Sponsor One",
        challenge_preferences=["Sponsor One", "Sponsor Two"],
        requested_additional_teammates=1,
        formation_source="Team Form",
        source_record_id=f"{row_number:064d}",
        source_submitted_at=datetime.now(timezone.utc),
    )
    test_session.add(team)
    test_session.flush()
    test_session.add_all(
        [
            EventTeamMember(
                event_id=event.id,
                team_id=team.id,
                registration_id=registration.id,
                member_position=1,
                display_name=f"{registration.first_name} {registration.last_name}",
                first_name=registration.first_name,
                last_name=registration.last_name,
                email=registration.email,
                normalized_email=registration.normalized_email,
                discord_username="linked-user",
                match_status="matched",
                match_method="email",
                match_detail="exact_email",
                source_row_number=row_number,
            ),
            EventTeamMember(
                event_id=event.id,
                team_id=team.id,
                member_position=2,
                display_name="Unlinked Teammate",
                first_name="Unlinked",
                last_name="Teammate",
                email="unlinked@example.edu",
                normalized_email="unlinked@example.edu",
                discord_username="unlinked-user",
                match_status="unmatched",
                match_method="email",
                match_detail="email_not_found",
                source_row_number=row_number,
            ),
        ]
    )
    test_session.flush()
    return team


def _setup_two_teams(test_session):
    event = Event(
        slug=f"duquantum-teams-{uuid4()}",
        name="DuQuantum Teams Test",
        state="active",
        pass_eligibility="confirmed",
    )
    attendee_one = User(auth0_id=f"auth0|team-one-{uuid4()}")
    attendee_two = User(auth0_id=f"auth0|team-two-{uuid4()}")
    test_session.add_all([event, attendee_one, attendee_two])
    test_session.flush()
    registration_one = EventRegistration(
        event_id=event.id,
        user_id=attendee_one.id,
        email="one@example.edu",
        normalized_email="one@example.edu",
        first_name="Team",
        last_name="One",
        admission_status="accepted",
        rsvp_status="confirmed",
        source_data={"private": "admin only"},
    )
    registration_two = EventRegistration(
        event_id=event.id,
        user_id=attendee_two.id,
        email="two@example.edu",
        normalized_email="two@example.edu",
        first_name="Team",
        last_name="Two",
        admission_status="accepted",
        rsvp_status="confirmed",
        source_data={"private": "admin only"},
    )
    test_session.add_all([registration_one, registration_two])
    test_session.flush()
    _add_team(
        test_session,
        event=event,
        registration=registration_one,
        name="Team One",
        row_number=2,
    )
    _add_team(
        test_session,
        event=event,
        registration=registration_two,
        name="Team Two",
        row_number=3,
    )
    return event, attendee_one, attendee_two


def test_attendee_receives_only_their_linked_team_and_no_raw_import_data(
    test_session,
):
    event, attendee_one, _attendee_two = _setup_two_teams(test_session)
    event.start_at = datetime.now(timezone.utc) - timedelta(hours=1)
    registration_row = test_session.query(EventRegistration).filter_by(event_id=event.id, user_id=attendee_one.id).one()
    test_session.add(EventCheckIn(event_id=event.id, registration_id=registration_row.id, checkpoint="arrival"))
    test_session.flush()
    _set_token(attendee_one.auth0_id)

    response = client.get(f"/events/{event.slug}/me")

    assert response.status_code == 200
    registration = response.json()["registration"]
    assert "source_data" not in registration
    team = registration["team"]
    assert team["team_name"] == "Team One"
    assert team["assignments_visible"] is True
    assert team["track"] == "Introductory"
    assert team["challenge"] == "Sponsor One"
    assert team["sponsor"] == "Sponsor One"
    assert team["sponsor_contact_name"] is None
    assert team["sponsor_contact_email"] is None
    assert team["track_preference"] == "Introductory Track"
    assert team["challenge_preferences"] == ["Sponsor One", "Sponsor Two"]
    assert team["source"] == "Team Form"
    assert [member["display_name"] for member in team["teammates"]] == [
        "Team One",
        "Unlinked Teammate",
    ]
    assert all("match_detail" not in member for member in team["teammates"])


@pytest.mark.parametrize("started,checkpoint", [(False, None), (False, "arrival"), (True, None), (True, "lunch"), (None, "arrival")])
def test_attendee_assignment_details_require_start_and_arrival(test_session, started, checkpoint):
    event, attendee, _ = _setup_two_teams(test_session)
    event.start_at = None if started is None else datetime.now(timezone.utc) + timedelta(days=-1 if started else 1)
    registration = test_session.query(EventRegistration).filter_by(event_id=event.id, user_id=attendee.id).one()
    if checkpoint:
        test_session.add(EventCheckIn(event_id=event.id, registration_id=registration.id, checkpoint=checkpoint))
    test_session.flush()
    _set_token(attendee.auth0_id)
    response = client.get(f"/events/{event.slug}/me")
    assert response.status_code == 200
    team = response.json()["registration"]["team"]
    assert team["assignments_visible"] is False
    assert team["team_name"] == "Team One"
    assert len(team["teammates"]) == 2
    for field in ("track", "track_preference", "challenge", "sponsor", "sponsor_contact_name", "sponsor_contact_email", "additional_teammates_detail"):
        assert team[field] is None
    assert team["challenge_preferences"] == []


@pytest.mark.parametrize("seconds,visible", [(1, False), (0, True), (-1, True)])
def test_assignment_release_uses_server_time_at_exact_start(test_session, monkeypatch, seconds, visible):
    moment = datetime.fromisoformat("2026-10-24T09:00:00-04:00")

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return moment.astimezone(tz or timezone.utc)

    monkeypatch.setattr(events_module, "datetime", FrozenDatetime)
    event, attendee, _ = _setup_two_teams(test_session)
    event.start_at = moment + timedelta(seconds=seconds)
    registration = test_session.query(EventRegistration).filter_by(event_id=event.id, user_id=attendee.id).one()
    test_session.add(EventCheckIn(event_id=event.id, registration_id=registration.id, checkpoint="arrival"))
    test_session.flush()
    _set_token(attendee.auth0_id)
    response = client.get(f"/events/{event.slug}/me")
    assert response.status_code == 200
    team = response.json()["registration"]["team"]
    assert team["assignments_visible"] is visible
    assert team["challenge"] == ("Sponsor One" if visible else None)


def test_admin_team_details_are_authorized_and_searchable(test_session):
    event, attendee_one, _attendee_two = _setup_two_teams(test_session)
    _set_token(attendee_one.auth0_id)
    denied = client.get(f"/events/{event.slug}/registrations")
    assert denied.status_code == 403
    assert client.get(f"/events/{event.slug}/teams").status_code == 403

    admin = User(auth0_id=f"auth0|team-admin-{uuid4()}")
    test_session.add(admin)
    test_session.flush()
    test_session.add(UserRole(user_id=admin.id, role=RoleEnum.ADMIN))
    test_session.flush()
    _set_token(admin.auth0_id)

    response = client.get(
        f"/events/{event.slug}/registrations", params={"q": "Team One"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    registration = body["registrations"][0]
    assert registration["source_data"] == {"private": "admin only"}
    assert registration["team"]["team_name"] == "Team One"
    assert registration["team"]["assignments_visible"] is True
    assert registration["team"]["challenge"] == "Sponsor One"
    assert registration["team"]["teammates"][0]["match_status"] == "matched"
    assert registration["team"]["teammates"][1]["match_detail"] == "email_not_found"


def test_admin_team_directory_includes_teams_without_linked_registrations(test_session):
    event, _attendee_one, _attendee_two = _setup_two_teams(test_session)
    unlinked = EventTeam(
        event_id=event.id,
        name="Unlinked Final Team",
        normalized_name="unlinked final team",
        team_number="61",
        assigned_track="Standard",
        assigned_challenge="BlueQubit",
        sponsor_name="BlueQubit",
        challenge_preferences=["BlueQubit"],
        formation_source="Random",
        source="final_teams_xlsx",
        source_record_id="f" * 64,
        source_submitted_at=None,
    )
    test_session.add(unlinked)
    test_session.flush()
    test_session.add(
        EventTeamMember(
            event_id=event.id,
            team_id=unlinked.id,
            member_position=1,
            display_name="Final Workbook Member",
            email="not-in-portal@example.edu",
            normalized_email="not-in-portal@example.edu",
            discord_username="final-member",
            match_status="unmatched",
            match_method="email",
            match_detail="email_not_found",
            source_row_number=220,
        )
    )
    admin = User(auth0_id=f"auth0|team-directory-admin-{uuid4()}")
    test_session.add(admin)
    test_session.flush()
    test_session.add(UserRole(user_id=admin.id, role=RoleEnum.ADMIN))
    test_session.flush()
    _set_token(admin.auth0_id)

    response = client.get(
        f"/events/{event.slug}/teams",
        params={"track": "Standard", "source": "Random", "match_status": "unmatched"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["teams"][0]["team_number"] == "61"
    assert body["teams"][0]["source"] == "Random"
    assert body["teams"][0]["teammates"][0]["registration_id"] is None
    assert body["teams"][0]["teammates"][0]["display_name"] == "Final Workbook Member"
