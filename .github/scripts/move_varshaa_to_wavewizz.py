"""Organizer-directed team transfer and one idempotent participant notice."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func
from db import get_local_session
from models import Event, EventRegistration, EventTeam, EventTeamMember, EmailDelivery
from services.event_email_campaign import SesSettings, SesEmailSender, RenderedEmail, _render_branded_html
from scripts.remind_event_accounts import validate_ses_delivery_posture, suppression_reason


def main():
    session = get_local_session()
    try:
        event = session.query(Event).filter_by(slug="duquantum-2026").one()
        attendee = session.query(EventRegistration).filter_by(event_id=event.id, normalized_email="vv366@scarletmail.rutgers.edu").with_for_update().one()
        if attendee.first_name.strip().casefold() != "varshaa" or attendee.admission_status != "accepted" or attendee.rsvp_status != "confirmed":
            raise ValueError("Attendee identity or eligibility changed")
        target = session.query(EventTeam).filter_by(event_id=event.id, team_number="50", active=True).with_for_update().one()
        if (target.name, target.assigned_track, target.assigned_challenge) != ("WaveWizz", "Introductory", "BlueQubit"):
            raise ValueError("Target team changed")
        member = session.query(EventTeamMember).filter_by(event_id=event.id, registration_id=attendee.id).with_for_update().one()
        old_team = session.query(EventTeam).filter_by(id=member.team_id).with_for_update().one()
        if member.team_id != target.id:
            if old_team.team_number != "48":
                raise ValueError("Current team changed; review required")
            def record(row):
                return {col.name: getattr(row, col.name) for col in row.__table__.columns}
            backup = Path(os.environ["TEAM_CHANGE_BACKUP"])
            backup.write_text(json.dumps({"registration": record(attendee), "member": record(member), "old_team": record(old_team), "target_team": record(target)}, default=str))
            backup.chmod(0o600)
            member.member_position = (session.query(func.max(EventTeamMember.member_position)).filter_by(team_id=target.id).scalar() or 0) + 1
            member.team_id = target.id
            attendee.source_data = {**(attendee.source_data or {}), "organizer_team_override": {"team_number": "50", "previous_team_number": "48", "at": datetime.now(timezone.utc).isoformat(), "reason": "Organizer requested Varshaa move to WaveWizz"}}
            session.commit()
        session.expire_all()
        member = session.query(EventTeamMember).filter_by(event_id=event.id, registration_id=attendee.id).one()
        if member.team_id != target.id:
            raise ValueError("Committed membership verification failed")
        print('TEAM_CHANGE {"team": "50", "name": "WaveWizz", "track": "Introductory", "challenge": "BlueQubit", "verified": true}', flush=True)
        campaign = "team-change-wavewizz-varshaa-20261024"
        delivery = session.query(EmailDelivery).filter_by(event_id=event.id, registration_id=attendee.id, campaign_key=campaign).one_or_none()
        if delivery is not None and delivery.status in ("sent", "queued"):
            print("NOTICE " + json.dumps({"status": delivery.status, "already_recorded": True}), flush=True)
            return
        settings = SesSettings.from_environment()
        mailer = SesEmailSender(settings)
        validate_ses_delivery_posture(mailer.client, settings)
        if suppression_reason(mailer.client, attendee.email):
            raise ValueError("Recipient suppressed; team move retained, notice not sent")
        url = settings.portal_url.rstrip("/") + "/events/duquantum-2026"
        intro = "Your DuQuantum team assignment has been updated. You are now on WaveWizz (team 50), in the Introductory track, working on the BlueQubit challenge."
        rendered = RenderedEmail(
            subject="Your DuQuantum team is now WaveWizz",
            text_body=f"Hi Varshaa,\n\n{intro}\n\nView your updated team in the portal: {url}\n\nPlease connect with your new teammates at the event. If you need help finding them, ask the DuQuantum organizers.\n\nDuQuantum 2026",
            html_body=_render_branded_html(first_name="Varshaa", eyebrow="Team assignment updated", heading="Welcome to WaveWizz", intro=intro, detail_label="Your new team", detail_value="50 — WaveWizz | Introductory | BlueQubit", supporting_text="Please connect with your new teammates at the event. If you need help finding them, ask the DuQuantum organizers.", action_text="View my team", action_url=url, event_url=url, logo_url=settings.portal_url.rstrip("/") + "/duquantum-2026/logo-email.png", font_url=settings.portal_url.rstrip("/") + "/duquantum-2026/edge-of-the-galaxy.otf"))
        if delivery is None:
            delivery = EmailDelivery(event_id=event.id, registration_id=attendee.id, campaign_key=campaign, recipient_email=attendee.email, template_version="duquantum-team-change-v1", status="queued")
            session.add(delivery)
        else:
            delivery.status, delivery.error = "queued", None
        session.commit()
        try:
            message_id = mailer.send(recipient=attendee.email, rendered=rendered)
        except Exception as error:
            delivery.status, delivery.error = "failed", type(error).__name__
            session.commit()
            raise
        delivery.status, delivery.provider_message_id, delivery.sent_at = "sent", message_id, datetime.now(timezone.utc)
        session.commit()
        print("NOTICE " + json.dumps({"status": "sent", "accepted_by_ses": True, "sender": settings.sender}), flush=True)
    finally:
        session.rollback()
        session.close()


if __name__ == "__main__":
    main()
