from types import SimpleNamespace

import pytest

from filter_pending_duquantum_recipients import pending_emails


def row(email, **overrides):
    values = dict(normalized_email=email, admission_status="accepted", rsvp_status="confirmed", user_id=None, claimed_at=None)
    values.update(overrides)
    return SimpleNamespace(**values)


def test_refresh_excludes_completed_ineligible_and_previously_reminded_accounts():
    records = [
        row("pending@example.org"),
        row("connected@example.org", user_id="user"),
        row("claimed@example.org", claimed_at="timestamp"),
        row("declined@example.org", admission_status="rejected"),
        row("unconfirmed@example.org", rsvp_status="pending"),
        row("reminded@example.org"),
    ]
    requested = [record.normalized_email for record in records]
    assert pending_emails(requested, records, {"reminded@example.org"}) == ["pending@example.org"]


def test_refresh_refuses_missing_ambiguous_or_extra_registrations():
    requested = ["pending@example.org"]
    for records in ([], [row(requested[0]), row(requested[0])], [row("other@example.org")]):
        with pytest.raises(ValueError, match="unique registrations"):
            pending_emails(requested, records, set())
