"""Export confirmed arrivals and current teams for the organizer workbook."""
import json
from datetime import datetime, timezone
from sqlalchemy import text
from db import get_local_session
from models import Event, EventRegistration, EventTeam, EventTeamMember, EventCheckIn


def main():
    session = get_local_session()
    try:
        session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        event = session.query(Event).filter_by(slug="duquantum-2026").one()
        arrival_ids = {r.registration_id for r in session.query(EventCheckIn).filter_by(event_id=event.id, checkpoint="arrival")}
        confirmed = {r.id: r for r in session.query(EventRegistration).filter_by(event_id=event.id, admission_status="accepted", rsvp_status="confirmed") if r.id in arrival_ids}
        def person(row):
            return {"registration_id": str(row.id), "name": " ".join(p for p in (row.first_name, row.last_name) if p).strip(), "email": row.email}
        teams, assigned = [], set()
        for team in session.query(EventTeam).filter_by(event_id=event.id, active=True):
            members = session.query(EventTeamMember).filter_by(team_id=team.id).order_by(EventTeamMember.member_position).all()
            present = [person(confirmed[m.registration_id]) for m in members if m.registration_id in confirmed]
            if not present:
                continue
            assigned.update(m.registration_id for m in members if m.registration_id in confirmed)
            teams.append({"number": team.team_number, "name": team.name, "track": team.assigned_track, "challenge": team.assigned_challenge or "Unassigned", "participants": present})
        teams.sort(key=lambda t: int(t["number"]))
        unassigned = [person(r) for rid, r in confirmed.items() if rid not in assigned]
        assert sum(len(t["participants"]) for t in teams) + len(unassigned) == len(confirmed)
        print(json.dumps({"event": event.slug, "as_of_utc": datetime.now(timezone.utc).isoformat(), "attendance_rule": "Accepted and RSVP-confirmed registration with an arrival check-in", "total_arrival_checkins": len(arrival_ids), "total_confirmed_arrivals": len(confirmed), "excluded_unconfirmed_arrivals": len(arrival_ids - set(confirmed)), "teams": teams, "unassigned": unassigned}))
    finally:
        session.rollback()
        session.close()


if __name__ == "__main__":
    main()
