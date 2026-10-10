"""Validate and import Google Forms confirmations into event registrations.

Run from ``portal-backend-python``. The command is intentionally dry-run and
offline by default, so parsing the private CSV cannot mutate the database by
accident.

Examples::

    python -m scripts.import_event_registrations
    python -m scripts.import_event_registrations --database-check
    python -m scripts.import_event_registrations --commit \
        --confirm-event duquantum-2026

The command prints aggregate counts only. It never logs attendee values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo


EVENT_SLUG = "duquantum-2026"
DEFAULT_INPUT = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "private"
    / EVENT_SLUG
    / "confirmation_responses.csv"
)

HEADER_TIMESTAMP = "Timestamp"
HEADER_FIRST_NAME = "First Name"
HEADER_LAST_NAME = "Last Name"
HEADER_EMAIL = "Email Address"
HEADER_PHONE = "Phone Number"
HEADER_AGE = "Age (on October 24, 2026)"
HEADER_UNIVERSITY = "University"
HEADER_DEGREE = "Current Degree Program / Level of Study"
HEADER_COUNTRY = "Current Country of Residence"

REQUIRED_HEADERS = {
    HEADER_TIMESTAMP,
    HEADER_FIRST_NAME,
    HEADER_LAST_NAME,
    HEADER_EMAIL,
    HEADER_PHONE,
    HEADER_AGE,
    HEADER_UNIVERSITY,
    HEADER_DEGREE,
    HEADER_COUNTRY,
}

CONSENT_HEADER_PREFIXES = {
    "attendance_commitment": "I commit to attending DuQuantum 2026",
    "photo_release_consent": "I consent to being photographed",
    "mlh_code_of_conduct_consent": "I have read and agree to the MLH Code of Conduct",
    "data_sharing_consent": "I authorize you to share my application/registration information",
    "mlh_marketing_opt_in": "I authorize MLH + DEV to send me occasional emails",
}

REQUIRED_TRUE_CONSENTS = {
    "attendance_commitment",
    "photo_release_consent",
    "mlh_code_of_conduct_consent",
    "data_sharing_consent",
}

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
TRUE_ANSWERS = {"yes", "y", "true", "1", "agree", "i agree", "i consent"}
FALSE_ANSWERS = {
    "no",
    "n",
    "false",
    "0",
    "disagree",
    "i disagree",
    "i do not agree",
    "i do not consent",
    "decline",
    "opt out",
}
TIMESTAMP_FORMATS = (
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %I:%M %p",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
)
FORM_TIMEZONE = ZoneInfo("America/New_York")


class ImportValidationError(ValueError):
    """A validation failure whose message is safe to print without PII."""


@dataclass(frozen=True)
class ParsedRegistration:
    row_number: int
    submitted_at: datetime
    email: str
    normalized_email: str
    first_name: str
    last_name: str
    phone: str
    age: int
    university: str
    degree_program: str
    country: str
    attendance_commitment: bool
    photo_release_consent: bool
    mlh_code_of_conduct_consent: bool
    data_sharing_consent: bool
    mlh_marketing_opt_in: bool
    source_data: dict[str, Any]
    source_record_id: str


@dataclass(frozen=True)
class ParseResult:
    raw_rows: int
    registrations: tuple[ParsedRegistration, ...]
    duplicate_groups: int
    superseded_rows: int
    invalid_reasons: Mapping[str, int]
    ineligible_reasons: Mapping[str, int]

    @property
    def invalid_rows(self) -> int:
        return sum(self.invalid_reasons.values())

    @property
    def ineligible_rows(self) -> int:
        return sum(self.ineligible_reasons.values())


def normalize_email(value: str) -> str:
    """Normalize for comparison without provider-specific address rewriting."""

    return value.strip().casefold()


def parse_timestamp(value: str) -> datetime:
    raw = value.strip()
    for format_string in TIMESTAMP_FORMATS:
        try:
            parsed = datetime.strptime(raw, format_string)
            if parsed.tzinfo is None:
                # Google Forms exports in the form owner's local time.
                return parsed.replace(tzinfo=FORM_TIMEZONE).astimezone(timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue
    raise ImportValidationError("unrecognized timestamp")


def parse_consent(value: str) -> bool:
    normalized = " ".join(value.strip().casefold().split())
    if not normalized:
        raise ImportValidationError("blank consent response")
    if normalized in FALSE_ANSWERS:
        return False
    if normalized in TRUE_ANSWERS:
        return True
    if any(
        phrase in normalized
        for phrase in (
            "do not agree",
            "do not consent",
            "do not authorize",
            "don't agree",
            "don't consent",
            "don't authorize",
            "opt out",
            "not comfortable",
        )
    ):
        return False
    if normalized.startswith(("no ", "no,", "decline", "disagree")):
        return False
    # Google Forms checkbox answers often repeat the full affirmative option
    # text rather than a simple "yes". Once explicit negative forms have been
    # rejected, a nonblank selected option is affirmative.
    return True


def _find_consent_headers(headers: Iterable[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for field_name, prefix in CONSENT_HEADER_PREFIXES.items():
        matches = [header for header in headers if header.startswith(prefix)]
        if len(matches) != 1:
            raise ImportValidationError(f"missing or ambiguous {field_name} column")
        mapping[field_name] = matches[0]
    return mapping


def _required_text(row: Mapping[str, str], header: str) -> str:
    value = (row.get(header) or "").strip()
    if not value:
        raise ImportValidationError(f"blank {header}")
    return value


def _source_record_id(normalized_email: str, submitted_at: datetime) -> str:
    source_key = f"{EVENT_SLUG}\0{normalized_email}\0{submitted_at.isoformat()}"
    return hashlib.sha256(source_key.encode("utf-8")).hexdigest()


def parse_age(value: str) -> int:
    """Accept a plain integer or the first plausible age in free-form text."""

    raw = value.strip()
    try:
        age = int(raw)
    except ValueError:
        age = next(
            (
                int(candidate)
                for candidate in re.findall(r"\b\d{1,3}\b", raw)
                if 13 <= int(candidate) <= 120
            ),
            -1,
        )
    if not 13 <= age <= 120:
        raise ImportValidationError("age is outside allowed range")
    return age


def parse_row(
    row: Mapping[str, str],
    *,
    row_number: int,
    consent_headers: Mapping[str, str],
    source_sha256: str,
) -> ParsedRegistration:
    submitted_at = parse_timestamp(_required_text(row, HEADER_TIMESTAMP))
    email = _required_text(row, HEADER_EMAIL)
    normalized_email = normalize_email(email)
    if not EMAIL_PATTERN.fullmatch(normalized_email):
        raise ImportValidationError("invalid email format")

    age = parse_age(_required_text(row, HEADER_AGE))

    consents = {
        field_name: parse_consent(row.get(header, ""))
        for field_name, header in consent_headers.items()
    }
    # Exact question/answer pairs are deliberately retained for auditability.
    # This object is private PII and must never be emitted to application logs.
    source_data = {
        "form_response": dict(row),
        "consents": consents,
        "_import": {
            "event_slug": EVENT_SLUG,
            "submitted_at": submitted_at.isoformat(),
            "source_sha256": source_sha256,
            "source_row_number": row_number,
        },
    }

    return ParsedRegistration(
        row_number=row_number,
        submitted_at=submitted_at,
        email=email.strip(),
        normalized_email=normalized_email,
        first_name=_required_text(row, HEADER_FIRST_NAME),
        last_name=_required_text(row, HEADER_LAST_NAME),
        phone=_required_text(row, HEADER_PHONE),
        age=age,
        university=_required_text(row, HEADER_UNIVERSITY),
        degree_program=_required_text(row, HEADER_DEGREE),
        country=_required_text(row, HEADER_COUNTRY),
        attendance_commitment=consents["attendance_commitment"],
        photo_release_consent=consents["photo_release_consent"],
        mlh_code_of_conduct_consent=consents["mlh_code_of_conduct_consent"],
        data_sharing_consent=consents["data_sharing_consent"],
        mlh_marketing_opt_in=consents["mlh_marketing_opt_in"],
        source_data=source_data,
        source_record_id=_source_record_id(normalized_email, submitted_at),
    )


def parse_csv(path: Path) -> ParseResult:
    source_bytes = path.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    invalid_reasons: Counter[str] = Counter()
    latest_by_email: dict[str, ParsedRegistration] = {}
    seen_counts: Counter[str] = Counter()
    raw_rows = 0

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        headers = reader.fieldnames or []
        missing = REQUIRED_HEADERS.difference(headers)
        if missing:
            raise ImportValidationError(
                f"CSV is missing {len(missing)} required column(s)"
            )
        consent_headers = _find_consent_headers(headers)

        for row_number, row in enumerate(reader, start=2):
            raw_rows += 1
            try:
                registration = parse_row(
                    row,
                    row_number=row_number,
                    consent_headers=consent_headers,
                    source_sha256=source_sha256,
                )
            except ImportValidationError as exc:
                invalid_reasons[str(exc)] += 1
                continue

            seen_counts[registration.normalized_email] += 1
            current = latest_by_email.get(registration.normalized_email)
            if current is None or (
                registration.submitted_at,
                registration.row_number,
            ) > (current.submitted_at, current.row_number):
                latest_by_email[registration.normalized_email] = registration

    duplicate_groups = sum(1 for count in seen_counts.values() if count > 1)
    superseded_rows = sum(count - 1 for count in seen_counts.values() if count > 1)
    ineligible_reasons: Counter[str] = Counter()
    eligible: list[ParsedRegistration] = []
    for registration in latest_by_email.values():
        missing_required = sorted(
            name for name in REQUIRED_TRUE_CONSENTS if not getattr(registration, name)
        )
        if missing_required:
            reason = "latest response declined: " + ", ".join(missing_required)
            ineligible_reasons[reason] += 1
            continue
        eligible.append(registration)
    registrations = tuple(sorted(eligible, key=lambda item: item.normalized_email))
    return ParseResult(
        raw_rows=raw_rows,
        registrations=registrations,
        duplicate_groups=duplicate_groups,
        superseded_rows=superseded_rows,
        invalid_reasons=dict(invalid_reasons),
        ineligible_reasons=dict(ineligible_reasons),
    )


def _existing_submitted_at(source_data: Any) -> datetime | None:
    if not isinstance(source_data, dict):
        return None
    metadata = source_data.get("_import")
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("submitted_at")
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _registration_values(item: ParsedRegistration) -> dict[str, Any]:
    return {
        "email": item.email,
        "normalized_email": item.normalized_email,
        "first_name": item.first_name,
        "last_name": item.last_name,
        "phone": item.phone,
        "age": item.age,
        "university": item.university,
        "degree_program": item.degree_program,
        "country": item.country,
        "admission_status": "accepted",
        "rsvp_status": "confirmed",
        "source": "google_forms_csv",
        "source_record_id": item.source_record_id,
        "source_data": item.source_data,
        "attendance_commitment": item.attendance_commitment,
        "photo_release_consent": item.photo_release_consent,
        "mlh_code_of_conduct_consent": item.mlh_code_of_conduct_consent,
        "data_sharing_consent": item.data_sharing_consent,
        "mlh_privacy_policy_consent": item.data_sharing_consent,
        "mlh_marketing_opt_in": item.mlh_marketing_opt_in,
    }


def sync_database(
    registrations: Iterable[ParsedRegistration], *, commit: bool
) -> Counter[str]:
    # Imports stay inside this function so offline validation remains usable on
    # an operator laptop without a configured database.
    from db import get_local_session
    from models import Event, EventRegistration

    counts: Counter[str] = Counter()
    session = get_local_session()
    try:
        event = session.query(Event).filter(Event.slug == EVENT_SLUG).one_or_none()
        if event is None:
            raise RuntimeError(
                "DuQuantum event seed is missing; apply the event migration first"
            )

        for item in registrations:
            existing = (
                session.query(EventRegistration)
                .filter(
                    EventRegistration.event_id == event.id,
                    EventRegistration.normalized_email == item.normalized_email,
                )
                .one_or_none()
            )
            if existing is not None:
                prior_timestamp = _existing_submitted_at(existing.source_data)
                if prior_timestamp is not None and prior_timestamp > item.submitted_at:
                    counts["newer_existing"] += 1
                    continue
                for key, value in _registration_values(item).items():
                    setattr(existing, key, value)
                counts["updated"] += 1
            else:
                session.add(
                    EventRegistration(event_id=event.id, **_registration_values(item))
                )
                counts["created"] += 1

        if commit:
            session.commit()
        else:
            session.rollback()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return counts


def _print_summary(result: ParseResult, db_counts: Mapping[str, int] | None) -> None:
    print(f"Rows read: {result.raw_rows}")
    print(f"Unique valid registrations: {len(result.registrations)}")
    print(f"Duplicate email groups: {result.duplicate_groups}")
    print(f"Older duplicate rows ignored: {result.superseded_rows}")
    print(f"Invalid rows: {result.invalid_rows}")
    for reason, count in sorted(result.invalid_reasons.items()):
        print(f"  {reason}: {count}")
    print(f"Latest responses excluded as ineligible: {result.ineligible_rows}")
    for reason, count in sorted(result.ineligible_reasons.items()):
        print(f"  {reason}: {count}")
    if db_counts is not None:
        print(f"Database creates: {db_counts.get('created', 0)}")
        print(f"Database updates: {db_counts.get('updated', 0)}")
        print(
            f"Skipped because database row is newer: {db_counts.get('newer_existing', 0)}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--database-check",
        action="store_true",
        help="compare with the database and roll back; still makes no changes",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="write the validated import to the database",
    )
    parser.add_argument(
        "--confirm-event",
        help=f"required with --commit; must equal {EVENT_SLUG}",
    )
    parser.add_argument("--expect-rows", type=int)
    parser.add_argument("--expect-eligible", type=int)
    parser.add_argument("--expect-ineligible", type=int)
    parser.add_argument("--expect-duplicate-groups", type=int)
    parser.add_argument("--expect-superseded", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.commit and args.confirm_event != EVENT_SLUG:
        print(f"Refusing commit: pass --confirm-event {EVENT_SLUG}")
        return 2
    if not args.input.is_file():
        print("Input CSV does not exist or is not a regular file")
        return 2

    try:
        result = parse_csv(args.input)
    except (OSError, csv.Error, ImportValidationError) as exc:
        # Validation errors are designed not to contain row values.
        print(f"Validation failed: {exc}")
        return 2

    expected_counts = {
        "rows": (args.expect_rows, result.raw_rows),
        "eligible": (args.expect_eligible, len(result.registrations)),
        "ineligible": (args.expect_ineligible, result.ineligible_rows),
        "duplicate groups": (
            args.expect_duplicate_groups,
            result.duplicate_groups,
        ),
        "superseded rows": (args.expect_superseded, result.superseded_rows),
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

    db_counts: Counter[str] | None = None
    if result.invalid_rows and args.commit:
        _print_summary(result, None)
        print("Refusing commit while invalid rows are present")
        return 2

    if args.commit or args.database_check:
        try:
            db_counts = sync_database(result.registrations, commit=args.commit)
        except Exception as exc:
            # Do not stringify database exceptions: parameterized statements can
            # include attendee PII in their exception representation.
            print(
                f"Database operation failed ({type(exc).__name__}); transaction rolled back"
            )
            return 1

    _print_summary(result, db_counts)
    print(
        "Import committed" if args.commit else "Dry run only; no database changes made"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
