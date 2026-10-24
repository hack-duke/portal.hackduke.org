"""Move Vikas to Cameron's team at the organizer's request; no email."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func
from db import get_local_session
from models import Event, EventRegistration, EventTeam, EventTeamMember


def main():
    session = get_local_session()
    try:
        event = session.query(Event).filter_by(slug="duquantum-2026").one()
        attendee = session.query(EventRegistration).filter_by(event_id=event.id, normalized_email="vikas.thoutam@duke.edu").with_for_update().one()
        if attendee.admission_status != "accepted" or attendee.rsvp_status != "confirmed":
            raise ValueError("Attendee eligibility changed")
        target = session.query(EventTeam).filter_by(event_id=event.id, team_number="12", active=True).with_for_update().one()
        if (target.name, target.assigned_track, target.assigned_challenge) != ("DuQuanta", "Standard", "DQC"):
            raise ValueError("Target team changed")
        members = session.query(EventTeamMember).filter_by(team_id=target.id).all()
        if sum((m.display_name or "").strip().casefold() == "cameron silverman" for m in members) != 1:
            raise ValueError("Cameron is not uniquely assigned to the target team")
        member = session.query(EventTeamMember).filter_by(event_id=event.id, registration_id=attendee.id).with_for_update().one()
        old_team = session.query(EventTeam).filter_by(id=member.team_id).with_for_update().one()
        if member.team_id != target.id:
            if old_team.team_number != "14":
                raise ValueError("Current membership changed; review required")
            def record(row):
                return {col.name: getattr(row, col.name) for col in row.__table__.columns}
            backup = Path(os.environ["TEAM_CHANGE_BACKUP"])
            backup.write_text(json.dumps({"registration": record(attendee), "member": record(member), "old_team": record(old_team), "target_team": record(target)}, default=str))
            backup.chmod(0o600)
            member.member_position = (session.query(func.max(EventTeamMember.member_position)).filter_by(team_id=target.id).scalar() or 0) + 1
            member.team_id = target.id
            attendee.source_data = {**(attendee.source_data or {}), "organizer_team_override": {"team_number": "12", "previous_team_number": "14", "at": datetime.now(timezone.utc).isoformat(), "reason": "Organizer requested Vikas join Cameron Silverman on DuQuanta"}}
            session.commit()
        session.expire_all()
        verified = session.query(EventTeamMember).filter_by(event_id=event.id, registration_id=attendee.id).one()
        if verified.team_id != target.id:
            raise ValueError("Committed team assignment verification failed")
        print("TEAM_CHANGE " + json.dumps({"team": target.team_number, "name": target.name, "track": target.assigned_track, "challenge": target.assigned_challenge, "members": session.query(EventTeamMember).filter_by(team_id=target.id).count(), "verified": True, "emails_sent": 0}), flush=True)
    finally:
        session.rollback()
        session.close()


if __name__ == "__main__":
    main()
