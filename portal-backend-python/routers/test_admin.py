import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timedelta
import json

from models.user import User
from models.admin_user import AdminUser
from models.application import Application, ApplicationStatus
from models.form import Form
from models.question import Question, QuestionType
from routers.admin import router
from fastapi import FastAPI
from db import get_db
from routers.admin import auth

app = FastAPI()
app.include_router(prefix="/admin", router=router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_dependency_overrides(test_session):
    """Override FastAPI dependency injections for testing."""
    # Always clear before setting up
    app.dependency_overrides.clear()
    # Set default overrides
    app.dependency_overrides[auth.verify] = lambda: {"sub": "auth0|admin_user_123"}
    app.dependency_overrides[get_db] = lambda: (yield test_session)
    yield
    # Clear overrides after test to prevent pollution
    app.dependency_overrides.clear()


@pytest.fixture
def test_admin_user(test_session):
    """Create a test admin user."""
    auth0_id = "auth0|admin_user_123"
    # Delete any existing user with this auth0_id from previous test runs
    test_session.query(User).filter(User.auth0_id == auth0_id).delete()
    test_session.flush()
    
    user = User(auth0_id=auth0_id)
    test_session.add(user)
    test_session.flush()
    
    admin = AdminUser(user_id=user.id)
    test_session.add(admin)
    test_session.flush()
    
    return user, admin


@pytest.fixture
def test_non_admin_user(test_session):
    """Create a test non-admin user."""
    auth0_id = "auth0|regular_user_123"
    # Delete any existing user with this auth0_id from previous test runs
    test_session.query(User).filter(User.auth0_id == auth0_id).delete()
    test_session.flush()
    
    user = User(auth0_id=auth0_id)
    test_session.add(user)
    test_session.flush()
    return user


@pytest.fixture
def test_form(test_session):
    """Create a test form."""
    form_key = "2026-cfg-application"  # Must match CURRENT_FORM_KEY in admin.py
    # Delete any existing form with this key from previous test runs
    test_session.query(Form).filter(Form.form_key == form_key).delete()
    test_session.flush()

    form = Form(form_key=form_key, year=2026, is_open=True)
    test_session.add(form)
    test_session.flush()
    return form


@pytest.fixture
def pending_applications(test_session, test_non_admin_user, test_form):
    """Create test pending applications."""
    apps = []
    for i in range(3):
        app = Application(
            user_id=test_non_admin_user.id,
            form_key=test_form.form_key,
            status=ApplicationStatus.PENDING,
            submission_json={"name": f"Applicant {i}", "email": f"user{i}@example.com"},
        )
        test_session.add(app)
        test_session.flush()
        apps.append(app)
    return apps


class TestAdminAuth:
    def test_admin_check_success(self, test_admin_user, test_session):
        """Test successful admin check."""
        response = client.post("/admin/auth/check")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_admin"] is True
        assert data["session_id"] is not None

    def test_non_admin_check(self, test_non_admin_user, test_session):
        """Test non-admin user cannot access admin panel."""
        app.dependency_overrides[auth.verify] = lambda: {"sub": "auth0|regular_user_123"}
        
        response = client.post("/admin/auth/check")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_admin"] is False
        assert data["session_id"] is None

    def test_session_invalidation_on_new_login(self, test_admin_user, test_session):
        """Test that logging in on a new tab invalidates the old session."""
        # First login
        response1 = client.post("/admin/auth/check")
        session_id_1 = response1.json()["session_id"]
        
        # Refresh the admin user from db to get latest session_id
        test_session.refresh(test_admin_user[1])
        assert test_admin_user[1].current_session_id == session_id_1
        
        # Second login (simulating new tab)
        response2 = client.post("/admin/auth/check")
        session_id_2 = response2.json()["session_id"]
        
        assert session_id_1 != session_id_2
        
        # Verify old session is invalid
        response_ping = client.get(
            "/admin/ping",
            params={"session_id": session_id_1}
        )
        assert response_ping.status_code == 403

    def test_unauthenticated_request(self, test_session):
        """Test that unauthenticated requests are rejected."""
        # Override with a bad auth that raises an exception
        from fastapi import HTTPException
        
        def mock_verify_fails():
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        app.dependency_overrides[auth.verify] = mock_verify_fails
        
        response = client.post("/admin/auth/check")
        assert response.status_code == 401


class TestNextApplication:
    def test_get_next_application_success(
        self, test_admin_user, pending_applications, test_session
    ):
        """Test getting the next pending application."""
        # First, authenticate
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        # Get next application
        response = client.get(
            "/admin/next-application",
            params={"session_id": session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(pending_applications[0].id)
        assert data["status"] == "pending"
        assert data["submission_json"]["name"] == "Applicant 0"

    def test_application_gets_locked(
        self, test_admin_user, pending_applications, test_session
    ):
        """Test that application gets locked when retrieved."""
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        # Get application
        client.get(
            "/admin/next-application",
            params={"session_id": session_id}
        )
        
        # Check it's locked
        app = test_session.query(Application).filter(
            Application.id == pending_applications[0].id
        ).first()
        assert app.locked_by is not None
        assert app.locked_at is not None

    def test_locked_application_not_given_to_other_admin(
        self, test_admin_user, test_session, test_form, test_non_admin_user
    ):
        """Test that locked applications are not given to other admins."""
        # Create two admins
        admin2_auth0_id = f"auth0|admin_user_{uuid4()}"
        admin2_user = User(auth0_id=admin2_auth0_id)
        test_session.add(admin2_user)
        test_session.flush()
        
        admin2 = AdminUser(user_id=admin2_user.id)
        test_session.add(admin2)
        test_session.flush()
        
        # Create two pending apps
        app1 = Application(
            user_id=test_non_admin_user.id,
            form_key=test_form.form_key,
            status=ApplicationStatus.PENDING,
            submission_json={"name": "App 1"},
        )
        app2 = Application(
            user_id=test_non_admin_user.id,
            form_key=test_form.form_key,
            status=ApplicationStatus.PENDING,
            submission_json={"name": "App 2"},
        )
        test_session.add(app1)
        test_session.add(app2)
        test_session.flush()
        
        # Admin1 gets app1
        auth_response1 = client.post("/admin/auth/check")
        session_id1 = auth_response1.json()["session_id"]
        
        response1 = client.get(
            "/admin/next-application",
            params={"session_id": session_id1}
        )
        retrieved_app1_id = response1.json()["id"]
        
        # Admin2 tries to get next app (should get app2, not app1)
        app.dependency_overrides[auth.verify] = lambda: {"sub": admin2_auth0_id}
        auth_response2 = client.post("/admin/auth/check")
        session_id2 = auth_response2.json()["session_id"]
        
        response2 = client.get(
            "/admin/next-application",
            params={"session_id": session_id2}
        )
        retrieved_app2_id = response2.json()["id"]
        
        assert retrieved_app1_id != retrieved_app2_id
        assert retrieved_app2_id == str(app2.id)

    def test_no_pending_applications(self, test_admin_user, test_session, test_form, test_non_admin_user):
        """Test that 404 is returned when no pending applications exist."""
        # Don't use pending_applications fixture - create a clean state with no pending apps
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        response = client.get(
            "/admin/next-application",
            params={"session_id": session_id}
        )
        
        assert response.status_code == 404

    def test_invalid_session(self, test_admin_user, pending_applications, test_session):
        """Test that invalid session is rejected."""
        response = client.get(
            "/admin/next-application",
            params={"session_id": "invalid_session_id"}
        )
        
        assert response.status_code == 403


class TestSubmitDecision:
    def test_accept_decision(
        self, test_admin_user, pending_applications, test_session
    ):
        """Test accepting an application."""
        # Get application and lock it
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        app_response = client.get(
            "/admin/next-application",
            params={"session_id": session_id}
        )
        app_id = app_response.json()["id"]
        
        # Submit decision
        decision_response = client.post(
            f"/admin/application/{app_id}/decision",
            json={"decision": "accept"},
            params={"session_id": session_id}
        )
        
        assert decision_response.status_code == 200
        data = decision_response.json()
        assert data["status"].lower() == "accepted"
        
        # Verify in database
        app = test_session.query(Application).filter(
            Application.id == pending_applications[0].id
        ).first()
        assert app.status == ApplicationStatus.ACCEPTED
        assert app.decided_by is not None
        assert app.locked_by is None  # Should be unlocked

    def test_reject_decision(
        self, test_admin_user, pending_applications, test_session
    ):
        """Test rejecting an application."""
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        app_response = client.get(
            "/admin/next-application",
            params={"session_id": session_id}
        )
        app_id = app_response.json()["id"]
        
        # Submit decision
        decision_response = client.post(
            f"/admin/application/{app_id}/decision",
            json={"decision": "reject"},
            params={"session_id": session_id}
        )
        
        assert decision_response.status_code == 200
        data = decision_response.json()
        assert data["status"] == "rejected"
        
        # Verify in database
        app = test_session.query(Application).filter(
            Application.id == pending_applications[0].id
        ).first()
        assert app.status == ApplicationStatus.REJECTED
        assert app.decided_by is not None

    def test_pending_decision_clears_decided_by(
        self, test_admin_user, pending_applications, test_session
    ):
        """Test that changing decision back to pending clears decided_by."""
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        app_response = client.get(
            "/admin/next-application",
            params={"session_id": session_id}
        )
        app_id = app_response.json()["id"]
        
        # Accept
        client.post(
            f"/admin/application/{app_id}/decision",
            json={"decision": "accept"},
            params={"session_id": session_id}
        )
        
        # Verify decided_by is set
        app_obj = test_session.query(Application).filter(
            Application.id == app_id
        ).first()
        assert app_obj.status == ApplicationStatus.ACCEPTED
        assert app_obj.decided_by is not None
        admin_user_id = test_admin_user[0].id
        
        # Now we need to get the app again to lock it (since accepting unlocks it)
        # Then we can change decision back to pending
        app_response2 = client.get(
            "/admin/next-application",
            params={"session_id": session_id}
        )
        
        # It should return the accepted app since it's pending now... wait, accepted apps aren't pending
        # So let's manually re-lock it instead
        app_obj.locked_by = admin_user_id
        app_obj.locked_at = datetime.utcnow()
        test_session.flush()
        
        # Now change decision back to pending
        decision_response = client.post(
            f"/admin/application/{app_id}/decision",
            json={"decision": "pending"},
            params={"session_id": session_id}
        )
        
        assert decision_response.status_code == 200
        
        # Verify decided_by is cleared and status is pending
        test_session.refresh(app_obj)
        assert app_obj.status == ApplicationStatus.PENDING
        assert app_obj.decided_by is None

    def test_cannot_decide_without_lock(
        self, test_admin_user, pending_applications, test_session
    ):
        """Test that admin cannot decide on app they don't have locked."""
        # Create another admin
        admin2_auth0_id = f"auth0|admin_user_{uuid4()}"
        admin2_user = User(auth0_id=admin2_auth0_id)
        test_session.add(admin2_user)
        test_session.flush()
        
        admin2 = AdminUser(user_id=admin2_user.id)
        test_session.add(admin2)
        test_session.flush()
        
        # Admin1 locks app
        auth_response1 = client.post("/admin/auth/check")
        session_id1 = auth_response1.json()["session_id"]
        
        app_response = client.get(
            "/admin/next-application",
            params={"session_id": session_id1}
        )
        app_id = app_response.json()["id"]
        
        # Admin2 tries to decide
        app.dependency_overrides[auth.verify] = lambda: {"sub": admin2_auth0_id}
        auth_response2 = client.post("/admin/auth/check")
        session_id2 = auth_response2.json()["session_id"]
        
        decision_response = client.post(
            f"/admin/application/{app_id}/decision",
            json={"decision": "accept"},
            params={"session_id": session_id2}
        )
        
        assert decision_response.status_code == 403

    def test_invalid_decision(
        self, test_admin_user, pending_applications, test_session
    ):
        """Test that invalid decision is rejected."""
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        app_response = client.get(
            "/admin/next-application",
            params={"session_id": session_id}
        )
        app_id = app_response.json()["id"]
        
        decision_response = client.post(
            f"/admin/application/{app_id}/decision",
            json={"decision": "maybe"},
            params={"session_id": session_id}
        )
        
        assert decision_response.status_code == 400


class TestStats:
    def test_stats_global_and_personal(
        self, test_admin_user, test_session, test_form, test_non_admin_user
    ):
        """Test that stats return both global and personal counts."""
        admin_user_obj = test_admin_user[0]  # test_admin_user is (user, admin) tuple
        
        # Create applications in different states
        accepted_by_admin = Application(
            user_id=test_non_admin_user.id,
            form_key=test_form.form_key,
            status=ApplicationStatus.ACCEPTED,
            decided_by=admin_user_obj.id,
        )
        rejected_by_admin = Application(
            user_id=test_non_admin_user.id,
            form_key=test_form.form_key,
            status=ApplicationStatus.REJECTED,
            decided_by=admin_user_obj.id,
        )
        pending = Application(
            user_id=test_non_admin_user.id,
            form_key=test_form.form_key,
            status=ApplicationStatus.PENDING,
        )
        
        test_session.add_all([accepted_by_admin, rejected_by_admin, pending])
        test_session.flush()
        
        # Get stats
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        stats_response = client.get(
            "/admin/stats",
            params={"session_id": session_id}
        )
        
        assert stats_response.status_code == 200
        data = stats_response.json()
        
        # Global stats
        assert data["total_pending"] == 1
        assert data["total_accepted"] == 1
        assert data["total_rejected"] == 1
        
        # Personal stats
        assert data["user_accepted"] == 1
        assert data["user_rejected"] == 1

    def test_stats_requires_valid_session(self, test_admin_user, test_session):
        """Test that invalid session is rejected."""
        response = client.get(
            "/admin/stats",
            params={"session_id": "invalid_session_id"}
        )
        
        assert response.status_code == 403


class TestPing:
    def test_ping_success(self, test_admin_user, test_session):
        """Test that valid session responds to ping."""
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        ping_response = client.get(
            "/admin/ping",
            params={"session_id": session_id}
        )
        
        assert ping_response.status_code == 200
        assert ping_response.json()["status"] == "ok"

    def test_ping_invalid_session(self, test_admin_user, test_session):
        """Test that invalid session fails ping."""
        response = client.get(
            "/admin/ping",
            params={"session_id": "invalid_session_id"}
        )
        
        assert response.status_code == 403


class TestLogout:
    def test_logout_clears_session(self, test_admin_user, test_session):
        """Test that logout clears the session."""
        # Login
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        # Logout
        logout_response = client.post("/admin/logout")
        assert logout_response.status_code == 200
        
        # Verify session is cleared
        ping_response = client.get(
            "/admin/ping",
            params={"session_id": session_id}
        )
        assert ping_response.status_code == 403

    def test_logout_releases_locks(
        self, test_admin_user, pending_applications, test_session
    ):
        """Test that logout releases all locks held by the admin."""
        admin_user_obj = test_admin_user[0]  # test_admin_user is (user, admin) tuple
        
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        # Lock multiple apps
        for _ in range(2):
            client.get(
                "/admin/next-application",
                params={"session_id": session_id}
            )
        
        # Logout
        client.post("/admin/logout")
        
        # Verify locks are released
        locked_apps = test_session.query(Application).filter(
            Application.locked_by == admin_user_obj.id
        ).all()
        assert len(locked_apps) == 0


class TestLockTimeout:
    def test_expired_lock_is_released(
        self, test_admin_user, test_session, test_form, test_non_admin_user
    ):
        """Test that expired locks are released when getting next application."""
        admin_user_obj = test_admin_user[0]  # test_admin_user is (user, admin) tuple
        
        # Create a single pending app with an old lock
        app_with_expired_lock = Application(
            user_id=test_non_admin_user.id,
            form_key=test_form.form_key,
            status=ApplicationStatus.PENDING,
            submission_json={"name": "App with expired lock"},
            locked_by=admin_user_obj.id,
            locked_at=datetime.utcnow() - timedelta(hours=2),
        )
        test_session.add(app_with_expired_lock)
        test_session.flush()
        
        # Now get next application from a different admin
        other_admin_auth0_id = f"auth0|admin_user_{uuid4()}"
        app.dependency_overrides[auth.verify] = lambda: {"sub": other_admin_auth0_id}
        other_admin_user = User(auth0_id=other_admin_auth0_id)
        test_session.add(other_admin_user)
        test_session.flush()
        
        other_admin = AdminUser(user_id=other_admin_user.id)
        test_session.add(other_admin)
        test_session.flush()
        
        auth_response = client.post("/admin/auth/check")
        session_id = auth_response.json()["session_id"]
        
        app_response = client.get(
            "/admin/next-application",
            params={"session_id": session_id}
        )
        
        # Should be able to get the old app (lock was expired)
        assert app_response.status_code == 200
        assert app_response.json()["id"] == str(app_with_expired_lock.id)
