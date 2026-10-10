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
from email.utils import formataddr
from typing import Any
from urllib.parse import urlparse


EVENT_SLUG = "duquantum-2026"
DEFAULT_SENDER_NAME = "DuQuantum 2026"


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
    sender_name: str = DEFAULT_SENDER_NAME

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
            sender_name=os.getenv("SES_FROM_NAME", DEFAULT_SENDER_NAME).strip()
            or DEFAULT_SENDER_NAME,
        )


CAMPAIGN_TEMPLATE_VERSIONS = {
    "pass-ready": "duquantum-pass-ready-v2",
    "event-reminder": "duquantum-event-reminder-v2",
    "auth0-invitation": "duquantum-auth0-invitation-v3",
    "admin-invitation": "duquantum-admin-invitation-v1",
}


def _render_branded_html(
    *,
    first_name: str,
    eyebrow: str,
    heading: str,
    intro: str,
    detail_label: str,
    detail_value: str,
    supporting_text: str,
    action_text: str,
    action_url: str,
    event_url: str,
    logo_url: str,
    font_url: str,
    next_steps: tuple[str, ...] = (),
) -> str:
    safe_name = html.escape(first_name.strip() or "Attendee")
    safe_eyebrow = html.escape(eyebrow)
    safe_heading = html.escape(heading)
    safe_intro = html.escape(intro)
    safe_detail_label = html.escape(detail_label)
    safe_detail_value = html.escape(detail_value)
    safe_supporting_text = html.escape(supporting_text)
    safe_action_text = html.escape(action_text)
    safe_action_url = html.escape(action_url, quote=True)
    safe_event_url = html.escape(event_url, quote=True)
    safe_logo_url = html.escape(logo_url, quote=True)
    safe_font_url = html.escape(font_url, quote=True)
    safe_next_steps = tuple(html.escape(step) for step in next_steps)
    next_steps_html = ""
    if safe_next_steps:
        step_rows = "".join(
            f"""
                        <tr>
                          <td width="34" valign="top" style="padding:0 10px 13px 0;">
                            <span style="background-color:#f3b562;border-radius:999px;color:#211538;display:inline-block;font-family:Arial,sans-serif;font-size:12px;font-weight:700;line-height:24px;text-align:center;width:24px;">{index}</span>
                          </td>
                          <td valign="top" style="color:#e4d8c5;font-family:Oxygen,Arial,sans-serif;font-size:14px;line-height:22px;padding:1px 0 13px;">{step}</td>
                        </tr>"""
            for index, step in enumerate(safe_next_steps, start=1)
        )
        next_steps_html = f"""
                  <tr>
                    <td style="padding:0 0 27px;">
                      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#120a24;border:1px solid #573b64;border-radius:12px;">
                        <tr>
                          <td style="color:#f3b562;font-family:Oxygen,Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:1.7px;line-height:17px;padding:18px 18px 13px;text-transform:uppercase;">After you create your password</td>
                        </tr>
                        <tr>
                          <td style="padding:0 18px 5px;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                              {step_rows}
                            </table>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>"""

    return f"""<!doctype html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="x-apple-disable-message-reformatting">
    <title>{safe_heading}</title>
    <style>
      @font-face {{
        font-family: "Edge of the Galaxy";
        font-style: normal;
        font-weight: 400;
        src: url("{safe_font_url}") format("opentype");
      }}
      @keyframes duq-glow {{
        0%, 100% {{ box-shadow: 0 0 0 rgba(243,181,98,0), 0 20px 55px rgba(0,0,0,.35); }}
        50% {{ box-shadow: 0 0 34px rgba(243,181,98,.15), 0 20px 55px rgba(0,0,0,.35); }}
      }}
      @keyframes duq-float {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-3px); }}
      }}
      @keyframes duq-signal {{
        0%, 100% {{ opacity: .45; }}
        50% {{ opacity: 1; }}
      }}
      .duq-card {{ animation: duq-glow 5s ease-in-out infinite; }}
      .duq-logo {{ animation: duq-float 4s ease-in-out infinite; }}
      .duq-signal {{ animation: duq-signal 2.4s ease-in-out infinite; }}
      .duq-button:hover {{ background-color: #ffd07b !important; }}
      @media only screen and (max-width: 620px) {{
        .duq-shell {{ padding: 18px 10px !important; }}
        .duq-card-cell {{ padding: 30px 22px !important; }}
        .duq-heading {{ font-size: 30px !important; line-height: 34px !important; }}
      }}
      @media (prefers-reduced-motion: reduce) {{
        .duq-card, .duq-logo, .duq-signal {{ animation: none !important; }}
      }}
    </style>
  </head>
  <body style="background-color:#0e0525;margin:0;padding:0;width:100%;">
    <div style="display:none;font-size:1px;color:#0e0525;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
      {safe_intro}&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;
    </div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#0e0525;width:100%;">
      <tr>
        <td class="duq-shell" align="center" style="padding:36px 16px;">
          <table class="duq-card" role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#161027;border:1px solid #573b64;border-radius:22px;max-width:640px;overflow:hidden;">
            <tr>
              <td style="background-color:#0a0517;border-bottom:1px solid #432c50;padding:26px 30px 22px;text-align:center;">
                <a href="{safe_event_url}" style="text-decoration:none;" target="_blank">
                  <img class="duq-logo" src="{safe_logo_url}" width="520" alt="DuQuantum 2026" style="border:0;display:block;height:auto;margin:0 auto;max-width:100%;width:520px;">
                </a>
              </td>
            </tr>
            <tr>
              <td class="duq-card-cell" style="padding:42px 46px 38px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td style="font-family:Oxygen,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:2.2px;line-height:18px;padding-bottom:14px;text-transform:uppercase;color:#f3b562;">
                      <span class="duq-signal" style="color:#f3b562;">●</span>&nbsp;&nbsp;{safe_eyebrow}
                    </td>
                  </tr>
                  <tr>
                    <td class="duq-heading" style="color:#fffaf0;font-family:'Edge of the Galaxy','Trebuchet MS',Arial,sans-serif;font-size:38px;font-weight:400;letter-spacing:.6px;line-height:43px;padding-bottom:18px;">
                      {safe_heading}
                    </td>
                  </tr>
                  <tr>
                    <td style="color:#fffaf0;font-family:Oxygen,Arial,sans-serif;font-size:17px;line-height:28px;padding-bottom:12px;">
                      Hi {safe_name},
                    </td>
                  </tr>
                  <tr>
                    <td style="color:#d9c9de;font-family:Oxygen,Arial,sans-serif;font-size:16px;line-height:26px;padding-bottom:26px;">
                      {safe_intro}
                    </td>
                  </tr>
                  <tr>
                    <td style="padding-bottom:28px;">
                      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#0a0517;border-left:4px solid #f3b562;border-radius:10px;">
                        <tr>
                          <td style="padding:17px 19px;">
                            <div style="color:#c7a983;font-family:Oxygen,Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:1.7px;line-height:17px;text-transform:uppercase;">{safe_detail_label}</div>
                            <div style="color:#fffaf0;font-family:Oxygen,Arial,sans-serif;font-size:16px;font-weight:700;line-height:24px;padding-top:3px;">{safe_detail_value}</div>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                  <tr>
                    <td align="left" style="padding-bottom:27px;">
                      <!--[if mso]>
                      <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{safe_action_url}" style="height:52px;v-text-anchor:middle;width:250px;" arcsize="18%" stroke="f" fillcolor="#f3b562">
                        <w:anchorlock/>
                        <center style="color:#211538;font-family:Arial,sans-serif;font-size:15px;font-weight:bold;">{safe_action_text}</center>
                      </v:roundrect>
                      <![endif]-->
                      <!--[if !mso]><!-- -->
                      <a class="duq-button" href="{safe_action_url}" target="_blank" style="background-color:#f3b562;border-radius:9px;color:#211538;display:inline-block;font-family:Oxygen,Arial,sans-serif;font-size:15px;font-weight:700;line-height:20px;padding:16px 23px;text-decoration:none;">{safe_action_text}&nbsp;&nbsp;→</a>
                      <!--<![endif]-->
                    </td>
                  </tr>
                  {next_steps_html}
                  <tr>
                    <td style="color:#bbaac3;font-family:Oxygen,Arial,sans-serif;font-size:14px;line-height:23px;">
                      {safe_supporting_text}
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="background-color:#0a0517;border-top:1px solid #432c50;padding:23px 30px;text-align:center;">
                <p style="color:#c7a983;font-family:Oxygen,Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:1.5px;line-height:18px;margin:0 0 7px;text-transform:uppercase;">HackDuke × Duke Quantum Information Society</p>
                <p style="color:#927f9e;font-family:Oxygen,Arial,sans-serif;font-size:12px;line-height:19px;margin:0;">Your attendee pass and personal information stay protected inside the portal.</p>
                <p style="font-family:Oxygen,Arial,sans-serif;font-size:12px;line-height:19px;margin:8px 0 0;"><a href="{safe_event_url}" style="color:#f3b562;text-decoration:underline;">portal.hackduke.org</a></p>
              </td>
            </tr>
          </table>
          <p style="color:#786887;font-family:Arial,sans-serif;font-size:11px;line-height:18px;margin:16px auto 0;max-width:600px;text-align:center;">If you did not expect this message, contact the DuQuantum organizers.</p>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def render_campaign(
    campaign_key: str,
    *,
    first_name: str,
    portal_url: str,
    account_setup_url: str | None = None,
    login_email: str | None = None,
) -> RenderedEmail:
    base_portal_url = portal_url.strip().rstrip("/")
    parsed_portal = urlparse(base_portal_url)
    if parsed_portal.scheme != "https" or not parsed_portal.netloc:
        raise ValueError("portal URL must be HTTPS")

    event_url = f"{base_portal_url}/events/{EVENT_SLUG}"
    logo_url = f"{base_portal_url}/duquantum-2026/logo-email.png"
    font_url = f"{base_portal_url}/duquantum-2026/edge-of-the-galaxy.otf"
    display_name = first_name.strip() or "Attendee"
    next_steps: tuple[str, ...] = ()

    if campaign_key == "pass-ready":
        subject = "Your DuQuantum 2026 attendee pass is ready"
        eyebrow = "Attendee access confirmed"
        heading = "Your pass is ready"
        intro = "Your DuQuantum 2026 attendee pass is ready and waiting securely in the portal."
        detail_label = "Event"
        detail_value = "DuQuantum 2026 · October 24–25 · Duke University"
        supporting_text = (
            "Sign in before you arrive to confirm that your pass loads correctly. "
            "For your privacy, the pass itself is never included in email."
        )
        action_text = "Open my attendee portal"
        action_url = event_url
    elif campaign_key == "event-reminder":
        subject = "DuQuantum 2026 attendee reminder"
        eyebrow = "The countdown is on"
        heading = "Get ready for DuQuantum"
        intro = (
            "DuQuantum 2026 is coming up soon. Take a moment to sign in and make "
            "sure your attendee pass is available before you arrive."
        )
        detail_label = "Save the date"
        detail_value = "October 24–25, 2026 · Duke University"
        supporting_text = (
            "Keep this portal link handy on event day. Your pass remains protected "
            "behind your account sign-in."
        )
        action_text = "Review my attendee details"
        action_url = event_url
    elif campaign_key == "auth0-invitation":
        if not account_setup_url:
            raise ValueError("account setup URL is required for an invitation")
        parsed_setup = urlparse(account_setup_url)
        if parsed_setup.scheme != "https" or not parsed_setup.netloc:
            raise ValueError("account setup URL must be HTTPS")
        normalized_login_email = (login_email or "").strip()
        if not normalized_login_email or "@" not in normalized_login_email:
            raise ValueError("login email is required for an invitation")
        subject = "Set up your DuQuantum 2026 portal account"
        eyebrow = "Your portal invitation"
        heading = "Welcome to DuQuantum"
        intro = (
            "An account has been reserved for your DuQuantum 2026 registration. "
            "Use the secure, single-use link below to create your private password "
            "directly on the HackDuke portal."
        )
        detail_label = "Your portal login email"
        detail_value = normalized_login_email
        supporting_text = (
            "No temporary password is sent or stored. Create your password, then "
            "sign in with the email above to view your attendee pass. This setup "
            "link is unique to you, expires after seven days, and can only be used once."
        )
        next_steps = (
            "Sign in at portal.hackduke.org with the email shown above and open your attendee pass.",
            "On your phone, use the browser Share or menu button and choose Add to Home Screen or Install app.",
            "Open the new DuQuantum icon from your Home Screen, tap Enable event alerts, and allow notifications.",
            "Keep notifications enabled during the event for live schedule reminders and organizer updates.",
        )
        action_text = "Create my password"
        action_url = account_setup_url
    elif campaign_key == "admin-invitation":
        if not account_setup_url:
            raise ValueError("account setup URL is required for an invitation")
        parsed_setup = urlparse(account_setup_url)
        if parsed_setup.scheme != "https" or not parsed_setup.netloc:
            raise ValueError("account setup URL must be HTTPS")
        normalized_login_email = (login_email or "").strip()
        if not normalized_login_email or "@" not in normalized_login_email:
            raise ValueError("login email is required for an invitation")
        admin_url = f"{base_portal_url}/admin/events/{EVENT_SLUG}/attendees"
        subject = "Set up your DuQuantum 2026 admin account"
        eyebrow = "Private organizer access"
        heading = "Your admin workspace is ready"
        intro = (
            "Your DuQuantum 2026 organizer account has been prepared. Use the "
            "secure, single-use link below to create a private password."
        )
        detail_label = "Admin login email"
        detail_value = normalized_login_email
        supporting_text = (
            "This setup link expires after seven days and can only be used once. "
            "Participant records contain private information; access them only "
            "for event operations and never share this invitation."
        )
        next_steps = (
            "Create a strong, unique password using the secure button above.",
            f"Sign in at {admin_url} with the organizer email shown above.",
            "Use Attendee manifest to search participants and review registration, pass, invitation, and check-in status.",
            "Open Check-in scanner on your phone and allow camera access to scan attendee passes.",
        )
        action_text = "Create admin password"
        action_url = account_setup_url
    else:
        raise ValueError("unknown email campaign")

    next_steps_text = ""
    if next_steps:
        next_steps_text = "\n\nAfter you create your password:\n" + "\n".join(
            f"{index}. {step}" for index, step in enumerate(next_steps, start=1)
        )

    text_body = (
        f"Hi {display_name},\n\n{intro}\n\n"
        f"{detail_label}: {detail_value}\n\n"
        f"{action_text}: {action_url}\n\n"
        f"{supporting_text}{next_steps_text}\n\n"
        "Organized by HackDuke and Duke Quantum Information Society.\n"
        "If you did not expect this message, contact the DuQuantum organizers."
    )
    html_body = _render_branded_html(
        first_name=display_name,
        eyebrow=eyebrow,
        heading=heading,
        intro=intro,
        detail_label=detail_label,
        detail_value=detail_value,
        supporting_text=supporting_text,
        action_text=action_text,
        action_url=action_url,
        event_url=event_url,
        logo_url=logo_url,
        font_url=font_url,
        next_steps=next_steps,
    )
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
            "FromEmailAddress": formataddr(
                (self.settings.sender_name, self.settings.sender)
            ),
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

    def already_sent(
        self, *, event_id: Any, registration_id: Any, campaign_key: str
    ) -> bool:
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
