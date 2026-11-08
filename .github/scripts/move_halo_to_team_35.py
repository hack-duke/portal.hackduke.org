"""Apply the organizer-requested Halo/Vinodhini replacement, without email."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from db import get_local_session
from models import Event, EventRegistration, EventTeam, EventTeamMember


def main():
    session = get_local_session()
    try:
        event = session.query(Event).filter_by(slug="duquantum-2026").one()
        halo = session.query(EventRegistration).filter_by(event_id=event.id, normalized_email="hxlokwok@gmail.com").with_for_update().one()
        vin = session.query(EventRegistration).filter_by(event_id=event.id, normalized_email="vr156@duke.edu").with_for_update().one()
        target = session.query(EventTeam).filter_by(event_id=event.id, team_number="35", active=True).with_for_update().one()
        if target.name != "Von Neumann's Ghost" or target.assigned_challenge != "Alice & Bob":
            raise ValueError("Target team does not match the organizer request")
        hm = session.query(EventTeamMember).filter_by(event_id=event.id, registration_id=halo.id).with_for_update().one()
        vm = session.query(EventTeamMember).filter_by(event_id=event.id, registration_id=vin.id).with_for_update().one_or_none()
        if hm.team_id == target.id and vm is None and vin.rsvp_status == "declined":
            print('TEAM_CHANGE {"already_applied": true}', flush=True)
            return
        old_team = session.query(EventTeam).filter_by(id=hm.team_id).with_for_update().one()
        if old_team.team_number != "60" or vm is None or vm.team_id != target.id:
            raise ValueError("Membership changed; review before applying")
        before = {str(t.id): session.query(EventTeamMember).filter_by(team_id=t.id).count() for t in (old_team, target)}
        def record(row):
            return {column.name: getattr(row, column.name) for column in row.__table__.columns}
        backup = Path(os.environ["TEAM_CHANGE_BACKUP"])
        backup.write_text(json.dumps({"registrations": [record(halo), record(vin)], "members": [record(hm), record(vm)], "teams": [record(old_team), record(target)]}, default=str))
        backup.chmod(0o600)
        position = vm.member_position
        session.delete(vm)
        session.flush()
        hm.team_id = target.id
        hm.member_position = position
        now = datetime.now(timezone.utc).isoformat()
        halo.source_data = {**(halo.source_data or {}), "organizer_team_override": {"team_number": "35", "previous_team_number": "60", "at": now, "reason": "Organizer requested replacement for withdrawn teammate"}}
        vin.rsvp_status = "declined"
        vin.attendance_commitment = False
        vin.source_data = {**(vin.source_data or {}), "organizer_withdrawal": {"at": now, "previous_team_number": "35", "reason": "Organizer reported attendee dropped out"}}
        session.flush()
        assert session.query(EventTeamMember).filter_by(team_id=target.id).count() == before[str(target.id)]
        assert session.query(EventTeamMember).filter_by(team_id=old_team.id).count() == before[str(old_team.id)] - 1
        assert session.query(EventTeamMember).filter_by(event_id=event.id, registration_id=halo.id).one().team_id == target.id
        assert session.query(EventTeamMember).filter_by(event_id=event.id, registration_id=vin.id).count() == 0
        session.commit()
        session.expire_all()
        assert session.query(EventTeamMember).filter_by(event_id=event.id, registration_id=halo.id).one().team_id == target.id
        assert session.query(EventRegistration).filter_by(id=vin.id).one().rsvp_status == "declined"
        print(json.dumps({"halo_team": target.team_number, "team_name": target.name, "challenge": target.assigned_challenge, "target_members": before[str(target.id)], "previous_team_members": before[str(old_team.id)] - 1, "vinodhini_withdrawn": True, "emails_sent": 0}), flush=True)
    finally:
        session.rollback()
        session.close()


if __name__ == "__main__":
    main()
