import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from models.application import Application, ApplicationStatus
from models.user import User
from models.form import Form
from models.question import Question, QuestionType
from routers.application import router
from fastapi import FastAPI
from db import get_db
from routers.application import auth
from routers.schema import GetApplicationResponse, SubmitApplicationResponse
from moto import mock_aws
from models.response import Response
import boto3
import json

app = FastAPI()
app.include_router(prefix="/application", router=router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_dependency_overrides(
    test_session,
):  # override fastapi dependency injections (https://fastapi.tiangolo.com/advanced/testing-dependencies/)
    app.dependency_overrides[auth.verify] = lambda: {"sub": "auth0|test_user_123"}
    app.dependency_overrides[get_db] = lambda: (yield test_session)


@pytest.fixture
def sample_form(test_session):
    form = Form(form_key="test_form", year=2025, is_open=True)
    test_session.add(form)
    test_session.flush()

    q1 = Question(
        form_key=form.form_key, question_key="name", question_type=QuestionType.TEXT
    )
    test_session.add(q1)
    test_session.flush()

    q2 = Question(
        form_key=form.form_key, question_key="email", question_type=QuestionType.TEXT
    )
    test_session.add(q2)
    test_session.flush()

    file_question = Question(
        form_key=form.form_key, question_key="file", question_type=QuestionType.FILE
    )
    test_session.add(file_question)
    test_session.flush()

    return form


@pytest.fixture
def sample_user(test_session):
    user = User(auth0_id="auth0|test_user_123")
    test_session.add(user)
    test_session.flush()
    return user


class TestApplication:
    def test_get_application_success(
        self,
        sample_user,
        sample_form,
        test_session,
    ):
        application = Application(
            user_id=sample_user.id,
            form_key=sample_form.form_key,
            status=ApplicationStatus.PENDING,
            submission_json={"name": "John Doe", "email": "john@example.com"},
        )
        test_session.add(application)
        test_session.flush()

        response = client.get("application", params={"form_key": "test_form"})

        assert response.status_code == 200
        data = GetApplicationResponse(**response.json())
        assert data.id == application.id
        assert data.status == ApplicationStatus.PENDING
        assert data.form_data == {"name": "John Doe", "email": "john@example.com"}

    @mock_aws
    def test_submit_application_success(
        self,
        monkeypatch,
        sample_user,
        sample_form,
        test_session,
    ):
        s3 = boto3.resource("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test")
        monkeypatch.setenv("S3_BUCKET_NAME", "test")

        form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "file": "test.pdf",
        }
        files = [
            (
                "files",
                (
                    "test.pdf",
                    b"I love HackDuke!",
                    "application/pdf",
                ),
            )
        ]

        response = client.post(
            "application/submit",
            params={"form_key": "test_form"},
            data={
                "form_key": "test_form",
                "form_data": json.dumps(form_data),
            },
            files=files,
        )

        response_obj = SubmitApplicationResponse(**response.json())
        assert response.status_code == 200
        assert response_obj.applicationId is not None

        application = (
            test_session.query(Application)
            .filter(Application.id == response_obj.applicationId)
            .first()
        )
        assert application is not None
        assert application.status == ApplicationStatus.PENDING
        assert application.user_id == sample_user.id

        for key, value in form_data.items():
            if key != "file":
                assert application.submission_json[key] == value

        questions = (
            test_session.query(Question)
            .filter(Question.form_key == sample_form.form_key)
            .all()
        )

        response = (
            test_session.query(Response)
            .filter(Response.application_id == application.id)
            .all()
        )
        assert len(response) == 3

        assert response[0].question_id == questions[0].id
        assert response[0].text_answer == form_data["name"]
        assert response[1].question_id == questions[1].id
        assert response[1].text_answer == form_data["email"]
        assert response[2].question_id == questions[2].id

        s3_key = response[2].file_s3_key
        file_obj = s3.Object("test", s3_key)
        assert file_obj.get()["Body"].read() == b"I love HackDuke!"
