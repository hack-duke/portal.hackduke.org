"""Read-only organizer roster; excludes credentials and pass capabilities."""
import json
from collections import Counter
from datetime import datetime, timezone
from sqlalchemy import text
from db import get_local_session
from models import Event, EventRegistration


def main():
    session = get_local_session()
    try:
        session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        event = session.query(Event).filter_by(slug="duquantum-2026").one()
        people, counts = [], Counter()
        fields = ("email", "first_name", "last_name", "preferred_name", "phone", "age", "university", "degree_program", "country", "attendance_commitment", "photo_release_consent", "mlh_code_of_conduct_consent", "mlh_privacy_policy_consent", "data_sharing_consent", "mlh_marketing_opt_in", "admission_status", "rsvp_status", "claimed_at", "created_at", "updated_at")
        for row in session.query(EventRegistration).filter_by(event_id=event.id):
            source = row.source_data or {}
            if source.get("final_master_duplicate_of") or source.get("superseded_test_invitation_at"):
                counts["archived_aliases_excluded"] += 1
                continue
            arrival = next((c for c in row.check_ins if c.checkpoint == "arrival"), None)
            connected = row.user_id is not None or row.claimed_at is not None
            setup = row.account_setup
            password_done = setup is not None and setup.consumed_at is not None
            complete = connected or password_done
            eligible = row.admission_status == "accepted" and row.rsvp_status == "confirmed"
            if not arrival and not (eligible and complete):
                counts["not_in_final_roster"] += 1
                continue
            person = {field: getattr(row, field) for field in fields}
            person.update(registration_id=str(row.id), checked_in=arrival is not None, arrival_at=arrival.checked_in_at if arrival else None, portal_connected=connected, password_setup_completed=password_done, password_setup_at=setup.consumed_at if password_done else None, account_completed=complete, inclusion_basis="Checked in and account completed" if arrival and complete else "Checked in only" if arrival else "Account completed; attendance unverified", checkpoints=[{"checkpoint": c.checkpoint, "at": c.checked_in_at} for c in row.check_ins], login_email=row.user.email if row.user else None, form_response=source.get("form_response", {}), organizer_note="Withdrawn by organizer" if source.get("organizer_withdrawal") else "Team moved by organizer" if source.get("organizer_team_override") else "", source=row.source)
            member = row.team_membership
            team = member.team if member and member.team.active else None
            person["team"] = {field: getattr(team, field) for field in ("team_number", "name", "assigned_track", "assigned_challenge", "sponsor_name", "sponsor_contact_name", "sponsor_contact_email")} if team else None
            person["discord"] = member.discord_username if member else None
            person["pass_status"] = row.event_pass.state if row.event_pass else "Not issued"
            deliveries = sorted(row.email_deliveries, key=lambda d: d.created_at, reverse=True)
            sent = [d for d in deliveries if d.status == "sent"]
            person["emails_sent"] = len(sent)
            person["last_email_sent_at"] = max((d.sent_at for d in sent if d.sent_at), default=None)
            person["latest_email_status"] = deliveries[0].status if deliveries else "Not sent"
            people.append(person)
            counts["checked_in"] += bool(arrival)
            counts["account_completed"] += complete
            counts["portal_connected"] += connected
            counts["account_only"] += complete and not arrival
            counts["checkin_only"] += bool(arrival) and not complete
            counts["both"] += bool(arrival) and complete
        people.sort(key=lambda p: ((p["last_name"] or "").casefold(), (p["first_name"] or "").casefold(), p["email"].casefold()))
        assert len({p["email"].casefold() for p in people}) == len(people)
        assert len(people) == counts["both"] + counts["account_only"] + counts["checkin_only"]
        print(json.dumps({"event": event.slug, "as_of_utc": datetime.now(timezone.utc), "counts": dict(counts), "people": people}, default=lambda v: v.isoformat() if isinstance(v, datetime) else str(v)))
    finally:
        session.rollback()
        session.close()


if __name__ == "__main__":
    main()
