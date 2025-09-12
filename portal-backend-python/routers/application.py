from fastapi import APIRouter, Depends, HTTPException, Security, Form, File, UploadFile
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from auth import VerifyToken
from db import get_db
from models.application import Application, ApplicationStatus
from models.response import Response
from models.question import Question, QuestionType
from models.user import User
from .schema import (
    SubmitApplicationResponse,
    GetApplicationResponse,
)
from utils.s3 import upload_file_to_s3
import json

router = APIRouter()
auth = VerifyToken()


@router.post("/submit", response_model=SubmitApplicationResponse)
async def submit_application(
    form_key: str = Form(...),
    form_data: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        user = User(auth0_id=auth0_id)
        db.add(user)
        db.flush()

    existing_application = (
        db.query(Application).filter(Application.user_id == user.id).first()
    )

    if existing_application:
        raise HTTPException(
            status_code=400, detail="Application already exists for this user"
        )

    try:
        parsed_form_data = json.loads(form_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid form_data JSON")

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

        if question:
            if question.question_type == QuestionType.FILE:
                if question_key in file_map:
                    file = file_map[question_key]

                    s3_key = (
                        f"{user.id}/{application.id}/{question_key}/{file.filename}"
                    )
                    await upload_file_to_s3(
                        file,
                        s3_key,
                    )

                    if s3_key:
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

    application.submission_json = valid_form_data

    db.commit()

    return SubmitApplicationResponse(applicationId=application.id)


@router.get("/application", response_model=GetApplicationResponse)
async def get_application(
    auth_payload: Dict[str, Any] = Security(auth.verify), db: Session = Depends(get_db)
):
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    application = db.query(Application).filter(Application.user_id == user.id).first()

    if not application:
        raise HTTPException(
            status_code=404, detail="Application not found with this authentication"
        )

    form_data = application.submission_json or {}

    return GetApplicationResponse(
        id=application.id,
        status=application.status,
        form_data=form_data,
    )


@router.get("/application/{id}", response_model=GetApplicationResponse)
async def get_application_by_id(
    id: UUID,
    _: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    application = db.query(Application).filter(Application.id == id).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    form_data = application.submission_json or {}

    return GetApplicationResponse(
        id=application.id,
        status=application.status,
        form_data=form_data,
    )
