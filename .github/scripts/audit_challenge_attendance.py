"""Read-only challenge attendance totals from current assignments and arrivals."""
import json
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import text
from db import get_local_session
from models import Event, EventTeam, EventTeamMember, EventCheckIn


def main():
    session = get_local_session()
    try:
        session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        event = session.query(Event).filter_by(slug="duquantum-2026").one()
        arrivals = {r.registration_id for r in session.query(EventCheckIn).filter_by(event_id=event.id, checkpoint="arrival")}
        groups = defaultdict(lambda: {"assigned_teams": 0, "represented_teams": 0, "checked_in_people": 0, "assigned_people": 0})
        assigned_arrivals = set()
        for team in session.query(EventTeam).filter_by(event_id=event.id, active=True):
            members = {r.registration_id for r in session.query(EventTeamMember).filter_by(team_id=team.id) if r.registration_id is not None}
            present = members & arrivals
            assigned_arrivals.update(present)
            group = groups[(team.assigned_challenge or "Unassigned", team.assigned_track or "Unassigned")]
            group["assigned_teams"] += 1
            group["represented_teams"] += bool(present)
            group["checked_in_people"] += len(present)
            group["assigned_people"] += len(members)
        output = {"as_of_utc": datetime.now(timezone.utc).isoformat(), "checkpoint": "arrival", "total_checked_in": len(arrivals), "checked_in_without_active_team": len(arrivals - assigned_arrivals), "groups": [{"challenge": key[0], "track": key[1], **value} for key, value in sorted(groups.items())]}
        assert sum(g["checked_in_people"] for g in output["groups"]) == len(assigned_arrivals)
        print("CHALLENGE_ATTENDANCE " + json.dumps(output), flush=True)
    finally:
        session.rollback()
        session.close()


if __name__ == "__main__":
    main()
