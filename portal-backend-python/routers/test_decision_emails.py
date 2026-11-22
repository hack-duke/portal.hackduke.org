import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from db import get_db
from models.application import Application, ApplicationStatus
from models.form import Form
from models.user import User
from models.user_role import UserRole, RoleEnum
from routers.admin import auth, router
from services import decision_emails

app = FastAPI()
app.include_router(prefix="/admin", router=router)
client = TestClient(app)

ADMIN_SUB = "auth0|decision_email_admin"
APPLICANT_SUB = "auth0|decision_email_applicant"
FORM_KEY = "2026-cfg-application"  # must match CURRENT_FORM_KEY in admin.py


class FakeSES:
    def __init__(self, fail_for=()):
        self.sent = []
        self.fail_for = set(fail_for)

    def send_email(self, Source, Destination, Message):
        to = Destination["ToAddresses"][0]
        if to in self.fail_for:
            raise RuntimeError("SES rejected")
        self.sent.append(
            {
                "source": Source,
                "to": Destination["ToAddresses"],
                "subject": Message["Subject"]["Data"],
                "html": Message["Body"]["Html"]["Data"],
            }
        )
        return {"MessageId": f"msg-{len(self.sent)}"}


@pytest.fixture
def fake_ses(monkeypatch):
    ses = FakeSES()
    monkeypatch.setattr(decision_emails, "get_ses_client", lambda: ses)
    monkeypatch.setenv("SES_SENDER_EMAIL", "HackDuke <team@hackduke.org>")
    monkeypatch.setenv("SES_MAX_SEND_RATE", "1000")
    monkeypatch.setenv("DECISION_EMAIL_EVENT_NAME", "Code for Good 2026")
    return ses


@pytest.fixture(autouse=True)
def overrides(test_session):
    app.dependency_overrides.clear()
    app.dependency_overrides[auth.verify] = lambda: {"sub": ADMIN_SUB}
    app.dependency_overrides[get_db] = lambda: (yield test_session)
    yield
    app.dependency_overrides.clear()


def _user(test_session, sub, admin=False):
    test_session.query(User).filter(User.auth0_id == sub).delete()
    test_session.flush()
    user = User(auth0_id=sub, first_name="Fallback", email="fallback@example.com")
    test_session.add(user)
    test_session.flush()
    if admin:
        test_session.add(UserRole(user_id=user.id, role=RoleEnum.ADMIN))
        test_session.flush()
    return user


@pytest.fixture
def admin_user(test_session):
    return _user(test_session, ADMIN_SUB, admin=True)


@pytest.fixture
def applicant(test_session):
    return _user(test_session, APPLICANT_SUB)


@pytest.fixture
def form(test_session):
    test_session.query(Form).filter(Form.form_key == FORM_KEY).delete()
    test_session.flush()
    f = Form(form_key=FORM_KEY, year=2026, is_open=True)
    test_session.add(f)
    test_session.flush()
    return f


@pytest.fixture
def apps(test_session, applicant, form):
    """2 accepted, 1 rejected, 1 pending, 1 confirmed."""
    specs = [
        (ApplicationStatus.ACCEPTED, {"first_name": "Ada", "email": "ada@example.com"}),
        (ApplicationStatus.ACCEPTED, {"first_name": "Ben", "pref_name": "Benji", "email": "ben@example.com"}),
        (ApplicationStatus.REJECTED, {"first_name": "<Cy>", "email": "cy@example.com"}),
        (ApplicationStatus.PENDING, {"first_name": "Dee", "email": "dee@example.com"}),
        (ApplicationStatus.CONFIRMED, {"first_name": "Eve", "email": "eve@example.com"}),
    ]
    created = []
    for status, submission in specs:
        a = Application(
            user_id=applicant.id,
            form_key=form.form_key,
            status=status,
            submission_json=submission,
        )
        test_session.add(a)
        created.append(a)
    test_session.flush()
    return created


def _session_id():
    return client.post("/admin/auth/check").json()["session_id"]


def test_preview_counts_and_samples(admin_user, apps, fake_ses):
    resp = client.get("/admin/decision-emails/preview", params={"session_id": _session_id()})
    assert resp.status_code == 200
    data = resp.json()
    assert data["counts"] == {"accepted": 2, "rejected": 1}
    assert data["total"] == 3
    assert data["already_emailed"] == 0
    assert "Code for Good 2026" in data["samples"]["accepted"]["subject"]
    assert "Hi Alex" in data["samples"]["rejected"]["html"]
    assert "<!--" not in data["samples"]["accepted"]["html"]
    assert fake_ses.sent == []  # preview never sends


def test_send_emails_each_decided_applicant_once(admin_user, apps, fake_ses, test_session):
    sid = _session_id()
    resp = client.post("/admin/decision-emails/send", params={"session_id": sid})
    assert resp.status_code == 200
    assert resp.json() == {"sent": 3, "failed": [], "skipped_missing_email": 0}

    by_to = {m["to"][0]: m for m in fake_ses.sent}
    assert set(by_to) == {"ada@example.com", "ben@example.com", "cy@example.com"}
    assert all(len(m["to"]) == 1 for m in fake_ses.sent)
    assert by_to["ada@example.com"]["source"] == "HackDuke <team@hackduke.org>"
    assert "accepted" in by_to["ada@example.com"]["html"]
    assert "Hi Benji," in by_to["ben@example.com"]["html"]  # preferred name wins
    assert "Hi &lt;Cy&gt;," in by_to["cy@example.com"]["html"]  # escaped
    assert "unable to offer you a spot" in by_to["cy@example.com"]["html"]

    test_session.expire_all()
    emailed = {a.status: a.decision_emailed_at for a in test_session.query(Application).filter(Application.form_key == FORM_KEY)}
    assert emailed[ApplicationStatus.PENDING] is None
    assert emailed[ApplicationStatus.CONFIRMED] is None

    # Pressing again sends nothing new.
    again = client.post("/admin/decision-emails/send", params={"session_id": sid})
    assert again.json()["sent"] == 0
    assert len(fake_ses.sent) == 3

    preview = client.get("/admin/decision-emails/preview", params={"session_id": sid}).json()
    assert preview["total"] == 0
    assert preview["already_emailed"] == 3


def test_failed_send_is_retried_next_time(admin_user, apps, fake_ses):
    fake_ses.fail_for = {"ben@example.com"}
    sid = _session_id()
    first = client.post("/admin/decision-emails/send", params={"session_id": sid}).json()
    assert first["sent"] == 2
    assert [f["email"] for f in first["failed"]] == ["ben@example.com"]

    fake_ses.fail_for = set()
    second = client.post("/admin/decision-emails/send", params={"session_id": sid}).json()
    assert second == {"sent": 1, "failed": [], "skipped_missing_email": 0}
    assert [m["to"][0] for m in fake_ses.sent].count("ben@example.com") == 1


def test_falls_back_to_user_email_and_skips_missing(admin_user, applicant, form, fake_ses, test_session):
    test_session.add(Application(user_id=applicant.id, form_key=FORM_KEY, status=ApplicationStatus.ACCEPTED, submission_json={}))
    nobody = _user(test_session, "auth0|no_email_applicant")
    nobody.email = None
    test_session.add(Application(user_id=nobody.id, form_key=FORM_KEY, status=ApplicationStatus.REJECTED, submission_json={}))
    test_session.flush()

    resp = client.post("/admin/decision-emails/send", params={"session_id": _session_id()}).json()
    assert resp["sent"] == 1
    assert resp["skipped_missing_email"] == 1
    assert fake_ses.sent[0]["to"] == ["fallback@example.com"]
    assert "Hi Fallback," in fake_ses.sent[0]["html"]


def test_missing_sender_config_returns_500(admin_user, apps, fake_ses, monkeypatch):
    monkeypatch.delenv("SES_SENDER_EMAIL")
    resp = client.post("/admin/decision-emails/send", params={"session_id": _session_id()})
    assert resp.status_code == 500
    assert "SES_SENDER_EMAIL" in resp.json()["detail"]
    assert fake_ses.sent == []


def test_non_admin_forbidden(applicant, apps, fake_ses):
    app.dependency_overrides[auth.verify] = lambda: {"sub": APPLICANT_SUB}
    for method, path in (("get", "/admin/decision-emails/preview"), ("post", "/admin/decision-emails/send")):
        resp = getattr(client, method)(path, params={"session_id": "whatever"})
        assert resp.status_code == 403
    assert fake_ses.sent == []


def test_invalid_session_forbidden(admin_user, apps, fake_ses):
    _session_id()
    resp = client.post("/admin/decision-emails/send", params={"session_id": "stale"})
    assert resp.status_code == 403
    assert fake_ses.sent == []
