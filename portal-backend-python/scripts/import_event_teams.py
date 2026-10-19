"""Validate and reconcile DuQuantum team-formation responses.

The command is offline and dry-run by default. It never guesses between two
named teams, never lets an ``N/A`` response erase a named-team response, and
never uses fuzzy-name matching. A supplied-but-unmatched email may reconcile
only through an exact full name that is unique in both current source sets.

Run from ``portal-backend-python``::

    python -m scripts.import_event_teams --input path/to/responses.xlsx
    python -m scripts.import_event_teams --database-check --report path/to/report.json
    python -m scripts.import_event_teams --commit \
        --confirm-event duquantum-2026

Console output and the optional reconciliation report contain row references
and aggregate counts only, not attendee names or email addresses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo


EVENT_SLUG = "duquantum-2026"
DEFAULT_INPUT = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "private"
    / EVENT_SLUG
    / "team_formation_and_challenge_preferences.xlsx"
)

HEADER_TIMESTAMP = "Timestamp"
HEADER_TEAM_NAME = "What is your team name? (please keep this appropriate)"
HEADER_ADDITIONAL_TEAMMATES = (
    "If you have entered less than 4 team members: how many additional "
    "teammates would you like us to assign to your team? (if you have 4 team "
    "members already, select 0)"
)
HEADER_TRACK = (
    "Would you like to compete in the Standard Track or the Introductory "
    "Track? (note this is agnostic of your challenge selection). We will try "
    "our best to assign you to your preferred track. We will take you "
    "background into account (e.g. a team with a 4th year PhD student in "
    "quantum computing will likely be placed in the Standard Track)."
)
CHALLENGE_HEADER_PREFIX = (
    "Please rank the sponsor challenges (labeled by company name) in order of "
    "preference for your team, where \"1st choice\" means most preferred, and "
    "\"6th choice\" means least preferred."
)

TEAM_MEMBER_HEADERS = tuple(
    {
        "first_name": f"Teammate {position}: First Name",
        "last_name": f"Teammate {position}: Last Name",
        "email": f"Teammate {position}: Email",
        "discord_username": f"Teammate {position}: Discord Username",
    }
    for position in range(1, 5)
)

PLACEHOLDER_VALUES = {
    "",
    "n a",
    "na",
    "nil",
    "none",
    "not applicable",
    "tbd",
    "unknown",
}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
FORM_TIMEZONE = ZoneInfo("America/New_York")
TIMESTAMP_FORMATS = (
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %I:%M %p",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
)


class TeamImportValidationError(ValueError):
    """A workbook error whose message is safe to print without source values."""


@dataclass(frozen=True)
class ParsedTeamMember:
    row_number: int
    position: int
    first_name: str | None
    last_name: str | None
    email: str | None
    normalized_email: str | None
    discord_username: str | None
    normalized_name: str


@dataclass(frozen=True)
class ParsedTeam:
    row_number: int
    submitted_at: datetime
    name: str
    normalized_name: str
    requested_additional_teammates: int
    track_preference: str
    challenge_preferences: tuple[str, ...]
    members: tuple[ParsedTeamMember, ...]
    source_record_id: str


@dataclass(frozen=True)
class ParseIssue:
    row_number: int
    reason: str


@dataclass(frozen=True)
class TeamParseResult:
    source_sha256: str
    raw_rows: int
    teams: tuple[ParsedTeam, ...]
    duplicate_team_groups: int
    superseded_team_rows: int
    no_team_rows: tuple[int, ...]
    invalid_rows: tuple[ParseIssue, ...]

    @property
    def member_rows(self) -> int:
        return sum(len(team.members) for team in self.teams)

    @property
    def invalid_reasons(self) -> Mapping[str, int]:
        return Counter(issue.reason for issue in self.invalid_rows)


@dataclass(frozen=True)
class ReconciledMember:
    team: ParsedTeam
    member: ParsedTeamMember
    registration_id: Any | None
    match_status: str
    match_method: str | None
    match_detail: str


@dataclass(frozen=True)
class ReconciliationResult:
    members: tuple[ReconciledMember, ...]

    @property
    def counts(self) -> Mapping[str, int]:
        return Counter(item.match_status for item in self.members)


@dataclass(frozen=True)
class DatabaseSyncResult:
    counts: Mapping[str, int]
    reconciliation: ReconciliationResult


def normalize_text(value: Any) -> str:
    """Normalize human-entered identifiers without discarding non-Latin text."""

    decomposed = unicodedata.normalize("NFKD", str(value or "").strip().casefold())
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(
        "".join(character if character.isalnum() else " " for character in without_marks).split()
    )


def normalize_email(value: Any) -> str:
    return str(value or "").strip().casefold()


def is_placeholder(value: Any) -> bool:
    return normalize_text(value) in PLACEHOLDER_VALUES


def _optional_source_text(value: Any) -> str | None:
    raw = str(value or "").strip()
    return None if is_placeholder(raw) else raw


def parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = str(value or "").strip()
        parsed = None
        for format_string in TIMESTAMP_FORMATS:
            try:
                parsed = datetime.strptime(raw, format_string)
                break
            except ValueError:
                continue
        if parsed is None:
            raise TeamImportValidationError("unrecognized timestamp")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=FORM_TIMEZONE)
    return parsed.astimezone(timezone.utc)


def _challenge_headers(headers: Iterable[str]) -> tuple[str, ...]:
    matches = [header for header in headers if header.startswith(CHALLENGE_HEADER_PREFIX)]
    if len(matches) != 6:
        raise TeamImportValidationError(
            "workbook must contain exactly six challenge preference columns"
        )
    return tuple(matches)


def _source_record_id(normalized_name: str, submitted_at: datetime) -> str:
    source_key = f"{EVENT_SLUG}\0{normalized_name}\0{submitted_at.isoformat()}"
    return hashlib.sha256(source_key.encode("utf-8")).hexdigest()


def _parse_requested_teammates(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise TeamImportValidationError("invalid additional teammate count")
        if not number.is_integer():
            raise TeamImportValidationError("invalid additional teammate count")
        parsed = int(number)
    if not 0 <= parsed <= 4:
        raise TeamImportValidationError("additional teammate count is outside 0-4")
    return parsed


def _parse_member(
    row: Mapping[str, Any], *, row_number: int, position: int
) -> ParsedTeamMember | None:
    headers = TEAM_MEMBER_HEADERS[position - 1]
    first_name = _optional_source_text(row.get(headers["first_name"]))
    last_name = _optional_source_text(row.get(headers["last_name"]))
    email = _optional_source_text(row.get(headers["email"]))
    discord_username = _optional_source_text(row.get(headers["discord_username"]))
    if not any((first_name, last_name, email, discord_username)):
        return None
    normalized_email = normalize_email(email) if email else None
    return ParsedTeamMember(
        row_number=row_number,
        position=position,
        first_name=first_name,
        last_name=last_name,
        email=email,
        normalized_email=normalized_email,
        discord_username=discord_username,
        normalized_name=normalize_text(f"{first_name or ''} {last_name or ''}"),
    )


def parse_team_rows(
    *,
    headers: Sequence[str],
    rows: Iterable[Mapping[str, Any]],
    source_sha256: str,
) -> TeamParseResult:
    required_headers = {
        HEADER_TIMESTAMP,
        HEADER_TEAM_NAME,
        HEADER_ADDITIONAL_TEAMMATES,
        HEADER_TRACK,
        *(header for group in TEAM_MEMBER_HEADERS for header in group.values()),
    }
    missing = required_headers.difference(headers)
    if missing:
        raise TeamImportValidationError(
            f"workbook is missing {len(missing)} required column(s)"
        )
    challenge_headers = _challenge_headers(headers)

    latest_by_team: dict[str, ParsedTeam] = {}
    seen_team_counts: Counter[str] = Counter()
    no_team_rows: list[int] = []
    invalid_rows: list[ParseIssue] = []
    raw_rows = 0

    for row_number, row in enumerate(rows, start=2):
        raw_rows += 1
        team_name = str(row.get(HEADER_TEAM_NAME) or "").strip()
        if is_placeholder(team_name):
            # These are unassigned participants, not teams. They cannot
            # supersede a named-team submission from the same person.
            no_team_rows.append(row_number)
            continue
        try:
            submitted_at = parse_timestamp(row.get(HEADER_TIMESTAMP))
            track_preference = str(row.get(HEADER_TRACK) or "").strip()
            if not track_preference:
                raise TeamImportValidationError("blank track preference")
            challenge_preferences = tuple(
                str(row.get(header) or "").strip() for header in challenge_headers
            )
            if any(not value for value in challenge_preferences):
                raise TeamImportValidationError("blank challenge preference")
            if len({value.casefold() for value in challenge_preferences}) != 6:
                raise TeamImportValidationError(
                    "challenge preferences must contain six unique sponsors"
                )
            members = tuple(
                member
                for position in range(1, 5)
                if (
                    member := _parse_member(
                        row, row_number=row_number, position=position
                    )
                )
                is not None
            )
            if not members:
                raise TeamImportValidationError("named team has no members")
            normalized_name = normalize_text(team_name)
            team = ParsedTeam(
                row_number=row_number,
                submitted_at=submitted_at,
                name=team_name,
                normalized_name=normalized_name,
                requested_additional_teammates=_parse_requested_teammates(
                    row.get(HEADER_ADDITIONAL_TEAMMATES)
                ),
                track_preference=track_preference,
                challenge_preferences=challenge_preferences,
                members=members,
                source_record_id=_source_record_id(normalized_name, submitted_at),
            )
        except TeamImportValidationError as exc:
            invalid_rows.append(ParseIssue(row_number=row_number, reason=str(exc)))
            continue

        seen_team_counts[team.normalized_name] += 1
        current = latest_by_team.get(team.normalized_name)
        if current is None or (team.submitted_at, team.row_number) > (
            current.submitted_at,
            current.row_number,
        ):
            latest_by_team[team.normalized_name] = team

    teams = tuple(sorted(latest_by_team.values(), key=lambda item: item.normalized_name))
    return TeamParseResult(
        source_sha256=source_sha256,
        raw_rows=raw_rows,
        teams=teams,
        duplicate_team_groups=sum(1 for count in seen_team_counts.values() if count > 1),
        superseded_team_rows=sum(
            count - 1 for count in seen_team_counts.values() if count > 1
        ),
        no_team_rows=tuple(no_team_rows),
        invalid_rows=tuple(invalid_rows),
    )


def parse_xlsx(path: Path) -> TeamParseResult:
    from openpyxl import load_workbook

    source_bytes = path.read_bytes()
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        if not workbook.sheetnames:
            raise TeamImportValidationError("workbook has no worksheets")
        worksheet = workbook[workbook.sheetnames[0]]
        values = worksheet.iter_rows(values_only=True)
        first_row = next(values, None)
        if first_row is None:
            raise TeamImportValidationError("workbook is empty")
        headers = tuple(str(value or "").strip() for value in first_row)
        rows = (
            dict(zip(headers, row))
            for row in values
            if any(value not in (None, "") for value in row)
        )
        return parse_team_rows(
            headers=headers,
            rows=rows,
            source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        )
    finally:
        workbook.close()


def _registration_name_keys(registration: Any) -> set[str]:
    keys = {
        normalize_text(
            f"{getattr(registration, 'first_name', '') or ''} "
            f"{getattr(registration, 'last_name', '') or ''}"
        )
    }
    preferred_name = getattr(registration, "preferred_name", None)
    if preferred_name:
        keys.add(
            normalize_text(
                f"{preferred_name} {getattr(registration, 'last_name', '') or ''}"
            )
        )
    return {key for key in keys if key}


def reconcile_members(
    teams: Sequence[ParsedTeam], registrations: Sequence[Any]
) -> ReconciliationResult:
    registrations_by_email: dict[str, list[Any]] = defaultdict(list)
    registrations_by_name: dict[str, dict[str, Any]] = defaultdict(dict)
    for registration in registrations:
        normalized_email = normalize_email(
            getattr(registration, "normalized_email", None)
            or getattr(registration, "email", None)
        )
        if normalized_email:
            registrations_by_email[normalized_email].append(registration)
        for name_key in _registration_name_keys(registration):
            registrations_by_name[name_key][str(registration.id)] = registration

    email_occurrences: dict[str, list[tuple[str, int]]] = defaultdict(list)
    team_name_occurrences: Counter[str] = Counter()
    for team in teams:
        for member in team.members:
            if member.normalized_name:
                team_name_occurrences[member.normalized_name] += 1
            if member.normalized_email and EMAIL_PATTERN.fullmatch(
                member.normalized_email
            ):
                email_occurrences[member.normalized_email].append(
                    (team.normalized_name, member.position)
                )

    preliminary: list[ReconciledMember] = []
    for team in teams:
        for member in team.members:
            if member.normalized_email:
                if not EMAIL_PATTERN.fullmatch(member.normalized_email):
                    preliminary.append(
                        ReconciledMember(
                            team,
                            member,
                            None,
                            "unmatched",
                            None,
                            "invalid_email",
                        )
                    )
                    continue
                occurrences = email_occurrences[member.normalized_email]
                team_keys = {team_key for team_key, _position in occurrences}
                if len(team_keys) > 1:
                    preliminary.append(
                        ReconciledMember(
                            team,
                            member,
                            None,
                            "ambiguous",
                            "email",
                            "email_conflict_between_named_teams",
                        )
                    )
                    continue
                if len(occurrences) > 1:
                    preliminary.append(
                        ReconciledMember(
                            team,
                            member,
                            None,
                            "ambiguous",
                            "email",
                            "email_duplicate_within_team",
                        )
                    )
                    continue
                matches = registrations_by_email.get(member.normalized_email, [])
                if len(matches) == 1:
                    preliminary.append(
                        ReconciledMember(
                            team,
                            member,
                            matches[0].id,
                            "matched",
                            "email",
                            "exact_email",
                        )
                    )
                elif len(matches) > 1:
                    preliminary.append(
                        ReconciledMember(
                            team,
                            member,
                            None,
                            "ambiguous",
                            "email",
                            "email_matches_multiple_registrations",
                        )
                    )
                else:
                    # A conservative exact-name reconciliation handles a
                    # participant who used a different address on the two
                    # forms. Both the event roster and effective team rows must
                    # contain the normalized full name exactly once. Fuzzy
                    # matching is intentionally never used.
                    name_matches = list(
                        registrations_by_name.get(
                            member.normalized_name, {}
                        ).values()
                    )
                    if (
                        member.normalized_name
                        and team_name_occurrences[member.normalized_name] == 1
                        and len(name_matches) == 1
                    ):
                        preliminary.append(
                            ReconciledMember(
                                team,
                                member,
                                name_matches[0].id,
                                "matched",
                                "exact_unique_name_email_mismatch",
                                "exact_unique_name_email_mismatch",
                            )
                        )
                    else:
                        preliminary.append(
                            ReconciledMember(
                                team,
                                member,
                                None,
                                "unmatched",
                                "email",
                                "email_not_found",
                            )
                        )
                continue

            if not member.normalized_name:
                preliminary.append(
                    ReconciledMember(
                        team,
                        member,
                        None,
                        "unmatched",
                        None,
                        "missing_email_and_name",
                    )
                )
                continue
            name_matches = list(
                registrations_by_name.get(member.normalized_name, {}).values()
            )
            if len(name_matches) == 1:
                preliminary.append(
                    ReconciledMember(
                        team,
                        member,
                        name_matches[0].id,
                        "matched",
                        "name",
                        "unique_exact_name_without_email",
                    )
                )
            elif len(name_matches) > 1:
                preliminary.append(
                    ReconciledMember(
                        team,
                        member,
                        None,
                        "ambiguous",
                        "name",
                        "name_matches_multiple_registrations",
                    )
                )
            else:
                preliminary.append(
                    ReconciledMember(
                        team,
                        member,
                        None,
                        "unmatched",
                        "name",
                        "name_not_found",
                    )
                )

    candidate_indexes: dict[str, list[int]] = defaultdict(list)
    for index, item in enumerate(preliminary):
        if item.registration_id is not None:
            candidate_indexes[str(item.registration_id)].append(index)
    for indexes in candidate_indexes.values():
        if len(indexes) <= 1:
            continue
        confidence = {
            "email": 3,
            "name": 2,
            "exact_unique_name_email_mismatch": 1,
        }
        highest = max(confidence.get(preliminary[index].match_method, 0) for index in indexes)
        highest_indexes = [
            index
            for index in indexes
            if confidence.get(preliminary[index].match_method, 0) == highest
        ]
        if len(highest_indexes) == 1:
            for index in indexes:
                if index == highest_indexes[0]:
                    continue
                preliminary[index] = replace(
                    preliminary[index],
                    registration_id=None,
                    match_status="unmatched",
                    match_detail="registration_already_linked_by_higher_confidence_match",
                )
            continue
        for index in indexes:
            preliminary[index] = replace(
                preliminary[index],
                registration_id=None,
                match_status="ambiguous",
                match_detail="registration_listed_multiple_times",
            )

    return ReconciliationResult(members=tuple(preliminary))


def sync_database(result: TeamParseResult, *, commit: bool) -> DatabaseSyncResult:
    from sqlalchemy.orm import joinedload

    from db import get_local_session
    from models import Event, EventRegistration, EventTeam, EventTeamMember

    session = get_local_session()
    counts: Counter[str] = Counter()
    try:
        event = session.query(Event).filter(Event.slug == EVENT_SLUG).one_or_none()
        if event is None:
            raise RuntimeError(
                "DuQuantum event seed is missing; apply migrations first"
            )
        registrations = list(
            session.query(EventRegistration)
            .filter(
                EventRegistration.event_id == event.id,
                EventRegistration.admission_status == "accepted",
                EventRegistration.rsvp_status == "confirmed",
            )
            .all()
        )
        reconciliation = reconcile_members(result.teams, registrations)
        reconciled_by_team: dict[str, list[ReconciledMember]] = defaultdict(list)
        for item in reconciliation.members:
            reconciled_by_team[item.team.normalized_name].append(item)

        existing_teams = list(
            session.query(EventTeam)
            .options(joinedload(EventTeam.members))
            .filter(EventTeam.event_id == event.id)
            .all()
        )
        existing_by_name = {team.normalized_name: team for team in existing_teams}
        current_names = {team.normalized_name for team in result.teams}

        for existing in existing_teams:
            if existing.normalized_name in current_names:
                continue
            if existing.active:
                existing.active = False
                counts["teams_archived"] += 1
            for member in existing.members:
                member.registration_id = None
                member.match_status = "unmatched"
                member.match_method = None
                member.match_detail = "team_not_in_latest_import"

        current_database_teams: dict[str, Any] = {}
        for parsed_team in result.teams:
            database_team = existing_by_name.get(parsed_team.normalized_name)
            if database_team is None:
                database_team = EventTeam(
                    event_id=event.id,
                    name=parsed_team.name,
                    normalized_name=parsed_team.normalized_name,
                    source_record_id=parsed_team.source_record_id,
                    source_submitted_at=parsed_team.submitted_at,
                )
                session.add(database_team)
                counts["teams_created"] += 1
            else:
                if not database_team.active:
                    counts["teams_reactivated"] += 1
                counts["teams_updated"] += 1
            database_team.name = parsed_team.name
            database_team.track_preference = parsed_team.track_preference
            database_team.challenge_preferences = list(
                parsed_team.challenge_preferences
            )
            database_team.requested_additional_teammates = (
                parsed_team.requested_additional_teammates
            )
            database_team.source = "google_forms_xlsx"
            database_team.source_record_id = parsed_team.source_record_id
            database_team.source_submitted_at = parsed_team.submitted_at
            database_team.active = True
            current_database_teams[parsed_team.normalized_name] = database_team

        session.flush()
        for database_team in current_database_teams.values():
            for existing_member in list(database_team.members):
                session.delete(existing_member)
        session.flush()

        for parsed_team in result.teams:
            database_team = current_database_teams[parsed_team.normalized_name]
            for item in sorted(
                reconciled_by_team[parsed_team.normalized_name],
                key=lambda value: value.member.position,
            ):
                session.add(
                    EventTeamMember(
                        event_id=event.id,
                        team_id=database_team.id,
                        registration_id=item.registration_id,
                        member_position=item.member.position,
                        first_name=item.member.first_name,
                        last_name=item.member.last_name,
                        email=item.member.email,
                        normalized_email=item.member.normalized_email,
                        discord_username=item.member.discord_username,
                        match_status=item.match_status,
                        match_method=item.match_method,
                        match_detail=item.match_detail,
                        source_row_number=item.member.row_number,
                    )
                )
                counts[f"members_{item.match_status}"] += 1

        session.flush()
        if commit:
            session.commit()
        else:
            session.rollback()
        return DatabaseSyncResult(counts=dict(counts), reconciliation=reconciliation)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def write_report(
    path: Path,
    *,
    parse_result: TeamParseResult,
    database_result: DatabaseSyncResult | None,
) -> None:
    reconciliation = database_result.reconciliation if database_result else None
    issues = []
    if reconciliation is not None:
        issues = [
            {
                "source_record_id": item.team.source_record_id,
                "row_number": item.member.row_number,
                "member_position": item.member.position,
                "status": item.match_status,
                "method": item.match_method,
                "reason": item.match_detail,
            }
            for item in reconciliation.members
            if item.match_status != "matched"
        ]
    payload = {
        "event_slug": EVENT_SLUG,
        "source_sha256": parse_result.source_sha256,
        "rows_read": parse_result.raw_rows,
        "named_teams": len(parse_result.teams),
        "member_rows": parse_result.member_rows,
        "duplicate_team_groups": parse_result.duplicate_team_groups,
        "superseded_team_rows": parse_result.superseded_team_rows,
        "no_team_row_numbers": list(parse_result.no_team_rows),
        "invalid_rows": [
            {"row_number": issue.row_number, "reason": issue.reason}
            for issue in parse_result.invalid_rows
        ],
        "match_counts": dict(reconciliation.counts) if reconciliation else None,
        "issues": issues,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _print_summary(
    parse_result: TeamParseResult, database_result: DatabaseSyncResult | None
) -> None:
    print(f"Rows read: {parse_result.raw_rows}")
    print(f"Substantive named teams: {len(parse_result.teams)}")
    print(f"Current named-team member rows: {parse_result.member_rows}")
    print(f"Repeated named-team groups: {parse_result.duplicate_team_groups}")
    print(f"Older named-team submissions ignored: {parse_result.superseded_team_rows}")
    print(f"No-team placeholder rows left unassigned: {len(parse_result.no_team_rows)}")
    print(f"Invalid rows: {len(parse_result.invalid_rows)}")
    for reason, count in sorted(parse_result.invalid_reasons.items()):
        print(f"  {reason}: {count}")
    if database_result is not None:
        match_counts = database_result.reconciliation.counts
        print(f"Members matched: {match_counts.get('matched', 0)}")
        print(f"Members unmatched: {match_counts.get('unmatched', 0)}")
        print(f"Members ambiguous: {match_counts.get('ambiguous', 0)}")
        for key, value in sorted(database_result.counts.items()):
            print(f"Database {key.replace('_', ' ')}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--database-check",
        action="store_true",
        help="reconcile against the database and roll the transaction back",
    )
    parser.add_argument(
        "--commit", action="store_true", help="write the reconciled teams"
    )
    parser.add_argument(
        "--confirm-event",
        help=f"required with --commit; must equal {EVENT_SLUG}",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="write a PII-free JSON report containing row/slot issue references",
    )
    parser.add_argument("--expect-rows", type=int)
    parser.add_argument("--expect-teams", type=int)
    parser.add_argument("--expect-members", type=int)
    parser.add_argument("--expect-no-team-rows", type=int)
    parser.add_argument("--expect-superseded", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.commit and args.confirm_event != EVENT_SLUG:
        print(f"Refusing commit: pass --confirm-event {EVENT_SLUG}")
        return 2
    if not args.input.is_file():
        print("Input XLSX does not exist or is not a regular file")
        return 2
    try:
        result = parse_xlsx(args.input)
    except (OSError, TeamImportValidationError, ValueError) as exc:
        print(f"Validation failed: {exc}")
        return 2

    expected_counts = {
        "rows": (args.expect_rows, result.raw_rows),
        "teams": (args.expect_teams, len(result.teams)),
        "members": (args.expect_members, result.member_rows),
        "no-team rows": (args.expect_no_team_rows, len(result.no_team_rows)),
        "superseded rows": (args.expect_superseded, result.superseded_team_rows),
    }
    mismatches = [
        label
        for label, (expected, actual) in expected_counts.items()
        if expected is not None and expected != actual
    ]
    if mismatches:
        _print_summary(result, None)
        print(f"Count guard failed for {len(mismatches)} aggregate value(s)")
        return 2
    if result.invalid_rows and args.commit:
        _print_summary(result, None)
        print("Refusing commit while invalid rows are present")
        return 2

    database_result = None
    if args.database_check or args.commit:
        try:
            database_result = sync_database(result, commit=args.commit)
        except Exception as exc:
            # SQL exceptions may embed bound PII; log only the exception type.
            print(
                f"Database operation failed ({type(exc).__name__}); "
                "transaction rolled back"
            )
            return 1
    if args.report:
        write_report(
            args.report,
            parse_result=result,
            database_result=database_result,
        )

    _print_summary(result, database_result)
    print("Import committed" if args.commit else "Dry run only; no database changes made")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
