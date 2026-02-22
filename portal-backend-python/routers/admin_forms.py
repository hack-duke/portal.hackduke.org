"""
Form and Question management endpoints for admin panel.
All endpoints require admin authentication (Auth0 JWT + AdminUser + session_id).
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Security
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from auth import VerifyToken
from db import get_db
from models.form import Form
from models.question import Question, QuestionType
from models.user import User
from models.admin_user import AdminUser

router = APIRouter()
auth = VerifyToken()


# ============================================================================
# Pydantic Models
# ============================================================================

class FormCreate(BaseModel):
    """Request body for creating a form."""
    form_key: str = Field(..., description="Unique form identifier (e.g., '2026-cfg-application')")
    year: int = Field(..., description="Year of the form")
    title: str = Field(..., description="Display title of the form")
    closed_message_title: Optional[str] = Field(None, description="Title shown when form is closed")
    closed_message_body: Optional[str] = Field(None, description="Message body shown when form is closed")
    is_open: bool = Field(False, description="Whether form is open for submissions")


class FormUpdate(BaseModel):
    """Request body for updating a form."""
    title: Optional[str] = None
    closed_message_title: Optional[str] = None
    closed_message_body: Optional[str] = None
    is_open: Optional[bool] = None


class FormResponse(BaseModel):
    """Response model for a form."""
    form_key: str
    year: int
    title: Optional[str]
    closed_message_title: Optional[str]
    closed_message_body: Optional[str]
    is_open: bool
    is_db_driven: bool
    question_count: int = 0

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    """Request body for creating a question."""
    question_key: str = Field(..., description="Unique identifier within the form")
    question_type: str = Field(..., description="Type: text, boolean, file, integer, float")
    label: str = Field(..., description="Display label for the question")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    description: Optional[str] = Field(None, description="Help text / description")
    required: bool = Field(False, description="Whether field is required")
    page_number: int = Field(1, description="Page number (1-based)")
    page_title: Optional[str] = Field(None, description="Title of the page")
    order_in_page: int = Field(0, description="Order within the page")
    config: Optional[Dict[str, Any]] = Field(None, description="Type-specific config (e.g., rows for textarea)")


class QuestionUpdate(BaseModel):
    """Request body for updating a question."""
    label: Optional[str] = None
    placeholder: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    page_number: Optional[int] = None
    page_title: Optional[str] = None
    order_in_page: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class QuestionResponse(BaseModel):
    """Response model for a question."""
    id: str
    form_key: str
    question_key: str
    question_type: str
    label: Optional[str]
    placeholder: Optional[str]
    description: Optional[str]
    required: bool
    page_number: int
    page_title: Optional[str]
    order_in_page: int
    config: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class ReorderQuestionsRequest(BaseModel):
    """Request body for reordering questions."""
    question_orders: List[Dict[str, Any]] = Field(
        ...,
        description="List of {question_id, page_number, order_in_page} dicts"
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _validate_admin_session(
    db: Session, auth0_id: str, session_id: str
) -> User:
    """
    Validate that the user is authenticated and is an admin with a valid session.
    Returns the User object if valid.
    Raises HTTPException if not valid.
    """
    # Get user from auth0_id
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Check if user is admin
    admin_user = db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    if not admin_user:
        raise HTTPException(status_code=403, detail="User is not an admin")

    # Validate session
    if admin_user.current_session_id != session_id:
        raise HTTPException(status_code=403, detail="Invalid or expired session")

    return user


# ============================================================================
# Form Management Endpoints
# ============================================================================

@router.get("/forms", response_model=List[FormResponse])
async def list_forms(
    session_id: str = Query(...),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
) -> List[FormResponse]:
    """List all forms, ordered by year descending."""
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    _validate_admin_session(db, auth0_id, session_id)

    forms = db.query(Form).order_by(Form.year.desc()).all()

    # Build response with question counts
    result = []
    for form in forms:
        question_count = db.query(Question).filter(
            Question.form_key == form.form_key
        ).count()
        response = FormResponse(
            form_key=form.form_key,
            year=form.year,
            title=form.title,
            closed_message_title=form.closed_message_title,
            closed_message_body=form.closed_message_body,
            is_open=form.is_open,
            is_db_driven=form.is_db_driven,
            question_count=question_count,
        )
        result.append(response)

    return result


@router.post("/forms", response_model=FormResponse)
async def create_form(
    form_data: FormCreate,
    session_id: str = Query(...),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
) -> FormResponse:
    """Create a new form."""
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    _validate_admin_session(db, auth0_id, session_id)

    # Check if form_key already exists
    existing = db.query(Form).filter(Form.form_key == form_data.form_key).first()
    if existing:
        raise HTTPException(status_code=400, detail="Form with this key already exists")

    # Create form
    new_form = Form(
        form_key=form_data.form_key,
        year=form_data.year,
        title=form_data.title,
        closed_message_title=form_data.closed_message_title,
        closed_message_body=form_data.closed_message_body,
        is_open=form_data.is_open,
        is_db_driven=True,
    )
    db.add(new_form)
    db.commit()
    db.refresh(new_form)

    return FormResponse(
        form_key=new_form.form_key,
        year=new_form.year,
        title=new_form.title,
        closed_message_title=new_form.closed_message_title,
        closed_message_body=new_form.closed_message_body,
        is_open=new_form.is_open,
        is_db_driven=new_form.is_db_driven,
        question_count=0,
    )


@router.put("/forms/{form_key}", response_model=FormResponse)
async def update_form(
    form_key: str,
    form_data: FormUpdate,
    session_id: str = Query(...),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
) -> FormResponse:
    """Update form details."""
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    _validate_admin_session(db, auth0_id, session_id)

    # Find form
    form = db.query(Form).filter(Form.form_key == form_key).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # Update fields
    if form_data.title is not None:
        form.title = form_data.title
    if form_data.closed_message_title is not None:
        form.closed_message_title = form_data.closed_message_title
    if form_data.closed_message_body is not None:
        form.closed_message_body = form_data.closed_message_body
    if form_data.is_open is not None:
        form.is_open = form_data.is_open

    db.commit()
    db.refresh(form)

    # Get question count
    question_count = db.query(Question).filter(
        Question.form_key == form.form_key
    ).count()

    return FormResponse(
        form_key=form.form_key,
        year=form.year,
        title=form.title,
        closed_message_title=form.closed_message_title,
        closed_message_body=form.closed_message_body,
        is_open=form.is_open,
        is_db_driven=form.is_db_driven,
        question_count=question_count,
    )


@router.delete("/forms/{form_key}")
async def delete_form(
    form_key: str,
    session_id: str = Query(...),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Delete a form (only if no applications exist)."""
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    _validate_admin_session(db, auth0_id, session_id)

    # Find form
    form = db.query(Form).filter(Form.form_key == form_key).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # Check if form has any applications (to prevent data loss)
    from models.application import Application
    app_count = db.query(Application).filter(
        Application.form_key == form_key
    ).count()
    if app_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete form with {app_count} application(s). Please archive or review applications first."
        )

    # Delete form (CASCADE will delete questions)
    db.delete(form)
    db.commit()

    return {"status": "deleted", "form_key": form_key}


@router.post("/forms/{form_key}/toggle-open", response_model=FormResponse)
async def toggle_form_open(
    form_key: str,
    session_id: str = Query(...),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
) -> FormResponse:
    """Toggle the is_open status of a form."""
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    _validate_admin_session(db, auth0_id, session_id)

    # Find form
    form = db.query(Form).filter(Form.form_key == form_key).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # Toggle is_open
    form.is_open = not form.is_open
    db.commit()
    db.refresh(form)

    # Get question count
    question_count = db.query(Question).filter(
        Question.form_key == form.form_key
    ).count()

    return FormResponse(
        form_key=form.form_key,
        year=form.year,
        title=form.title,
        closed_message_title=form.closed_message_title,
        closed_message_body=form.closed_message_body,
        is_open=form.is_open,
        is_db_driven=form.is_db_driven,
        question_count=question_count,
    )


# ============================================================================
# Question Management Endpoints
# ============================================================================

@router.get("/forms/{form_key}/questions", response_model=List[QuestionResponse])
async def list_questions(
    form_key: str,
    session_id: str = Query(...),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
) -> List[QuestionResponse]:
    """List all questions for a form, ordered by page_number and order_in_page."""
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    _validate_admin_session(db, auth0_id, session_id)

    # Check form exists
    form = db.query(Form).filter(Form.form_key == form_key).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # Get questions ordered
    questions = (
        db.query(Question)
        .filter(Question.form_key == form_key)
        .order_by(Question.page_number.asc(), Question.order_in_page.asc())
        .all()
    )

    result = [
        QuestionResponse(
            id=str(q.id),
            form_key=q.form_key,
            question_key=q.question_key,
            question_type=q.question_type.value,
            label=q.label,
            placeholder=q.placeholder,
            description=q.description,
            required=q.required,
            page_number=q.page_number,
            page_title=q.page_title,
            order_in_page=q.order_in_page,
            config=q.config,
        )
        for q in questions
    ]

    return result


@router.post("/forms/{form_key}/questions", response_model=QuestionResponse)
async def create_question(
    form_key: str,
    question_data: QuestionCreate,
    session_id: str = Query(...),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
) -> QuestionResponse:
    """Add a question to a form."""
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    _validate_admin_session(db, auth0_id, session_id)

    # Check form exists
    form = db.query(Form).filter(Form.form_key == form_key).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # Check question_key uniqueness within form
    existing = (
        db.query(Question)
        .filter(
            Question.form_key == form_key,
            Question.question_key == question_data.question_key
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Question with this key already exists in this form"
        )

    # Validate question_type
    try:
        question_type = QuestionType[question_data.question_type.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid question_type. Must be one of: {', '.join([t.name for t in QuestionType])}"
        )

    # Create question
    new_question = Question(
        form_key=form_key,
        question_key=question_data.question_key,
        question_type=question_type,
        label=question_data.label,
        placeholder=question_data.placeholder,
        description=question_data.description,
        required=question_data.required,
        page_number=question_data.page_number,
        page_title=question_data.page_title,
        order_in_page=question_data.order_in_page,
        config=question_data.config,
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return QuestionResponse(
        id=str(new_question.id),
        form_key=new_question.form_key,
        question_key=new_question.question_key,
        question_type=new_question.question_type.value,
        label=new_question.label,
        placeholder=new_question.placeholder,
        description=new_question.description,
        required=new_question.required,
        page_number=new_question.page_number,
        page_title=new_question.page_title,
        order_in_page=new_question.order_in_page,
        config=new_question.config,
    )


@router.put("/forms/{form_key}/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    form_key: str,
    question_id: str,
    question_data: QuestionUpdate,
    session_id: str = Query(...),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
) -> QuestionResponse:
    """Update a question."""
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    _validate_admin_session(db, auth0_id, session_id)

    # Parse UUID
    try:
        question_uuid = UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question ID format")

    # Find question
    question = db.query(Question).filter(Question.id == question_uuid).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Verify it belongs to the specified form
    if question.form_key != form_key:
        raise HTTPException(
            status_code=400,
            detail="Question does not belong to the specified form"
        )

    # Update fields
    if question_data.label is not None:
        question.label = question_data.label
    if question_data.placeholder is not None:
        question.placeholder = question_data.placeholder
    if question_data.description is not None:
        question.description = question_data.description
    if question_data.required is not None:
        question.required = question_data.required
    if question_data.page_number is not None:
        question.page_number = question_data.page_number
    if question_data.page_title is not None:
        question.page_title = question_data.page_title
    if question_data.order_in_page is not None:
        question.order_in_page = question_data.order_in_page
    if question_data.config is not None:
        question.config = question_data.config

    db.commit()
    db.refresh(question)

    return QuestionResponse(
        id=str(question.id),
        form_key=question.form_key,
        question_key=question.question_key,
        question_type=question.question_type.value,
        label=question.label,
        placeholder=question.placeholder,
        description=question.description,
        required=question.required,
        page_number=question.page_number,
        page_title=question.page_title,
        order_in_page=question.order_in_page,
        config=question.config,
    )


@router.delete("/forms/{form_key}/questions/{question_id}")
async def delete_question(
    form_key: str,
    question_id: str,
    session_id: str = Query(...),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Delete a question."""
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    _validate_admin_session(db, auth0_id, session_id)

    # Parse UUID
    try:
        question_uuid = UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question ID format")

    # Find question
    question = db.query(Question).filter(Question.id == question_uuid).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Verify it belongs to the specified form
    if question.form_key != form_key:
        raise HTTPException(
            status_code=400,
            detail="Question does not belong to the specified form"
        )

    # Delete question
    db.delete(question)
    db.commit()

    return {"status": "deleted", "question_id": question_id}


@router.patch("/forms/{form_key}/questions/reorder")
async def reorder_questions(
    form_key: str,
    reorder_data: ReorderQuestionsRequest,
    session_id: str = Query(...),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Reorder questions within a form."""
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    _validate_admin_session(db, auth0_id, session_id)

    # Check form exists
    form = db.query(Form).filter(Form.form_key == form_key).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # Update each question's order
    updated_count = 0
    for order_item in reorder_data.question_orders:
        question_id = order_item.get("question_id")
        page_number = order_item.get("page_number")
        order_in_page = order_item.get("order_in_page")

        if not question_id or page_number is None or order_in_page is None:
            raise HTTPException(
                status_code=400,
                detail="Each order item must have question_id, page_number, and order_in_page"
            )

        try:
            question_uuid = UUID(question_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid question ID: {question_id}")

        question = db.query(Question).filter(Question.id == question_uuid).first()
        if not question:
            raise HTTPException(status_code=404, detail=f"Question not found: {question_id}")

        if question.form_key != form_key:
            raise HTTPException(
                status_code=400,
                detail=f"Question {question_id} does not belong to form {form_key}"
            )

        question.page_number = page_number
        question.order_in_page = order_in_page
        updated_count += 1

    db.commit()

    return {"status": "reordered", "count": updated_count}
