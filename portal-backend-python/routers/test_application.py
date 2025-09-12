import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from models.application import Application, ApplicationStatus
from models.user import User
from models.form import Form
from routers.application import router
from fastapi import FastAPI
from db import get_db
from routers.application import auth
from routers.schema import GetApplicationResponse

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def setup_dependency_overrides(test_session, sample_auth_payload):
    def override_get_db():
        yield test_session

    app.dependency_overrides[auth.verify] = lambda: sample_auth_payload
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def sample_auth_payload():
    return {"sub": "auth0|test_user_123"}


@pytest.fixture
def sample_form(test_session):
    form = Form(form_key="test_form", year=2024)
    test_session.add(form)
    test_session.flush()
    return form


@pytest.fixture
def sample_user(test_session):
    user = User(auth0_id="auth0|test_user_123")
    test_session.add(user)
    test_session.flush()
    return user


@pytest.fixture
def sample_application(test_session, sample_user, sample_form):
    application = Application(
        user_id=sample_user.id,
        form_key=sample_form.form_key,
        status=ApplicationStatus.PENDING,
        submission_json={"name": "John Doe", "email": "john@example.com"},
    )
    test_session.add(application)
    test_session.flush()
    return application


class TestGetApplication:
    def test_get_application_success(
        self,
        setup_dependency_overrides,
        sample_user,
        sample_application,
    ):
        response = client.get("/application")

        assert response.status_code == 200
        data = GetApplicationResponse(**response.json())
        assert data.id == sample_application.id
        assert data.status == ApplicationStatus.PENDING
        assert data.form_data == {"name": "John Doe", "email": "john@example.com"}

    def test_get_application_user_not_found(self, setup_dependency_overrides):
        response = client.get("/application")

        assert response.status_code == 404

    def test_get_application_not_found(
        self,
        setup_dependency_overrides,
        sample_user,
    ):
        response = client.get("/application")

        assert response.status_code == 404


class TestGetApplicationById:
    def test_get_application_by_id_success(
        self,
        setup_dependency_overrides,
        sample_application,
    ):
        response = client.get(f"/application/{sample_application.id}")

        assert response.status_code == 200
        data = GetApplicationResponse(**response.json())
        assert data.id == sample_application.id
        assert data.status == ApplicationStatus.PENDING
        assert data.form_data == {"name": "John Doe", "email": "john@example.com"}

    def test_get_application_by_id_not_found(self, setup_dependency_overrides):
        fake_id = uuid4()
        response = client.get(f"/application/{fake_id}")

        assert response.status_code == 404

    def test_get_application_by_id_invalid_uuid(self, setup_dependency_overrides):
        response = client.get("/application/invalid-uuid")

        assert response.status_code == 422
