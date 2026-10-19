from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from models import Event, EventRegistration, EventTeam
from scripts.import_event_teams import (
    CHALLENGE_HEADER_PREFIX,
    HEADER_ADDITIONAL_TEAMMATES,
    HEADER_TEAM_NAME,
    HEADER_TIMESTAMP,
    HEADER_TRACK,
    TEAM_MEMBER_HEADERS,
    ParsedTeam,
    ParsedTeamMember,
    TeamParseResult,
    parse_team_rows,
    reconcile_members,
    sync_database,
)


CHALLENGE_HEADERS = tuple(
    f"{CHALLENGE_HEADER_PREFIX} [{position} choice]" for position in range(1, 7)
)
HEADERS = (
    HEADER_TIMESTAMP,
    HEADER_TEAM_NAME,
    *(header for group in TEAM_MEMBER_HEADERS for header in group.values()),
    HEADER_ADDITIONAL_TEAMMATES,
    HEADER_TRACK,
    *CHALLENGE_HEADERS,
)


def _row(*, timestamp, team_name, member_email, first_name="First", last_name="Last"):
    row = {header: "N/A" for group in TEAM_MEMBER_HEADERS for header in group.values()}
    row.update(
        {
            HEADER_TIMESTAMP: timestamp,
            HEADER_TEAM_NAME: team_name,
            HEADER_ADDITIONAL_TEAMMATES: 0,
            HEADER_TRACK: "Introductory Track",
            TEAM_MEMBER_HEADERS[0]["first_name"]: first_name,
            TEAM_MEMBER_HEADERS[0]["last_name"]: last_name,
            TEAM_MEMBER_HEADERS[0]["email"]: member_email,
            **{
                header: f"Sponsor {index}"
                for index, header in enumerate(CHALLENGE_HEADERS, start=1)
            },
        }
    )
    return row


def _member(
    *,
    row_number,
    position,
    first_name,
    last_name,
    email=None,
):
    return ParsedTeamMember(
        row_number=row_number,
        position=position,
        first_name=first_name,
        last_name=last_name,
        email=email,
        normalized_email=email.casefold() if email else None,
        discord_username=None,
        normalized_name=f"{first_name} {last_name}".casefold(),
    )


def _team(*, row_number, name, members):
    return ParsedTeam(
        row_number=row_number,
        submitted_at=datetime(2026, 10, row_number, tzinfo=timezone.utc),
        name=name,
        normalized_name=name.casefold(),
        requested_additional_teammates=0,
        track_preference="Introductory Track",
        challenge_preferences=tuple(f"Sponsor {index}" for index in range(1, 7)),
        members=tuple(members),
        source_record_id=f"{row_number:064d}",
    )


def _parse_result(*teams):
    return TeamParseResult(
        source_sha256="0" * 64,
        raw_rows=len(teams),
        teams=tuple(teams),
        duplicate_team_groups=0,
        superseded_team_rows=0,
        no_team_rows=(),
        invalid_rows=(),
    )


def test_team_parser_keeps_latest_named_submission_and_ignores_later_na_row():
    rows = [
        _row(
            timestamp=datetime(2026, 10, 1, 9),
            team_name="Quantum Crew",
            member_email="person@example.edu",
        ),
        _row(
            timestamp=datetime(2026, 10, 2, 9),
            team_name="Quantum Crew",
            member_email="updated@example.edu",
        ),
        _row(
            timestamp=datetime(2026, 10, 3, 9),
            team_name="N/A",
            member_email="person@example.edu",
        ),
    ]

    result = parse_team_rows(
        headers=HEADERS,
        rows=rows,
        source_sha256="1" * 64,
    )

    assert result.raw_rows == 3
    assert len(result.teams) == 1
    assert result.teams[0].members[0].normalized_email == "updated@example.edu"
    assert result.duplicate_team_groups == 1
    assert result.superseded_team_rows == 1
    assert result.no_team_rows == (4,)
    assert result.invalid_rows == ()


def test_reconciliation_uses_exact_matches_and_never_fuzzy_matches():
    exact = SimpleNamespace(
        id=uuid4(),
        email="exact@example.edu",
        normalized_email="exact@example.edu",
        first_name="Ada",
        preferred_name=None,
        last_name="Lovelace",
    )
    alternate_email = SimpleNamespace(
        id=uuid4(),
        email="grace@example.edu",
        normalized_email="grace@example.edu",
        first_name="Grace",
        preferred_name=None,
        last_name="Hopper",
    )
    name_only = SimpleNamespace(
        id=uuid4(),
        email="alan@example.edu",
        normalized_email="alan@example.edu",
        first_name="Alan",
        preferred_name=None,
        last_name="Turing",
    )
    preferred_alias = SimpleNamespace(
        id=uuid4(),
        email="john@example.edu",
        normalized_email="john@example.edu",
        first_name="John",
        preferred_name="Jack",
        last_name="Smith",
    )
    conflict = SimpleNamespace(
        id=uuid4(),
        email="conflict@example.edu",
        normalized_email="conflict@example.edu",
        first_name="Shared",
        preferred_name=None,
        last_name="Person",
    )
    teams = (
        _team(
            row_number=2,
            name="Exact",
            members=[
                _member(
                    row_number=2,
                    position=1,
                    first_name="Ada",
                    last_name="Lovelace",
                    email="exact@example.edu",
                )
            ],
        ),
        _team(
            row_number=3,
            name="Alternate",
            members=[
                _member(
                    row_number=3,
                    position=1,
                    first_name="Grace",
                    last_name="Hopper",
                    email="different@example.edu",
                )
            ],
        ),
        _team(
            row_number=4,
            name="No Email",
            members=[
                _member(
                    row_number=4,
                    position=1,
                    first_name="Alan",
                    last_name="Turing",
                )
            ],
        ),
        _team(
            row_number=5,
            name="Primary Alias",
            members=[
                _member(
                    row_number=5,
                    position=1,
                    first_name="John",
                    last_name="Smith",
                    email="john@example.edu",
                )
            ],
        ),
        _team(
            row_number=6,
            name="Secondary Alias",
            members=[
                _member(
                    row_number=6,
                    position=1,
                    first_name="Jack",
                    last_name="Smith",
                    email="jack-alt@example.edu",
                )
            ],
        ),
        _team(
            row_number=7,
            name="Conflict One",
            members=[
                _member(
                    row_number=7,
                    position=1,
                    first_name="Shared",
                    last_name="Person",
                    email="conflict@example.edu",
                )
            ],
        ),
        _team(
            row_number=8,
            name="Conflict Two",
            members=[
                _member(
                    row_number=8,
                    position=1,
                    first_name="Shared",
                    last_name="Person",
                    email="conflict@example.edu",
                )
            ],
        ),
        _team(
            row_number=9,
            name="No Fuzzy",
            members=[
                _member(
                    row_number=9,
                    position=1,
                    first_name="Almost",
                    last_name="Hopper",
                    email="missing@example.edu",
                )
            ],
        ),
    )

    result = reconcile_members(
        teams,
        [exact, alternate_email, name_only, preferred_alias, conflict],
    )
    by_row = {item.member.row_number: item for item in result.members}

    assert by_row[2].registration_id == exact.id
    assert by_row[2].match_method == "email"
    assert by_row[3].registration_id == alternate_email.id
    assert by_row[3].match_method == "exact_unique_name_email_mismatch"
    assert by_row[4].registration_id == name_only.id
    assert by_row[4].match_method == "name"
    assert by_row[5].registration_id == preferred_alias.id
    assert by_row[6].registration_id is None
    assert by_row[6].match_detail == (
        "registration_already_linked_by_higher_confidence_match"
    )
    assert by_row[7].match_status == "ambiguous"
    assert by_row[8].match_status == "ambiguous"
    assert by_row[9].registration_id is None
    assert by_row[9].match_detail == "email_not_found"


def test_database_sync_preserves_assignments_and_archives_stale_teams(
    test_sessionmaker, monkeypatch
):
    setup = test_sessionmaker()
    event = Event(slug="duquantum-2026", name="DuQuantum 2026", state="active")
    registration = EventRegistration(
        event=event,
        email="person@example.edu",
        normalized_email="person@example.edu",
        first_name="First",
        last_name="Last",
        admission_status="accepted",
        rsvp_status="confirmed",
        source_data={},
    )
    historical = EventRegistration(
        event=event,
        email="historical@example.edu",
        normalized_email="historical@example.edu",
        first_name="Historical",
        last_name="Person",
        admission_status="revoked",
        rsvp_status="declined",
        source_data={},
    )
    setup.add_all([event, registration, historical])
    setup.commit()
    event_id = event.id
    registration_id = registration.id
    setup.close()
    monkeypatch.setattr("db.get_local_session", test_sessionmaker)

    team = _team(
        row_number=2,
        name="Quantum Crew",
        members=[
            _member(
                row_number=2,
                position=1,
                first_name="First",
                last_name="Last",
                email="person@example.edu",
            ),
            _member(
                row_number=2,
                position=2,
                first_name="Historical",
                last_name="Person",
                email="historical@example.edu",
            ),
        ],
    )
    created = sync_database(_parse_result(team), commit=True)

    assert created.counts["teams_created"] == 1
    assert created.counts["members_matched"] == 1
    assert created.counts["members_unmatched"] == 1
    verify = test_sessionmaker()
    database_team = verify.query(EventTeam).one()
    database_team.assigned_track = "Standard Track"
    database_team.assigned_challenge = "Assigned challenge"
    database_team.sponsor_name = "Assigned sponsor"
    database_team.sponsor_contact_name = "Sponsor Contact"
    database_team.sponsor_contact_email = "sponsor@example.com"
    verify.commit()
    verify.close()

    sync_database(_parse_result(team), commit=True)
    verify = test_sessionmaker()
    database_team = verify.query(EventTeam).one()
    assert database_team.assigned_track == "Standard Track"
    assert database_team.assigned_challenge == "Assigned challenge"
    assert database_team.sponsor_name == "Assigned sponsor"
    assert database_team.sponsor_contact_email == "sponsor@example.com"
    assert database_team.members[0].registration_id == registration_id
    verify.close()

    archived = sync_database(_parse_result(), commit=True)
    assert archived.counts["teams_archived"] == 1
    verify = test_sessionmaker()
    database_team = (
        verify.query(EventTeam).filter(EventTeam.event_id == event_id).one()
    )
    assert database_team.active is False
    assert database_team.members[0].registration_id is None
    assert database_team.members[0].match_detail == "team_not_in_latest_import"
    verify.close()

    # sync_database intentionally opens and commits its own sessions, so clean
    # up the event explicitly instead of relying on the surrounding fixture's
    # transaction. This keeps the complete backend suite order-independent.
    cleanup = test_sessionmaker()
    cleanup.query(Event).filter(Event.id == event_id).delete()
    cleanup.commit()
    cleanup.close()
