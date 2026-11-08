from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest
from send_duquantum_test_invitation import _retire_test_registration


def record(**overrides):
    fields = dict(source="manual_test_invitation", source_data={"purpose": "operator_test_invitation"}, first_name="Derek", last_name="Wang", admission_status="accepted", rsvp_status="confirmed", account_setup=SimpleNamespace(expires_at=datetime.now(timezone.utc) + timedelta(days=7)), event_pass=SimpleNamespace(state="active", revoked_at=None))
    fields.update(overrides)
    return SimpleNamespace(**fields)


def test_email_correction_expires_old_setup_and_revokes_only_its_event_access():
    old = record()
    now = datetime.now(timezone.utc)
    _retire_test_registration(old, first_name="Derek", last_name="Wang", now=now)
    assert old.admission_status == "revoked"
    assert old.rsvp_status == "declined"
    assert old.account_setup.expires_at == now
    assert old.event_pass.state == "revoked"
    assert old.event_pass.revoked_at == now


@pytest.mark.parametrize("overrides", [{"source": "google_forms_csv"}, {"last_name": "Other"}, {"source_data": {}}])
def test_correction_refuses_to_retire_an_unrelated_or_real_registration(overrides):
    old = record(**overrides)
    with pytest.raises(RuntimeError, match="matching test"):
        _retire_test_registration(old, first_name="Derek", last_name="Wang", now=datetime.now(timezone.utc))
    assert old.admission_status == "accepted"
