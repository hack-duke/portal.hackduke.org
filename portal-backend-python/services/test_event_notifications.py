import json
from datetime import datetime, timezone

import pytest

from services.event_notifications import (
    DUQUANTUM_NOTIFICATIONS,
    WebPushSettings,
    due_notifications,
    notification_payload,
)


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
