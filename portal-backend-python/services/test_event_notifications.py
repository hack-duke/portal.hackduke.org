import json
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select

from services.event_notifications import (
    DUQUANTUM_NOTIFICATIONS,
    WebPushSettings,
    due_notifications,
    notification_payload,
    send_due_event_notifications,
)
from models.event import Event
from models.event_notification_delivery import EventNotificationDelivery
from models.event_push_subscription import EventPushSubscription
from models.event_registration import EventRegistration
from services.event_notifications import EVENT_SLUG


@pytest_asyncio.fixture
async def notification_session_data(test_session):
    event = Event(
        slug=EVENT_SLUG,
        name="DuQuantum",
        state="active",
        pass_eligibility="confirmed",
    )
    test_session.add(event)
    await test_session.flush()
    registration = EventRegistration(
        event_id=event.id,
        email="push@example.org",
        normalized_email="push@example.org",
        admission_status="accepted",
        rsvp_status="confirmed",
        source="test",
        source_data={},
    )
    test_session.add(registration)
    await test_session.flush()
    subscription = EventPushSubscription(
        event_id=event.id,
        registration_id=registration.id,
        endpoint="https://fcm.googleapis.com/test-endpoint",
        endpoint_hash="f" * 64,
        p256dh="p256dh",
        auth="auth",
        active=True,
    )
    test_session.add(subscription)
    await test_session.flush()
    return event, subscription


def enabled_settings():
    return WebPushSettings(
        enabled=True,
        public_key="public",
        private_key="private",
        subject="mailto:events@example.org",
    )


async def load_delivery(test_session):
    return (
        await test_session.scalars(select(EventNotificationDelivery))
    ).one()


@pytest.mark.asyncio
async def test_send_due_event_notifications_persists_idempotent_success(
    test_session, notification_session_data
):
    _event, _subscription = notification_session_data
    sent_payloads = []

    def sender(**kwargs):
        sent_payloads.append(kwargs)
        return type("Response", (), {"status_code": 201})()

    now = datetime(2026, 10, 24, 13, 3, tzinfo=timezone.utc)
    first = await send_due_event_notifications(
        test_session, now=now, settings=enabled_settings(), sender=sender
    )
    second = await send_due_event_notifications(
        test_session, now=now, settings=enabled_settings(), sender=sender
    )

    delivery = await load_delivery(test_session)
    assert first == {"due": 1, "sent": 1, "failed": 0, "disabled": 0}
    assert second == {"due": 1, "sent": 0, "failed": 0, "disabled": 0}
    assert len(sent_payloads) == 1
    assert sent_payloads[0]["vapid_claims"] == {"sub": "mailto:events@example.org"}
    assert delivery.status == "sent"
    assert delivery.attempts == 1
    assert delivery.provider_status == 201


@pytest.mark.asyncio
async def test_send_due_event_notifications_retries_failed_delivery(
    test_session, notification_session_data
):
    _event, _subscription = notification_session_data
    calls = 0

    def sender(**_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary provider failure")
        return type("Response", (), {"status_code": 201})()

    now = datetime(2026, 10, 24, 13, 3, tzinfo=timezone.utc)
    first = await send_due_event_notifications(
        test_session, now=now, settings=enabled_settings(), sender=sender
    )
    failed = await load_delivery(test_session)
    assert failed.status == "failed"
    assert failed.attempts == 1

    second = await send_due_event_notifications(
        test_session, now=now, settings=enabled_settings(), sender=sender
    )
    retried = await load_delivery(test_session)
    assert first == {"due": 1, "sent": 0, "failed": 1, "disabled": 0}
    assert second == {"due": 1, "sent": 1, "failed": 0, "disabled": 0}
    assert calls == 2
    assert retried.status == "sent"
    assert retried.attempts == 2


def test_schedule_matches_duquantum_2026_event_window():
    assert len(DUQUANTUM_NOTIFICATIONS) == 14
    assert DUQUANTUM_NOTIFICATIONS[0].key == "sat-check-in"
    assert DUQUANTUM_NOTIFICATIONS[0].scheduled_for.isoformat() == (
        "2026-10-24T09:00:00-04:00"
    )
    assert DUQUANTUM_NOTIFICATIONS[-1].key == "sun-closing"
    assert DUQUANTUM_NOTIFICATIONS[-1].scheduled_for.isoformat() == (
        "2026-10-25T15:30:00-04:00"
    )
    assert all(item.url == "/events/duquantum-2026" for item in DUQUANTUM_NOTIFICATIONS)


def test_due_notifications_uses_a_short_idempotent_delivery_window():
    now = datetime(2026, 10, 24, 13, 3, tzinfo=timezone.utc)

    due = due_notifications(now)

    assert [item.key for item in due] == ["sat-check-in"]
    assert due_notifications(datetime(2026, 10, 24, 13, 10, tzinfo=timezone.utc)) == ()


def test_due_notifications_requires_timezone_aware_clock():
    with pytest.raises(ValueError):
        due_notifications(datetime(2026, 10, 24, 9))


def test_payload_contains_schedule_content_but_no_attendee_data():
    payload = json.loads(notification_payload(DUQUANTUM_NOTIFICATIONS[0]))

    assert payload["title"] == "DuQuantum check-in is open"
    assert payload["tag"] == "duquantum-2026-sat-check-in"
    assert set(payload) == {"title", "body", "url", "tag"}


def test_enabled_settings_require_complete_vapid_configuration(monkeypatch):
    monkeypatch.setenv("EVENT_NOTIFICATIONS_ENABLED", "true")
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("VAPID_SUBJECT", raising=False)

    with pytest.raises(RuntimeError):
        WebPushSettings.from_environment()


def test_disabled_settings_do_not_require_keys(monkeypatch):
    monkeypatch.setenv("EVENT_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("VAPID_SUBJECT", raising=False)

    settings = WebPushSettings.from_environment()

    assert settings.enabled is False
    assert settings.public_key is None
