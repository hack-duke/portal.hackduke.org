from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from models import Event, EventRegistration, EventTeam
from scripts.import_event_teams import (
    MASTER_HEADERS,
    TEAM_HEADERS,
    ParsedTeam,
    ParsedTeamMember,
    TeamImportValidationError,
    TeamParseResult,
    main,
    parse_final_rows,
    parse_final_teams_xlsx,
    reconcile_members,
    sync_database,
)


REAL_WORKBOOK = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "private"
    / "duquantum-2026"
    / "final_teams.xlsx"
)
REAL_SHA256 = "91611e9aae4b3395368e443ba2701cdf8fabd9dd219004317a0ddf67b5369eef"


def _member(row, position, name, email):
    return ParsedTeamMember(
        row_number=row,
        position=position,
        display_name=name,
        email=email,
        normalized_email=email.casefold(),
        discord_username=None,
        normalized_name=name.casefold(),
    )


def _team(number="1", members=()):
    return ParsedTeam(
        row_number=2,
        team_number=number,
        name=f"Team {number}",
        normalized_name=f"team {number}",
        assigned_track="Introductory",
        assigned_challenge="Sponsor Challenge",
        formation_source="Team Form",
        requested_additional_teammates=0,
        additional_teammates_detail=None,
        challenge_preferences=("Sponsor Challenge", "Other"),
        members=tuple(members),
        source_record_id=number.zfill(64),
    )


def _result(*teams):
    return TeamParseResult(
        source_sha256="0" * 64,
        master_rows=sum(len(team.members) for team in teams),
        team_rows=len(teams),
        teams=tuple(teams),
    )


def _synthetic_rows():
    master = {header: None for header in MASTER_HEADERS}
    master.update(
        {
            "Team #": 1,
            "Team Name": "Quantum Crew",
            "Track": "Introductory",
            "Assigned Challenge": "Sponsor Challenge",
            "Team Size": 1,
            "Member Name": "Ada Lovelace",
            "Email": "ada@example.edu",
            "Discord": "ada",
            "Team Source": "Team Form",
        }
    )
    team = {header: None for header in TEAM_HEADERS}
    team.update(
        {
            "Team #": 1,
            "Team Name": "Quantum Crew",
            "Track": "Introductory",
            "Assigned Challenge": "Sponsor Challenge",
            "Size": 1,
            "Additional Members Requested": "0",
            "Members": "Ada Lovelace",
            "1st Choice": "Sponsor Challenge",
            "2nd Choice": "Other",
            "Team Source": "Team Form",
        }
    )
    return master, team


def test_parser_cross_checks_both_final_sheets():
    master, team = _synthetic_rows()
    result = parse_final_rows(
        master_headers=MASTER_HEADERS,
        master_rows=[master],
        team_headers=TEAM_HEADERS,
        team_rows=[team],
        source_sha256="1" * 64,
    )
    assert result.master_rows == 1
    assert result.team_rows == 1
    assert result.teams[0].assigned_track == "Introductory"
    assert result.teams[0].track_preference is None
    assert result.teams[0].assigned_challenge == "Sponsor Challenge"
    assert result.teams[0].members[0].display_name == "Ada Lovelace"

    changed = dict(team, **{"Assigned Challenge": "Different"})
    with pytest.raises(TeamImportValidationError, match="cross-sheet assignment"):
        parse_final_rows(
            master_headers=MASTER_HEADERS,
            master_rows=[master],
            team_headers=TEAM_HEADERS,
            team_rows=[changed],
            source_sha256="1" * 64,
        )


@pytest.mark.skipif(not REAL_WORKBOOK.is_file(), reason="private workbook not present")
def test_real_final_workbook_has_audited_shape_and_assignments():
    result = parse_final_teams_xlsx(REAL_WORKBOOK)
    assert result.source_sha256 == REAL_SHA256
    assert (result.master_rows, result.team_rows, len(result.teams)) == (219, 61, 61)
    assert result.member_rows == 219
    assert Counter(len(team.members) for team in result.teams) == {
        4: 46,
        3: 7,
        2: 6,
        1: 2,
    }
    assert Counter(team.formation_source for team in result.teams) == {
        "Team Form": 42,
        "Random": 18,
        "Organizer-added": 1,
    }
    assert Counter(
        team.assigned_track for team in result.teams for _member in team.members
    ) == {"Introductory": 139, "Standard": 80}
    assert all(team.assigned_challenge for team in result.teams)
    assert all(team.track_preference is None for team in result.teams)


def test_reconciliation_is_email_first_then_unique_exact_name_without_fuzzy():
    exact = SimpleNamespace(
        id=uuid4(),
        email="exact@example.edu",
        normalized_email="exact@example.edu",
        first_name="Ada",
        preferred_name=None,
        last_name="Lovelace",
    )
    alternate = SimpleNamespace(
        id=uuid4(),
        email="roster@example.edu",
        normalized_email="roster@example.edu",
        first_name="Grace",
        preferred_name=None,
        last_name="Hopper",
    )
    teams = (
        _team("1", [_member(2, 1, "Ada Lovelace", "exact@example.edu")]),
        _team("2", [_member(3, 1, "Grace Hopper", "other@example.edu")]),
        _team("3", [_member(4, 1, "Almost Hopper", "missing@example.edu")]),
    )
    result = reconcile_members(teams, [exact, alternate])
    assert [item.match_method for item in result.members] == [
        "email",
        "exact_unique_name_email_mismatch",
        "email",
    ]
    assert [item.match_status for item in result.members] == [
        "matched",
        "matched",
        "unmatched",
    ]


def test_sync_filters_roster_and_applies_final_assignments(
    test_sessionmaker, monkeypatch
):
    setup = test_sessionmaker()
    event = Event(slug="duquantum-2026", name="DuQuantum 2026", state="active")
    accepted = EventRegistration(
        event=event,
        email="accepted@example.edu",
        normalized_email="accepted@example.edu",
        first_name="Accepted",
        last_name="Person",
        admission_status="accepted",
        rsvp_status="confirmed",
        source_data={},
    )
    revoked = EventRegistration(
        event=event,
        email="revoked@example.edu",
        normalized_email="revoked@example.edu",
        first_name="Revoked",
        last_name="Person",
        admission_status="revoked",
        rsvp_status="declined",
        source_data={},
    )
    setup.add_all([event, accepted, revoked])
    setup.commit()
    event_id = event.id
    setup.close()
    monkeypatch.setattr("db.get_local_session", test_sessionmaker)

    team = _team(
        members=[
            _member(2, 1, "Accepted Person", "accepted@example.edu"),
            _member(3, 2, "Revoked Person", "revoked@example.edu"),
        ]
    )
    with pytest.raises(TeamImportValidationError, match="match-count guard"):
        sync_database(
            _result(team),
            commit=True,
            expected_match_counts={"matched": 2, "unmatched": 0, "ambiguous": 0},
        )
    guard_verify = test_sessionmaker()
    assert guard_verify.query(EventTeam).count() == 0
    guard_verify.close()

    synced = sync_database(_result(team), commit=True)
    assert synced.counts["members_matched"] == 1
    assert synced.counts["members_unmatched"] == 1
    verify = test_sessionmaker()
    database_team = verify.query(EventTeam).one()
    assert database_team.team_number == "1"
    assert database_team.assigned_track == "Introductory"
    assert database_team.assigned_challenge == "Sponsor Challenge"
    assert database_team.sponsor_name == "Sponsor Challenge"
    assert database_team.track_preference is None
    assert database_team.sponsor_contact_name is None
    assert database_team.source == "final_teams_xlsx"
    assert database_team.members[0].display_name == "Accepted Person"
    database_team.track_preference = "Historical form preference"
    database_team.sponsor_contact_name = "Organizer-entered contact"
    database_team.sponsor_contact_email = "contact@example.com"
    verify.commit()
    verify.close()

    sync_database(_result(team), commit=True)
    verify = test_sessionmaker()
    database_team = verify.query(EventTeam).one()
    assert database_team.track_preference == "Historical form preference"
    assert database_team.sponsor_contact_name == "Organizer-entered contact"
    assert database_team.sponsor_contact_email == "contact@example.com"
    verify.close()

    cleanup = test_sessionmaker()
    cleanup.query(EventTeam).filter(EventTeam.event_id == event_id).delete()
    cleanup.query(Event).filter(Event.id == event_id).delete()
    cleanup.commit()
    cleanup.close()


@pytest.mark.skipif(not REAL_WORKBOOK.is_file(), reason="private workbook not present")
def test_cli_source_guard_rejects_wrong_workbook_hash(capsys):
    status = main(["--input", str(REAL_WORKBOOK), "--expect-source-sha256", "0" * 64])
    assert status == 2
    assert "Source/count guard failed" in capsys.readouterr().out
