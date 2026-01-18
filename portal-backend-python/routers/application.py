from fastapi import APIRouter, Depends, HTTPException, Security, Form as FastAPIForm, File, UploadFile, Query
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from auth import VerifyToken
from db import get_db
from models.application import Application, ApplicationStatus
from models.response import Response
from models.question import Question, QuestionType
from models.user import User
from models.form import Form as FormModel  # <-- ORM model alias
from .schema import (
    SubmitApplicationResponse,
    GetApplicationResponse,
)
from utils.s3 import upload_file_to_s3
from pydantic import BaseModel
import json

router = APIRouter()
auth = VerifyToken()


class FormStatusResponse(BaseModel):
    form_key: str
    is_open: bool


@router.get("/form-status", response_model=FormStatusResponse)
async def form_status(
    form_key: str,
    email: Optional[str] = Query(None, description="User email to check for exception override"),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    form = db.query(FormModel).filter(FormModel.form_key == form_key).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # Check if form is open OR if the email has an exception
    is_open = bool(form.is_open)
    if not is_open and email:
        exception_emails = form.exception_emails or []
        if email.lower() in [e.lower() for e in exception_emails]:
            is_open = True

    return FormStatusResponse(form_key=form_key, is_open=is_open)


@router.post("/submit", response_model=SubmitApplicationResponse)
async def submit_application(
    form_key: str = FastAPIForm(...),   # <-- use FastAPIForm (not ORM model)
    form_data: str = FastAPIForm(...),
    auth0_email: Optional[str] = FastAPIForm(None),  # For exception list checking
    files: List[UploadFile] = File(default=[]),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    # Parse form data early to check for email exception
    try:
        parsed_form_data = json.loads(form_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid form_data JSON")

    # Ensure form exists and is open (or user has exception)
    form = db.query(FormModel).filter(FormModel.form_key == form_key).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    if not form.is_open:
        # Check if user's Auth0 email has an exception
        exception_emails = form.exception_emails or []
        email_to_check = (auth0_email or "").lower()
        has_exception = email_to_check and email_to_check in [e.lower() for e in exception_emails]
        if not has_exception:
            raise HTTPException(status_code=403, detail="Form is closed")

    user = (
        db.query(User).filter(User.auth0_id == auth0_id).first()
    )  # TODO: User creation should not be handled here
    if not user:
        user = User(auth0_id=auth0_id)
        db.add(user)
        db.flush()

    existing_application = (
        db.query(Application)
        .filter(Application.user_id == user.id, Application.form_key == form_key)
        .first()
    )

    if existing_application:
        raise HTTPException(
            status_code=400,
            detail="Application already exists for this user for this form",
        )

    application = Application(
        user_id=user.id,
        form_key=form_key,
        status=ApplicationStatus.PENDING,
    )

    db.add(application)
    db.flush()

    valid_form_data = {}

    file_map = {file.filename: file for file in files if file.filename}

    for question_key, field_value in parsed_form_data.items():
        question = (
            db.query(Question)
            .filter(
                Question.form_key == form_key,
                Question.question_key == question_key,
            )
            .first()
        )

        if not question:
            continue

        if question.question_type == QuestionType.FILE:
            filename = str(field_value) if field_value else None
            if filename and filename in file_map:
                file = file_map[filename]

                s3_key = f"{form_key}/{application.id}/{question_key}/{file.filename}"
                await upload_file_to_s3(
                    file,
                    s3_key,
                )

                response = Response(
                    user_id=user.id,
                    question_id=question.id,
                    application_id=application.id,
                    file_s3_key=s3_key,
                )
                db.add(response)

                valid_form_data[question_key] = s3_key
        else:
            response = Response(
                user_id=user.id,
                question_id=question.id,
                application_id=application.id,
                text_answer=str(field_value) if field_value is not None else None,
                bool_answer=field_value if isinstance(field_value, bool) else None,
            )
            db.add(response)

            valid_form_data[question_key] = field_value

    user.first_name = valid_form_data.get("first_name")
    user.last_name = valid_form_data.get("last_name")
    user.email = valid_form_data.get("email")

    application.submission_json = valid_form_data

    db.commit()

    return SubmitApplicationResponse(applicationId=application.id)


@router.get("", response_model=GetApplicationResponse)
async def get_application(
    form_key: str,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    application = (
        db.query(Application)
        .filter(Application.user_id == user.id, Application.form_key == form_key)
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404, detail="Application not found with this authentication"
        )

    form_data = application.submission_json or {}

    return GetApplicationResponse(
        id=application.id,
        status=application.status,
        created_at=application.created_at,
        form_data=form_data,
    )
