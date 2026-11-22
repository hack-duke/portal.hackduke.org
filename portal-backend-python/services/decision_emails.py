"""Accept/reject decision emails for applicants.

Each applicant with a final decision (ACCEPTED or REJECTED) gets exactly one
email, tracked by Application.decision_emailed_at. Sending is idempotent: a
row is claimed atomically before its email goes out, so pressing the button
twice (or two admins pressing it at once) never double-sends.
"""
import html
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from string import Template
from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

from models.application import Application, ApplicationStatus
from models.user import User
from utils.ses import get_sender_email, get_ses_client, send_email

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"

DECISION_TEMPLATES = {
    ApplicationStatus.ACCEPTED: {
        "file": "accepted.html",
        "subject": "You're in! Welcome to ${event_name}",
    },
    ApplicationStatus.REJECTED: {
        "file": "rejected.html",
        "subject": "Your ${event_name} application",
    },
}

EMAILABLE_STATUSES = tuple(DECISION_TEMPLATES.keys())

_LEADING_COMMENT = re.compile(r"^\s*<!--.*?-->\s*", re.DOTALL)


def _event_name() -> str:
    return os.getenv("DECISION_EMAIL_EVENT_NAME", "HackDuke: Code for Good 2026")


def _portal_url() -> str:
    return os.getenv("FRONTEND_URL", "https://portal.hackduke.org")


def _max_send_rate() -> float:
    """Emails per second; keep below the account's SES MaxSendRate."""
    try:
        rate = float(os.getenv("SES_MAX_SEND_RATE", "10"))
    except ValueError:
        rate = 10.0
    return max(rate, 0.1)


def _load_template(status: ApplicationStatus) -> str:
    raw = (TEMPLATE_DIR / DECISION_TEMPLATES[status]["file"]).read_text()
    return _LEADING_COMMENT.sub("", raw, count=1)


def _first_name(app: Application, user: Optional[User]) -> str:
    submission = app.submission_json or {}
    name = (
        submission.get("pref_name")
        or submission.get("first_name")
        or (user.first_name if user else None)
        or "there"
    )
    return str(name).strip() or "there"


def recipient_email(app: Application, user: Optional[User]) -> Optional[str]:
    submission = app.submission_json or {}
    email = submission.get("email") or (user.email if user else None)
    email = str(email).strip() if email else ""
    return email or None


def render_email(
    status: ApplicationStatus, first_name: str
) -> tuple[str, str]:
    """Return (subject, html_body) for a decision email."""
    values = {
        "first_name": html.escape(first_name),
        "event_name": html.escape(_event_name()),
        "portal_url": html.escape(_portal_url()),
    }
    subject_values = {**values, "event_name": _event_name()}
    subject = Template(DECISION_TEMPLATES[status]["subject"]).safe_substitute(
        subject_values
    )
    body = Template(_load_template(status)).safe_substitute(values)
    return subject, body


def _pending_query(db: Session, form_key: str):
    return (
        db.query(Application, User)
        .outerjoin(User, User.id == Application.user_id)
        .filter(
            Application.form_key == form_key,
            Application.status.in_(EMAILABLE_STATUSES),
            Application.decision_emailed_at.is_(None),
        )
        .order_by(Application.decided_at.asc().nullsfirst(), Application.id)
    )


def preview(db: Session, form_key: str) -> dict:
    rows = _pending_query(db, form_key).all()
    counts = {s.value: 0 for s in EMAILABLE_STATUSES}
    missing_email = 0
    for app, user in rows:
        if recipient_email(app, user) is None:
            missing_email += 1
        else:
            counts[app.status.value] += 1

    already_emailed = (
        db.query(Application)
        .filter(
            Application.form_key == form_key,
            Application.decision_emailed_at.isnot(None),
        )
        .count()
    )

    samples = {}
    for status in EMAILABLE_STATUSES:
        subject, body = render_email(status, "Alex")
        samples[status.value] = {"subject": subject, "html": body}

    return {
        "counts": counts,
        "total": sum(counts.values()),
        "missing_email": missing_email,
        "already_emailed": already_emailed,
        "samples": samples,
    }


@dataclass
class SendResult:
    sent: int = 0
    failed: list[dict] = field(default_factory=list)
    skipped_missing_email: int = 0


def send_pending(db: Session, form_key: str, ses_client=None) -> SendResult:
    """Email every decided-but-not-yet-emailed applicant, one email each."""
    result = SendResult()
    get_sender_email()  # fail fast (RuntimeError) if SES isn't configured
    rows = _pending_query(db, form_key).all()
    if not rows:
        return result

    client = ses_client or get_ses_client()
    interval = 1.0 / _max_send_rate()
    for status in EMAILABLE_STATUSES:  # fail fast on a missing template
        _load_template(status)

    for app, user in rows:
        app_id = app.id
        status = app.status
        to = recipient_email(app, user)
        if to is None:
            result.skipped_missing_email += 1
            continue

        # Atomically claim the row so concurrent runs can't double-send.
        claimed = db.execute(
            update(Application)
            .where(
                Application.id == app_id,
                Application.status == status,
                Application.decision_emailed_at.is_(None),
            )
            .values(decision_emailed_at=datetime.now(timezone.utc))
            .execution_options(synchronize_session=False)
        ).rowcount
        db.commit()
        if not claimed:
            continue

        subject, body = render_email(status, _first_name(app, user))
        started = time.monotonic()
        try:
            send_email(to=to, subject=subject, html_body=body, client=client)
            result.sent += 1
        except Exception as e:  # release the claim so a retry picks it up
            db.execute(
                update(Application)
                .where(Application.id == app_id)
                .values(decision_emailed_at=None)
                .execution_options(synchronize_session=False)
            )
            db.commit()
            result.failed.append(
                {"application_id": str(app_id), "email": to, "error": type(e).__name__}
            )

        elapsed = time.monotonic() - started
        if elapsed < interval:
            time.sleep(interval - elapsed)

    return result
