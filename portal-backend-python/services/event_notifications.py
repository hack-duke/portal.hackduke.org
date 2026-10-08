"""DuQuantum browser-push schedule and delivery service.

The schedule is intentionally defined in application code so changes are
reviewed and deployed alongside the public event schedule. Push payloads are
event-only: they never contain attendee details, registration IDs, or passes.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from pywebpush import WebPushException, webpush
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.event import Event
from models.event_notification_delivery import EventNotificationDelivery
from models.event_push_subscription import EventPushSubscription


EVENT_SLUG = "duquantum-2026"
EVENT_TIMEZONE = ZoneInfo("America/New_York")
DEFAULT_DUE_WINDOW = timedelta(minutes=10)


@dataclass(frozen=True)
class ScheduledNotification:
    key: str
    scheduled_for: datetime
    title: str
    body: str
    url: str = "/events/duquantum-2026"


def _event_time(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=EVENT_TIMEZONE)


DUQUANTUM_NOTIFICATIONS = (
    ScheduledNotification(
        "sat-check-in",
        _event_time(24, 9),
        "DuQuantum check-in is open",
        "Check in at the Wilkinson Building 0th Floor Lobby until 11:00 AM.",
    ),
    ScheduledNotification(
        "sat-opening",
        _event_time(24, 10, 30),
        "Opening ceremony is starting",
        "Join us in Wilkinson 021 for the DuQuantum opening ceremony.",
    ),
    ScheduledNotification(
        "sat-hacking-lunch",
        _event_time(24, 11, 30),
        "Hacking starts now",
        "Build time begins. Hacker lunch is available in the 0th Floor Lobby until 12:30 PM.",
    ),
    ScheduledNotification(
        "sat-sponsor-fair",
        _event_time(24, 13),
        "Sponsor fair is starting",
        "Meet the DuQuantum sponsors in Wilkinson 126.",
    ),
    ScheduledNotification(
        "sat-intro-workshop",
        _event_time(24, 14),
        "Quantum workshop is starting",
        "The Intro to Quantum Computing workshop begins in Wilkinson 130.",
    ),
    ScheduledNotification(
        "sat-mlh-workshops",
        _event_time(24, 15),
        "MLH workshops are starting",
        "Head to Wilkinson 130 for the MLH workshops.",
    ),
    ScheduledNotification(
        "sat-plenary",
        _event_time(24, 16),
        "Plenary lectures are starting",
        "The DuQuantum plenary lectures begin in Wilkinson 130.",
    ),
    ScheduledNotification(
        "sat-dinner",
        _event_time(24, 18, 30),
        "Hacker dinner is ready",
        "Dinner is available in the Wilkinson 0th Floor Lobby until 8:00 PM.",
    ),
    ScheduledNotification(
        "sat-night",
        _event_time(24, 20),
        "Night work space is open",
        "Wilkinson 021 is available for overnight work and sleeping.",
    ),
    ScheduledNotification(
        "sun-brunch",
        _event_time(25, 10),
        "Sunday brunch is ready",
        "Brunch is available in the Wilkinson 0th Floor Lobby until noon.",
    ),
    ScheduledNotification(
        "sun-hacking-ends",
        _event_time(25, 11, 30),
        "Hacking ends now",
        "Submit your project and get ready for judging at noon.",
    ),
    ScheduledNotification(
        "sun-judging",
        _event_time(25, 12),
        "Judging is starting",
        "Project judging is beginning in the assigned Wilkinson rooms.",
    ),
    ScheduledNotification(
        "sun-deliberations",
        _event_time(25, 13, 45),
        "Judging deliberations are starting",
        "Final deliberations are beginning in Wilkinson 130.",
    ),
    ScheduledNotification(
        "sun-closing",
        _event_time(25, 15, 30),
        "Closing ceremony is starting",
        "Join us in Wilkinson 021 for awards and the DuQuantum closing ceremony.",
    ),
)


@dataclass(frozen=True)
class WebPushSettings:
    enabled: bool
    public_key: Optional[str]
    private_key: Optional[str]
    subject: Optional[str]

    @classmethod
    def from_environment(cls) -> "WebPushSettings":
        enabled = os.getenv("EVENT_NOTIFICATIONS_ENABLED", "false").casefold() in {
            "1",
            "true",
            "yes",
            "on",
        }
        public_key = os.getenv("VAPID_PUBLIC_KEY") or None
        private_key = os.getenv("VAPID_PRIVATE_KEY") or None
        subject = os.getenv("VAPID_SUBJECT") or None
        if enabled and not all((public_key, private_key, subject)):
            raise RuntimeError(
                "Event notifications are enabled without complete VAPID settings"
            )
        if enabled and not subject.startswith(("mailto:", "https://")):
            raise RuntimeError("VAPID subject must be a mailto or HTTPS URI")
        return cls(enabled, public_key, private_key, subject)


def due_notifications(
    now: Optional[datetime] = None,
    window: timedelta = DEFAULT_DUE_WINDOW,
) -> tuple[ScheduledNotification, ...]:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return tuple(
        item
        for item in DUQUANTUM_NOTIFICATIONS
        if item.scheduled_for <= current < item.scheduled_for + window
    )


def notification_payload(item: ScheduledNotification) -> str:
    return json.dumps(
        {
            "title": item.title,
            "body": item.body,
            "url": item.url,
            "tag": f"duquantum-2026-{item.key}",
        },
        separators=(",", ":"),
    )


def _provider_status(error: WebPushException) -> Optional[int]:
    response = getattr(error, "response", None)
    return getattr(response, "status_code", None)


def send_due_event_notifications(
    db: Session,
    *,
    now: Optional[datetime] = None,
    settings: Optional[WebPushSettings] = None,
    sender: Callable[..., object] = webpush,
) -> dict[str, int]:
    """Send notifications due now, with database-backed per-device idempotency."""

    config = settings or WebPushSettings.from_environment()
    counts = {"due": 0, "sent": 0, "failed": 0, "disabled": 0}
    if not config.enabled:
        return counts

    due = due_notifications(now)
    counts["due"] = len(due)
    if not due:
        return counts

    event = db.query(Event).filter(Event.slug == EVENT_SLUG).first()
    if event is None:
        return counts

    subscriptions = (
        db.query(EventPushSubscription)
        .filter(
            EventPushSubscription.event_id == event.id,
            EventPushSubscription.active.is_(True),
        )
        .all()
    )

    for item in due:
        scheduled_utc = item.scheduled_for.astimezone(timezone.utc)
        for subscription in subscriptions:
            delivery = (
                db.query(EventNotificationDelivery)
                .filter(
                    EventNotificationDelivery.subscription_id == subscription.id,
                    EventNotificationDelivery.notification_key == item.key,
                )
                .first()
            )
            if delivery is not None and delivery.status in {"sent", "skipped"}:
                continue
            if delivery is not None and delivery.attempts >= 3:
                continue
            if delivery is None:
                delivery = EventNotificationDelivery(
                    event_id=event.id,
                    subscription_id=subscription.id,
                    notification_key=item.key,
                    scheduled_for=scheduled_utc,
                    status="queued",
                    attempts=0,
                )
                db.add(delivery)
                try:
                    db.commit()
                except IntegrityError:
                    # Another worker claimed this device/event delivery first.
                    db.rollback()
                    continue

            delivery.attempts += 1
            try:
                response = sender(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh,
                            "auth": subscription.auth,
                        },
                    },
                    data=notification_payload(item),
                    vapid_private_key=config.private_key,
                    vapid_claims={"sub": config.subject},
                    ttl=3600,
                )
                delivery.status = "sent"
                delivery.sent_at = datetime.now(timezone.utc)
                delivery.provider_status = getattr(response, "status_code", None)
                delivery.error = None
                counts["sent"] += 1
            except WebPushException as error:
                status = _provider_status(error)
                delivery.provider_status = status
                if status in {404, 410}:
                    subscription.active = False
                    subscription.disabled_at = datetime.now(timezone.utc)
                    subscription.last_error = "subscription_expired"
                    delivery.status = "skipped"
                    delivery.error = "subscription_expired"
                    counts["disabled"] += 1
                else:
                    delivery.status = "failed"
                    delivery.error = "provider_error"
                    counts["failed"] += 1
            except Exception:
                delivery.status = "failed"
                delivery.error = "delivery_error"
                counts["failed"] += 1
            db.commit()

    return counts
