from types import SimpleNamespace
import pytest
from reconcile_duquantum_final_master import pick_registration, build_teams, prepare, people, select_existing_account


def row(email, **extra):
    values = dict(normalized_email=email, source_data={}, first_name="Test", last_name="Person", user_id=None, claimed_at=None, admission_status="accepted", rsvp_status="confirmed")
    values.update(extra)
    return SimpleNamespace(**values)


def person():
    return dict(email="form@example.org", aliases=["form@example.org", "login@example.org"], names={"test person"})


def test_existing_claimed_login_is_preserved_across_team_form_aliases():
    linked = row("login@example.org", user_id="user")
    stale = row("form@example.org", admission_status="revoked")
    assert pick_registration(person(), [linked, stale]) is linked


def test_conflicting_claimed_accounts_are_never_merged():
    with pytest.raises(ValueError, match="Multiple claimed"):
        pick_registration(person(), [row("login@example.org", user_id="u1", last_name="Different"), row("form@example.org", user_id="u2")])


def test_two_claimed_addresses_for_same_confirmed_person_use_exact_master_address():
    direct = row("form@example.org", user_id="u1")
    alias = row("login@example.org", user_id="u2")
    assert pick_registration(person(), [direct, alias]) is direct


def test_superseded_test_address_is_not_reactivated_by_name_matching():
    wrong = row("typo@example.org", source_data={"superseded_test_invitation_at": "date"})
    assert pick_registration(person(), [wrong]) is None


def test_existing_social_login_is_preserved_instead_of_switching_to_database_identity():
    google = {"user_id": "google-oauth2|social", "email_verified": True}
    database = {"user_id": "auth0|database", "email_verified": False}
    assert select_existing_account([google, database], [database], google["user_id"]) is google
    assert select_existing_account([google], [], google["user_id"]) is google
    assert select_existing_account([google], []) is google
    assert select_existing_account([google, database], [database], "unknown") is None


def test_master_rows_and_larger_teams_are_preserved_without_editing_sources():
    from pathlib import Path
    teams = Path(r"C:\Users\mzora\Downloads\DuQuantum 2026 Final Teams (1).xlsx")
    attendance = Path(r"C:\Users\mzora\Downloads\DuQuantum 2026 MASTER Attendance List (FINAL).xlsx")
    if not teams.exists() or not attendance.exists():
        pytest.skip("Private organizer workbooks are local only")
    payload = prepare(teams, attendance)
    result = build_teams(payload)
    profiles = people(payload)
    assert len(profiles) == 219
    assert all(item["fields"]["attendance_commitment"] is True for item in profiles)
    assert result.member_rows == 219
    assert len(result.teams) == 61
    assert len(next(team for team in result.teams if team.team_number == "14").members) == 6
    assert any(team.team_number == "62" for team in result.teams)
    assert not any(team.team_number == "61" for team in result.teams)
