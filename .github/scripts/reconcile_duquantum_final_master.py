"""Reconcile the confirmed master roster, accounts, teams and a scoped reminder.

Private source data arrives only over stdin. Console output is aggregate only.
Every write phase requires the exact inventory fingerprint and count.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

EVENT = "duquantum-2026"
BATCH = "auth0-invitation-final-master-20261024"
TEAM_SHA = "e27d4b99e3ab5527fbd34990b7335750a3dad5dc9c7022117c4b918a6a926ca7"
PROFILE_SHA = "ecfe7d36446e226915fe280c126b5230a74762ef11f4c903b86f302b2335c4e7"
REPORTED = ("speri0915@gmail.com", "zirui.xu.1@vanderbilt.edu", "darren.lau@yale.edu")


def norm(value):
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).casefold().split())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def emit(label, value):
    print(label, json.dumps(value, default=str, sort_keys=True), flush=True)


def consent(value):
    if value is None or str(value).strip() == "":
        return None
    return norm(value) in {"i agree", "yes", "true", "i consent"}


def prepare(team_path, profile_path):
    from openpyxl import load_workbook
    if hashlib.sha256(Path(team_path).read_bytes()).hexdigest() != TEAM_SHA:
        raise ValueError("Unexpected final-teams source hash")
    if hashlib.sha256(Path(profile_path).read_bytes()).hexdigest() != PROFILE_SHA:
        raise ValueError("Unexpected attendance source hash")
    source = load_workbook(team_path, read_only=True, data_only=True)
    profiles = load_workbook(profile_path, read_only=True, data_only=True)
    try:
        def rows(book, sheet):
            iterator = book[sheet].iter_rows(values_only=True)
            headers = next(iterator)
            return [(n, dict(zip(headers, row))) for n, row in enumerate(iterator, 2) if any(v not in (None, "") for v in row)]
        master = []
        ignored = 0
        for row_number, row in rows(source, "Master List"):
            if not row.get("Member Name") and not row.get("Email"):
                ignored += 1
                continue
            if not row.get("Member Name") or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", norm(row.get("Email"))):
                raise ValueError(f"Invalid attendee at master row {row_number}")
            row["_row"] = row_number
            master.append(row)
        profile_rows = [row for _, row in rows(profiles, "Master List") if row.get("Email")]
        payload = {"event": EVENT, "team_sha": TEAM_SHA, "profile_sha": PROFILE_SHA, "master": master, "profiles": profile_rows, "ignored_notes_rows": ignored}
        validate_payload(payload)
        return payload
    finally:
        source.close()
        profiles.close()


def validate_payload(payload):
    if payload.get("event") != EVENT or payload.get("team_sha") != TEAM_SHA or payload.get("profile_sha") != PROFILE_SHA:
        raise ValueError("Source identity mismatch")
    master = payload["master"]
    if len(master) != 219:
        raise ValueError("Final master must contain exactly 219 attendees")
    for field in ("Email", "Member Name"):
        if len({norm(row[field]) for row in master}) != len(master):
            raise ValueError(f"Duplicate master {field}")
    groups = defaultdict(list)
    for row in master:
        number = float(row["Team #"])
        if not number.is_integer() or number < 1:
            raise ValueError("Invalid team number")
        groups[str(int(number))].append(row)
    if len(groups) != 61 or max(map(len, groups.values())) != 6:
        raise ValueError("Unexpected team counts")
    for rows in groups.values():
        for field in ("Team Name", "Track", "Assigned Challenge", "Team Source"):
            if len({str(row.get(field) or "").strip() for row in rows}) != 1:
                raise ValueError(f"Conflicting Master List {field}")
    if len({norm(rows[0]["Team Name"]) for rows in groups.values()}) != len(groups):
        raise ValueError("Duplicate final team names")
    return groups


def people(payload):
    from scripts.import_event_registrations import parse_age
    by_email, by_name = defaultdict(list), defaultdict(list)
    for profile in payload["profiles"]:
        by_email[norm(profile["Email"])].append(profile)
        by_name[norm(f"{profile.get('First Name') or ''} {profile.get('Last Name') or ''}")].append(profile)
    result = []
    for row in payload["master"]:
        email, name = norm(row["Email"]), norm(row["Member Name"])
        candidates = by_email[email] or by_name[name]
        profile = candidates[0] if len(candidates) == 1 else {}
        aliases = {email}
        if profile:
            aliases.add(norm(profile["Email"]))
            aliases.update(re.findall(r"[^\s,;<>]+@[^\s,;<>]+\.[^\s,;<>]+", norm(profile.get("Other Emails on Record"))))
        parts = str(row["Member Name"]).strip().split(maxsplit=1)
        first = profile.get("First Name") or parts[0]
        last = profile.get("Last Name") or (parts[1] if len(parts) > 1 else "")
        fields = {"first_name": first, "last_name": last, "university": row.get("University") or profile.get("University"), "degree_program": row.get("Degree Level") or profile.get("Degree / Level"), "attendance_commitment": True}
        for key, field in (("phone", "Phone"), ("age", "Age (Oct 24, 2026)"), ("country", "Country of Residence")):
            value = profile.get(field)
            if value is not None:
                fields[key] = parse_age(str(value)) if key == "age" else str(int(value)) if key == "phone" and isinstance(value, float) else str(value)
        for key, field in (("photo_release_consent", "Photo Consent"), ("mlh_code_of_conduct_consent", "MLH Code of Conduct"), ("data_sharing_consent", "MLH Data Sharing"), ("mlh_marketing_opt_in", "MLH Emails")):
            value = consent(profile.get(field))
            if value is not None:
                fields[key] = value
        result.append({"row": row["_row"], "email": email, "aliases": sorted(aliases), "names": {name, norm(f"{first} {last}")}, "fields": fields})
    return result


def pick_registration(person, registrations):
    candidates = [row for row in registrations if row.normalized_email in person["aliases"] and not (row.source_data or {}).get("superseded_test_invitation_at") and not (row.source_data or {}).get("final_master_duplicate_of")]
    def select(rows):
        connected = [row for row in rows if row.user_id is not None or row.claimed_at is not None]
        active = [row for row in rows if row.admission_status == "accepted" and row.rsvp_status == "confirmed"]
        direct = [row for row in rows if row.normalized_email == person["email"]]
        for group in (connected, active, direct, rows):
            if len(group) == 1:
                return group[0]
            if len(group) > 1 and group is connected:
                if len(direct) == 1 and all(norm(f"{row.first_name or ''} {row.last_name or ''}") in person["names"] for row in connected):
                    return direct[0]
                raise ValueError("Multiple claimed registrations match one master attendee")
        if rows:
            raise ValueError("Ambiguous registration aliases")
        return None
    if candidates:
        return select(candidates)
    names = [row for row in registrations if norm(f"{row.first_name or ''} {row.last_name or ''}") in person["names"] and not (row.source_data or {}).get("superseded_test_invitation_at") and not (row.source_data or {}).get("final_master_duplicate_of")]
    return select(names)


def registration_plan(payload, session, event):
    from models import EventRegistration
    registrations = session.query(EventRegistration).filter_by(event_id=event.id).all()
    plan = []
    for person in people(payload):
        try:
            registration = pick_registration(person, registrations)
        except ValueError as error:
            emit("REGISTRATION_CONFLICT", {"master_row": person["row"], "reason": str(error)})
            raise
        person["duplicates"] = [other for other in registrations if registration is not None and other.id != registration.id and other.normalized_email in person["aliases"] and norm(f"{other.first_name or ''} {other.last_name or ''}") in person["names"] and not (other.source_data or {}).get("final_master_duplicate_of")]
        plan.append((person, registration))
    ids = [str(row.id) for _, row in plan if row is not None]
    if len(set(ids)) != len(ids):
        raise ValueError("Two master attendees resolve to the same registration")
    canonical = [row.normalized_email if row is not None else person["email"] for person, row in plan]
    if len(set(canonical)) != len(canonical):
        raise ValueError("Duplicate canonical login emails")
    fingerprint = digest([(person["row"], str(row.id) if row is not None else None, canonical[i], person["fields"], sorted(str(other.id) for other in person["duplicates"])) for i, (person, row) in enumerate(plan)])
    emit("ROSTER_PLAN", {"attendees": len(plan), "new": sum(row is None for _, row in plan), "restore": sum(row is not None and (row.admission_status != "accepted" or row.rsvp_status != "confirmed") for _, row in plan), "duplicate_alias_registrations": sum(len(person["duplicates"]) for person, _ in plan), "login_aliases_preserved": sum(row is not None and row.normalized_email != person["email"] for person, row in plan), "fingerprint": fingerprint})
    return plan, fingerprint


def build_teams(payload):
    from scripts.import_event_teams import ParsedTeam, ParsedTeamMember, TeamParseResult, normalize_text, _additional_teammates, _source_record_id
    groups = validate_payload(payload)
    teams = []
    for number, rows in sorted(groups.items(), key=lambda item: int(item[0])):
        first = rows[0]
        name = str(first["Team Name"]).strip()
        requested, detail = _additional_teammates(first.get("Additional Members Requested (original team)"))
        members = tuple(ParsedTeamMember(row_number=row["_row"], position=i, display_name=str(row["Member Name"]).strip(), email=norm(row["Email"]), normalized_email=norm(row["Email"]), discord_username=str(row.get("Discord") or "").strip() or None, normalized_name=normalize_text(row["Member Name"])) for i, row in enumerate(rows, 1))
        prefs = tuple(str(first[f"Pref {i}"]).strip() for i in range(1, 7) if first.get(f"Pref {i}"))
        teams.append(ParsedTeam(row_number=first["_row"], team_number=number, name=name, normalized_name=normalize_text(name), assigned_track=str(first["Track"]).strip(), assigned_challenge=str(first["Assigned Challenge"]).strip(), formation_source=str(first["Team Source"]).strip(), requested_additional_teammates=requested, additional_teammates_detail=detail, challenge_preferences=prefs, members=members, source_record_id=_source_record_id(number, normalize_text(name))))
    return TeamParseResult(source_sha256=TEAM_SHA, master_rows=219, team_rows=len(teams), teams=tuple(teams))


def backup(session, event, path):
    from models import EventRegistration, EventTeam, EventTeamMember
    if not path:
        raise ValueError("Private backup path is required")
    data = {}
    for model in (EventRegistration, EventTeam, EventTeamMember):
        data[model.__tablename__] = [{column.name: getattr(row, column.name) for column in model.__table__.columns} for row in session.query(model).filter_by(event_id=event.id).all()]
    Path(path).write_text(json.dumps(data, default=str), encoding="utf-8")
    Path(path).chmod(0o600)


def account_inventory(plan, auth0, auth_settings, session):
    from scripts.onboard_event_auth0 import database_users
    from models import User
    result, errors, ambiguous, mismatch = [], 0, 0, 0
    for person, row in plan:
        try:
            users = database_users(auth0.find_users_by_email(row.normalized_email), auth_settings.database_connection)
        except Exception:
            errors += 1
            continue
        if len(users) > 1:
            ambiguous += 1
            continue
        user = users[0] if users else None
        if row.user_id is not None:
            linked = session.query(User).filter_by(id=row.user_id).one()
            if user is None or linked.auth0_id != user["user_id"]:
                mismatch += 1
        result.append((person, row, user))
    fingerprint = digest([(person["row"], str(row.id), row.normalized_email, user["user_id"] if user else None) for person, row, user in result])
    summary = {"total": len(plan), "existing": sum(user is not None for _, _, user in result), "missing": sum(user is None for _, _, user in result), "lookup_errors": errors, "ambiguous": ambiguous, "linked_identity_mismatches": mismatch, "fingerprint": fingerprint}
    emit("ACCOUNT_PLAN", summary)
    if errors or ambiguous or mismatch:
        raise ValueError("Account inventory has blockers; no account or email changes made")
    return result, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--team-workbook")
    parser.add_argument("--attendance-workbook")
    parser.add_argument("--phase", choices=("inventory", "roster", "accounts", "teams", "reminders", "verify"))
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--expected-fingerprint")
    parser.add_argument("--backup")
    args = parser.parse_args()
    if args.prepare:
        payload = prepare(args.team_workbook, args.attendance_workbook)
        encoded = base64.b64encode(gzip.compress(json.dumps(payload, default=str).encode())).decode()
        if len(encoded) > 47000:
            raise ValueError("Protected payload exceeds one secret")
        print(encoded)
        return 0
    payload = json.load(sys.stdin)
    validate_payload(payload)
    from db import get_local_session
    from models import Event, EventRegistration, EmailDelivery
    from services.auth0_onboarding import Auth0OnboardingClient, Auth0OnboardingSettings
    from services.event_email_campaign import SesSettings, SesEmailSender, render_campaign, CAMPAIGN_TEMPLATE_VERSIONS
    from services.account_setup import issue_account_setup_link
    from scripts.remind_event_accounts import validate_ses_delivery_posture, suppression_reason
    def confirm(count, fingerprint):
        if args.expected_count != count or args.expected_fingerprint != fingerprint:
            raise ValueError("Exact phase count or fingerprint changed; no changes made")
    session = get_local_session()
    try:
        event = session.query(Event).filter_by(slug=EVENT).one()
        plan, fingerprint = registration_plan(payload, session, event)
        if args.phase == "roster":
            confirm(len(plan), fingerprint)
            backup(session, event, args.backup)
            for person, row in plan:
                restoring = row is not None and row.admission_status != "accepted"
                if row is None:
                    row = EventRegistration(event_id=event.id, email=person["email"], normalized_email=person["email"], source="confirmed_final_master")
                    session.add(row)
                for key, value in person["fields"].items():
                    setattr(row, key, value)
                row.admission_status, row.rsvp_status = "accepted", "confirmed"
                row.source_data = {**(row.source_data or {}), "final_master_confirmation": {"team_sha256": TEAM_SHA, "attendance_sha256": PROFILE_SHA, "master_row": person["row"], "aliases": person["aliases"], "at": datetime.now(timezone.utc).isoformat()}}
                for duplicate in person["duplicates"]:
                    duplicate.admission_status, duplicate.rsvp_status = "revoked", "declined"
                    duplicate.source_data = {**(duplicate.source_data or {}), "final_master_duplicate_of": str(row.id)}
                    if duplicate.account_setup is not None:
                        duplicate.account_setup.expires_at = datetime.now(timezone.utc)
                    if duplicate.event_pass is not None:
                        duplicate.event_pass.state, duplicate.event_pass.revoked_at = "revoked", datetime.now(timezone.utc)
                if restoring and row.event_pass is not None and row.event_pass.state == "revoked":
                    row.event_pass.state, row.event_pass.revoked_at = "active", None
            session.commit()
            emit("ROSTER_COMMITTED", {"attendees": len(plan), "private_backup": True})
            return 0
        if any(row is None for _, row in plan):
            if args.phase == "inventory":
                return 0
            raise ValueError("Roster must be committed before subsequent phases")
        if any(row.admission_status != "accepted" or row.rsvp_status != "confirmed" for _, row in plan):
            if args.phase == "inventory":
                return 0
            raise ValueError("Master registrations are not all confirmed")
        team_result = build_teams(payload)
        team_fp = digest([asdict(team) for team in team_result.teams])
        emit("TEAM_PLAN", {"teams": len(team_result.teams), "members": team_result.member_rows, "largest_team": max(len(team.members) for team in team_result.teams), "fingerprint": team_fp})
        if args.phase == "teams":
            from scripts.import_event_teams import sync_database
            confirm(len(team_result.teams), team_fp)
            backup(session, event, args.backup)
            session.close()
            result = sync_database(team_result, commit=True, expected_match_counts={"matched": 219, "unmatched": 0, "ambiguous": 0})
            emit("TEAMS_COMMITTED", dict(result.counts))
            return 0
        source_by_row = {row["_row"]: row for row in payload["master"]}
        team_errors = 0
        for person, row in plan:
            member = row.team_membership
            expected = source_by_row[person["row"]]
            if member is None or member.match_status != "matched" or member.team is None or not member.team.active:
                team_errors += 1
            elif (member.team.team_number != str(int(expected["Team #"])) or member.team.name != str(expected["Team Name"]).strip() or member.team.assigned_track != str(expected["Track"]).strip() or member.team.assigned_challenge != str(expected["Assigned Challenge"]).strip()):
                team_errors += 1
        emit("TEAM_LINK_CHECK", {"correct": len(plan) - team_errors, "mismatches": team_errors})
        if args.phase in ("verify", "reminders") and team_errors:
            raise ValueError("Final team assignments must be published before reminders")
        settings = Auth0OnboardingSettings.from_environment()
        with Auth0OnboardingClient(settings) as auth0:
            accounts, account_summary = account_inventory(plan, auth0, settings, session)
            if args.phase == "accounts":
                confirm(account_summary["missing"], account_summary["fingerprint"])
                for _, row, user in accounts:
                    if user is None:
                        auth0.create_user(email=row.normalized_email, first_name=row.first_name or "", last_name=row.last_name or "")
                accounts, verified = account_inventory(plan, auth0, settings, session)
                if verified["missing"]:
                    raise ValueError("Not all Auth0 accounts were verified after provisioning")
                emit("ACCOUNTS_VERIFIED", {"unique_accounts": len(accounts), "created": account_summary["missing"], "missing": 0})
                return 0
            if account_summary["missing"]:
                if args.phase == "inventory":
                    return 0
                raise ValueError("All attendee accounts must exist before reminders")
            mail_settings = SesSettings.from_environment()
            mailer = SesEmailSender(mail_settings)
            emit("SES_POSTURE", validate_ses_delivery_posture(mailer.client, mail_settings))
            reminder_plan, counts = [], Counter()
            for person, row, user in accounts:
                recorded = session.query(EmailDelivery).filter_by(event_id=event.id, registration_id=row.id, campaign_key=BATCH).one_or_none()
                if recorded is not None and recorded.status in ("queued", "sent"):
                    counts["batch_" + recorded.status] += 1
                    continue
                if row.user_id is not None or row.claimed_at is not None:
                    counts["completed"] += 1
                    continue
                reason = suppression_reason(mailer.client, row.email)
                if reason:
                    counts["suppressed_" + reason] += 1
                    continue
                setup = user.get("email_verified") is not True
                template = "auth0-invitation-reminder" if setup else "auth0-invitation-existing-reminder"
                if setup and not any(item.status == "sent" for item in row.email_deliveries):
                    template = "auth0-invitation"
                reminder_plan.append((person, row, user, template, recorded))
                counts["setup" if setup else "signin"] += 1
            reminder_fp = digest([(person["row"], str(row.id), row.normalized_email, user["user_id"], template) for person, row, user, template, _ in reminder_plan])
            emit("REMINDER_PLAN", {**dict(counts), "recipients": len(reminder_plan), "fingerprint": reminder_fp})
            for index, email in enumerate(REPORTED, 1):
                found = [(person, row, user) for person, row, user in accounts if email in person["aliases"] or row.normalized_email == email]
                if len(found) != 1:
                    raise ValueError("Reported recipient is not uniquely reconciled")
                person, row, user = found[0]
                delivery = session.query(EmailDelivery).filter_by(event_id=event.id, registration_id=row.id, campaign_key=BATCH).one_or_none()
                emit("REPORTED", {"request": index, "master_row": person["row"], "registration_confirmed": True, "auth0_unique": True, "portal_connected": row.user_id is not None or row.claimed_at is not None, "batch_status": delivery.status if delivery else "not_sent", "suppression": suppression_reason(mailer.client, row.email)})
            if args.phase != "reminders":
                return 0
            confirm(len(reminder_plan), reminder_fp)
            failed = 0
            for person, row, user, template, delivery in reminder_plan:
                try:
                    setup_url = None
                    if template in ("auth0-invitation", "auth0-invitation-reminder"):
                        setup_url = issue_account_setup_link(session, event_id=event.id, event_slug=EVENT, registration_id=row.id, auth0_user_id=user["user_id"], portal_url=mail_settings.portal_url, ttl_seconds=settings.account_setup_ttl_seconds)
                    rendered = render_campaign(template, first_name=row.first_name or "Attendee", portal_url=mail_settings.portal_url, login_email=row.email, account_setup_url=setup_url)
                    if delivery is None:
                        delivery = EmailDelivery(event_id=event.id, registration_id=row.id, campaign_key=BATCH, recipient_email=row.email, template_version=CAMPAIGN_TEMPLATE_VERSIONS[template], status="queued")
                        session.add(delivery)
                    else:
                        delivery.status, delivery.error = "queued", None
                        delivery.template_version = CAMPAIGN_TEMPLATE_VERSIONS[template]
                    session.commit()
                    try:
                        message_id = mailer.send(recipient=row.email, rendered=rendered)
                    except Exception as error:
                        delivery.status, delivery.error = "failed", type(error).__name__
                        session.commit()
                        raise
                    delivery.status, delivery.provider_message_id, delivery.sent_at = "sent", message_id, datetime.now(timezone.utc)
                    session.commit()
                except Exception as error:
                    session.rollback()
                    failed += 1
                    emit("SEND_FAILED", {"master_row": person["row"], "error_type": type(error).__name__})
            emit("REMINDERS_SENT", {"accepted_by_ses": len(reminder_plan) - failed, "failed": failed})
            return 1 if failed else 0
    finally:
        session.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        # Runtime/database exception strings may contain source PII.
        emit("OPERATION_FAILED", {"type": type(error).__name__, "reason": str(error) if type(error) is ValueError else None})
        raise SystemExit(1)
