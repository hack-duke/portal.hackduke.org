import pytest
import pytest_asyncio
from sqlalchemy import select, delete

from httpx2 import ASGITransport, AsyncClient
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
from models.response import Response
from aioboto3 import Session
from aiomoto import mock_aws
import json

pytestmark = pytest.mark.asyncio


app = FastAPI()
app.include_router(prefix="/application", router=router)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(autouse=True)
async def setup_dependency_overrides(
    test_session,
):  # override fastapi dependency injections (https://fastapi.tiangolo.com/advanced/testing-dependencies/)
    app.dependency_overrides[auth.verify] = lambda: {"sub": "auth0|test_user_123"}
    async def override_db():
        yield test_session

    app.dependency_overrides[get_db] = override_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_form(test_session):
    form = Form(form_key="test_form", year=2025, is_open=True)
    test_session.add(form)
    await test_session.flush()

    q1 = Question(
        form_key=form.form_key, question_key="name", question_type=QuestionType.TEXT
    )
    test_session.add(q1)
    await test_session.flush()

    q2 = Question(
        form_key=form.form_key, question_key="email", question_type=QuestionType.TEXT
    )
    test_session.add(q2)
    await test_session.flush()

    file_question = Question(
        form_key=form.form_key, question_key="file", question_type=QuestionType.FILE
    )
    test_session.add(file_question)
    await test_session.flush()

    return form


@pytest_asyncio.fixture
async def sample_user(test_session):
    user = User(auth0_id="auth0|test_user_123")
    test_session.add(user)
    await test_session.flush()
    return user


class TestApplication:
    async def test_get_application_success(
        self,
        sample_user,
        sample_form,
        test_session, client,
    ):
        application = Application(
            user_id=sample_user.id,
            form_key=sample_form.form_key,
            status=ApplicationStatus.PENDING,
            submission_json={"name": "John Doe", "email": "john@example.com"},
        )
        test_session.add(application)
        await test_session.flush()

        response = (await client.get("application", params={"form_key": "test_form"}))

        assert response.status_code == 200
        data = GetApplicationResponse(**response.json())
        assert data.id == application.id
        assert data.status == ApplicationStatus.PENDING
        assert data.form_data == {"name": "John Doe", "email": "john@example.com"}

    async def test_submit_application_success(
        self,
        monkeypatch,
        sample_user,
        sample_form,
        test_session, client,
    ):
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
        monkeypatch.setenv("AWS_REGION", "us-east-1")
        monkeypatch.setenv("S3_BUCKET_NAME", "test")
        async with mock_aws():
            async with Session().resource("s3", region_name="us-east-1") as s3:
                await s3.create_bucket(Bucket="test")

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

                response = await client.post(
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
                    await test_session.scalars(
                        select(Application)
                        .filter(Application.id == response_obj.applicationId)
                        .limit(1)
                    )
                ).first()
                assert application is not None
                assert application.status == ApplicationStatus.PENDING
                assert application.user_id == sample_user.id

                for key, value in form_data.items():
                    if key != "file":
                        assert application.submission_json[key] == value

                questions = (
                    await test_session.scalars(
                        select(Question).filter(
                            Question.form_key == sample_form.form_key
                        )
                    )
                ).all()

                responses = (
                    await test_session.scalars(
                        select(Response).filter(
                            Response.application_id == application.id
                        )
                    )
                ).all()
                assert len(responses) == 3

                assert responses[0].question_id == questions[0].id
                assert responses[0].text_answer == form_data["name"]
                assert responses[1].question_id == questions[1].id
                assert responses[1].text_answer == form_data["email"]
                assert responses[2].question_id == questions[2].id

                s3_object = await s3.Object("test", responses[2].file_s3_key)
                file_response = await s3_object.get()
                assert await file_response["Body"].read() == b"I love HackDuke!"
