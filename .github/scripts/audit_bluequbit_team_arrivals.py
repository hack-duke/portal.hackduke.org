"""Read-only team availability audit; output source row references, not emails."""
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
        arrivals = {row.registration_id: row.checked_in_at.isoformat() for row in session.query(EventCheckIn).filter_by(event_id=event.id, checkpoint="arrival")}
        teams = session.query(EventTeam).filter_by(event_id=event.id, active=True).all()
        result = []
        for team in sorted(teams, key=lambda t: int(t.team_number)):
            members = []
            for member in session.query(EventTeamMember).filter_by(team_id=team.id).order_by(EventTeamMember.member_position):
                registration = session.query(EventRegistration).filter_by(id=member.registration_id).one_or_none() if member.registration_id else None
                if registration is None:
                    raise ValueError("Unlinked member needs review")
                source_row = (registration.source_data or {}).get("final_master_confirmation", {}).get("master_row")
                if source_row is None:
                    raise ValueError("Member lacks master source reference")
                members.append({"master_row": source_row, "arrival_at": arrivals.get(registration.id), "rsvp": registration.rsvp_status})
            checked_in = sum(m["arrival_at"] is not None for m in members)
            if checked_in == 3:
                result.append({"number": team.team_number, "name": team.name, "track": team.assigned_track, "challenge": team.assigned_challenge, "members": members, "checked_in": checked_in})
        print("TEAM_AVAILABILITY " + json.dumps({"as_of_utc": datetime.now(timezone.utc).isoformat(), "checkpoint": "arrival", "teams": result}), flush=True)
    finally:
        session.rollback()
        session.close()


if __name__ == "__main__":
    main()
