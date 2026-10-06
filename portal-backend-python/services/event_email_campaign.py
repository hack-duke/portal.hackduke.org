"""Event-scoped transactional email delivery through Amazon SES.

This module contains no import-time AWS or database calls. Callers must opt in
to sending, and campaign messages intentionally link to the portal instead of
placing an attendee pass or other personal data in email.
"""

from __future__ import annotations

import html
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    text_body: str
    html_body: str


@dataclass(frozen=True)
class SesSettings:
    region: str
    sender: str
    portal_url: str
    configuration_set: str | None = None

    @classmethod
    def from_environment(cls) -> "SesSettings":
        sender = os.getenv("SES_FROM_EMAIL", "").strip()
        portal_url = os.getenv("PORTAL_PUBLIC_URL", "").strip().rstrip("/")
        if not sender or "@" not in sender:
            raise ValueError("SES_FROM_EMAIL must be a configured verified sender")
        parsed_url = urlparse(portal_url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise ValueError("PORTAL_PUBLIC_URL must be an HTTPS URL")
        return cls(
            region=os.getenv("SES_REGION", os.getenv("AWS_REGION", "us-east-2")),
            sender=sender,
            portal_url=portal_url,
            configuration_set=os.getenv("SES_CONFIGURATION_SET") or None,
        )


CAMPAIGN_TEMPLATE_VERSIONS = {
    "pass-ready": "duquantum-pass-ready-v1",
    "event-reminder": "duquantum-event-reminder-v1",
    "auth0-invitation": "duquantum-auth0-invitation-v1",
}


def render_campaign(
    campaign_key: str,
    *,
    first_name: str,
    portal_url: str,
    password_ticket_url: str | None = None,
) -> RenderedEmail:
    safe_name = html.escape(first_name.strip() or "Attendee")
    safe_portal_url = html.escape(portal_url, quote=True)

    if campaign_key == "pass-ready":
        subject = "Your DuQuantum 2026 attendee pass is ready"
        intro = "Your DuQuantum 2026 attendee pass is ready in the portal."
        action_text = "Open the attendee portal"
        action_url = portal_url
    elif campaign_key == "event-reminder":
        subject = "DuQuantum 2026 attendee reminder"
        intro = (
            "DuQuantum 2026 is October 24–25. Sign in to the portal before "
            "arrival and make sure your attendee pass is available."
        )
        action_text = "Review your attendee details"
        action_url = portal_url
    elif campaign_key == "auth0-invitation":
        if not password_ticket_url:
            raise ValueError("password ticket URL is required for an invitation")
        parsed_ticket = urlparse(password_ticket_url)
        if parsed_ticket.scheme != "https" or not parsed_ticket.netloc:
            raise ValueError("password ticket URL must be HTTPS")
        subject = "Set up your DuQuantum 2026 portal account"
        intro = (
            "An account has been reserved for your DuQuantum 2026 registration. "
            "Use the secure, single-use link below to choose your own password."
        )
        action_text = "Set up my portal account"
        action_url = password_ticket_url
    else:
        raise ValueError("unknown email campaign")

    safe_action_url = html.escape(action_url, quote=True)
    text_body = (
        f"Hi {first_name.strip() or 'Attendee'},\n\n{intro}\n\n"
        f"{action_text}: {action_url}\n\n"
        "If you did not expect this message, contact the DuQuantum organizers."
    )
    html_body = f"""<!doctype html>
<html lang="en">
  <body style="background:#140c24;color:#fff;font-family:Arial,sans-serif;margin:0;padding:32px">
    <main style="background:#211538;border:1px solid #5b437d;border-radius:12px;max-width:600px;margin:auto;padding:32px">
      <p style="color:#f3c969;font-weight:700;letter-spacing:.08em">DUQUANTUM 2026</p>
      <h1 style="font-size:24px">Hi {safe_name},</h1>
      <p style="font-size:16px;line-height:1.6">{html.escape(intro)}</p>
      <p style="margin:28px 0">
        <a href="{safe_action_url}" style="background:#f3c969;color:#211538;border-radius:8px;display:inline-block;font-weight:700;padding:14px 20px;text-decoration:none">{html.escape(action_text)}</a>
      </p>
      <p style="color:#cbbfdc;font-size:13px;line-height:1.5">If you did not expect this message, contact the DuQuantum organizers.</p>
    </main>
  </body>
</html>"""
    return RenderedEmail(subject=subject, text_body=text_body, html_body=html_body)


class SesEmailSender:
    def __init__(self, settings: SesSettings, client: Any | None = None):
        self.settings = settings
        if client is None:
            import boto3

            client = boto3.client("sesv2", region_name=settings.region)
        self.client = client

    def send(self, *, recipient: str, rendered: RenderedEmail) -> str:
        request: dict[str, Any] = {
            "FromEmailAddress": self.settings.sender,
            "Destination": {"ToAddresses": [recipient]},
            "Content": {
                "Simple": {
                    "Subject": {"Data": rendered.subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": rendered.text_body, "Charset": "UTF-8"},
                        "Html": {"Data": rendered.html_body, "Charset": "UTF-8"},
                    },
                }
            },
        }
        if self.settings.configuration_set:
            request["ConfigurationSetName"] = self.settings.configuration_set
        response = self.client.send_email(**request)
        return str(response["MessageId"])


class OptionalEmailDeliveryAudit:
    """Adapter for the optional EmailDelivery model.

    The event schema can launch without a delivery table. If
    ``models.email_delivery.EmailDelivery`` is later added, the CLI will use it
    for idempotency and status history without changing the send service.
    """

    def __init__(self, session: Any):
        self.session = session
        try:
            from models.email_delivery import EmailDelivery
        except (ImportError, ModuleNotFoundError):
            EmailDelivery = None
        self.model = EmailDelivery

    @property
    def available(self) -> bool:
        return self.model is not None

    def already_sent(self, *, event_id: Any, registration_id: Any, campaign_key: str) -> bool:
        """Return true for sent or uncertain queued rows.

        A process can exit after SES accepted a message but before ``sent`` was
        recorded. Treating ``queued`` as non-sendable avoids a blind duplicate;
        an operator must reconcile it against SES before changing it to failed.
        """
        if self.model is None:
            return False
        row = (
            self.session.query(self.model)
            .filter(
                self.model.event_id == event_id,
                self.model.registration_id == registration_id,
                self.model.campaign_key == campaign_key,
                self.model.status.in_(("queued", "sent")),
            )
            .first()
        )
        return row is not None

    def queued(
        self,
        *,
        event_id: Any,
        registration_id: Any,
        campaign_key: str,
        recipient: str,
    ) -> Any | None:
        if self.model is None:
            return None
        row = (
            self.session.query(self.model)
            .filter(
                self.model.event_id == event_id,
                self.model.registration_id == registration_id,
                self.model.campaign_key == campaign_key,
            )
            .one_or_none()
        )
        if row is None:
            row = self.model(
                event_id=event_id,
                registration_id=registration_id,
                campaign_key=campaign_key,
                recipient_email=recipient,
                template_version=CAMPAIGN_TEMPLATE_VERSIONS[campaign_key],
                status="queued",
            )
            self.session.add(row)
        elif row.status == "failed":
            row.recipient_email = recipient
            row.template_version = CAMPAIGN_TEMPLATE_VERSIONS[campaign_key]
            row.status = "queued"
            row.provider_message_id = None
            row.error = None
            row.sent_at = None
        else:
            raise RuntimeError("delivery is already queued or sent")
        self.session.flush()
        return row

    @staticmethod
    def mark_sent(row: Any | None, provider_message_id: str) -> None:
        if row is not None:
            row.status = "sent"
            row.provider_message_id = provider_message_id
            row.sent_at = datetime.now(timezone.utc)

    @staticmethod
    def mark_failed(row: Any | None, error: Exception) -> None:
        if row is not None:
            row.status = "failed"
            # Exception type is operationally useful and cannot contain PII.
            row.error = type(error).__name__


def is_registration_eligible(registration: Any, event: Any) -> bool:
    if registration.admission_status != "accepted":
        return False
    if event.pass_eligibility == "confirmed":
        return registration.rsvp_status == "confirmed"
    return True


def campaign_allows_registration(registration: Any, *, marketing: bool) -> bool:
    """Enforce optional MLH/DEV marketing consent independently."""

    return not marketing or registration.mlh_marketing_opt_in is True
