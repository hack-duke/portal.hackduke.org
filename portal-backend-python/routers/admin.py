from fastapi import APIRouter, Depends, HTTPException, Security, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID
from urllib.parse import quote, unquote
import uuid as uuid_lib

from auth import VerifyToken
from db import get_db
from models.user import User
from models.admin_user import AdminUser
from models.application import Application, ApplicationStatus
from models.response import Response
from pydantic import BaseModel
from services.google_sheets import export_applicants_to_sheets

router = APIRouter()
auth = VerifyToken()

# Constants
LOCK_TIMEOUT_HOURS = 1
LOCK_TIMEOUT_SECONDS = LOCK_TIMEOUT_HOURS * 3600
CURRENT_FORM_KEY = "2026-cfg-application"
RESUME_QUESTION_ID = "0f9782ba-7b18-418d-90ad-ec13a9b467c5"
RESUME_S3_BASE_URL = "https://hackathon-resume-bucket.s3.us-east-2.amazonaws.com/"


class AdminCheckResponse(BaseModel):
    is_admin: bool
    session_id: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    form_key: str
    status: str
    submission_json: Optional[Dict[str, Any]]
    created_at: str
    resume_url: Optional[str] = None

    class Config:
        from_attributes = True


class AdminStatsResponse(BaseModel):
    total_pending: int
    total_accepted: int
    total_rejected: int
    user_accepted: int
    user_rejected: int


class DecisionRequest(BaseModel):
    decision: str  # "accept", "reject", or "pending"


class ExportResponse(BaseModel):
    accepted_tab: str
    rejected_tab: str
    accepted_count: int
    rejected_count: int


class ApplicationListItem(BaseModel):
    id: str
    status: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    pref_name: Optional[str] = None
    email: Optional[str] = None
    university: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[str] = None
    country: Optional[str] = None
    created_at: str
    decided_by: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    applications: list[ApplicationListItem]
    total: int


class SingleApplicationResponse(BaseModel):
    id: str
    user_id: str
    form_key: str
    status: str
    submission_json: Optional[Dict[str, Any]]
    created_at: str
    resume_url: Optional[str] = None
    is_locked_by_other: bool = False
    locked_by_email: Optional[str] = None

    class Config:
        from_attributes = True


def _is_lock_expired(locked_at: Optional[datetime]) -> bool:
    """Check if a lock has timed out."""
    if not locked_at:
        return True
    # Make locked_at timezone-aware if it isn't
    if locked_at.tzinfo is None:
        locked_at = locked_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - locked_at > timedelta(seconds=LOCK_TIMEOUT_SECONDS)


def _release_expired_locks(db: Session) -> None:
    """Release all locks that have timed out, including skipped apps."""
    # Find apps with locked_at set (either locked or skipped)
    apps_with_lock_time = db.query(Application).filter(
        Application.locked_at.isnot(None)
    ).all()

    changed = False
    for app in apps_with_lock_time:
        if _is_lock_expired(app.locked_at):
            app.locked_by = None
            app.locked_at = None
            changed = True

    if changed:
        db.commit()


def _invalidate_other_sessions(
    db: Session, admin_user_id: UUID, new_session_id: str
) -> None:
    """Invalidate all other sessions for this admin user."""
    admin = db.query(AdminUser).filter(AdminUser.user_id == admin_user_id).first()
    if admin:
        admin.current_session_id = new_session_id
        db.commit()


def _validate_session(
    db: Session, admin_user_id: UUID, session_id: str
) -> bool:
    """Validate that the session is still active."""
    admin = db.query(AdminUser).filter(AdminUser.user_id == admin_user_id).first()
    if not admin or admin.current_session_id != session_id:
        return False
    return True


@router.post("/auth/check", response_model=AdminCheckResponse)
async def check_admin_status(
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    """
    Check if the authenticated user is an admin.
    If they are, create or update their session.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    # Get or create user
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        user = User(auth0_id=auth0_id)
        db.add(user)
        db.flush()

    # Check if user is in admin allowlist
    admin_user = (
        db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    )

    if not admin_user:
        db.commit()
        return AdminCheckResponse(is_admin=False)

    # Release any locks held by this user (e.g., from a previous abruptly closed session)
    locked_apps = db.query(Application).filter(Application.locked_by == user.id).all()
    if locked_apps:
        for app in locked_apps:
            app.locked_by = None
            app.locked_at = None
        db.commit()

    # Create new session ID and invalidate other sessions
    new_session_id = str(uuid_lib.uuid4())
    _invalidate_other_sessions(db, user.id, new_session_id)

    return AdminCheckResponse(is_admin=True, session_id=new_session_id)


@router.get("/next-application", response_model=ApplicationResponse)
async def get_next_application(
    session_id: str,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    """
    Get the next PENDING application for judging.
    Locks it to the current admin user.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    # Get user and verify admin status
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    admin_user = (
        db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    )
    if not admin_user:
        raise HTTPException(status_code=403, detail="User is not an admin")

    # Validate session
    if not _validate_session(db, user.id, session_id):
        raise HTTPException(status_code=403, detail="Session invalidated")

    # Release expired locks
    _release_expired_locks(db)

    # Get next PENDING application (not locked, or locked by this user)
    # Only from the current form
    # Order by locked_at NULLS FIRST so skipped apps go to back of queue
    next_app = (
        db.query(Application)
        .filter(Application.form_key == CURRENT_FORM_KEY)
        .filter(Application.status == ApplicationStatus.PENDING)
        .filter(
            or_(
                Application.locked_by.is_(None),
                Application.locked_by == user.id,
            )
        )
        .order_by(Application.locked_at.asc().nullsfirst())
        .first()
    )

    if not next_app:
        raise HTTPException(status_code=404, detail="No pending applications")

    # Lock the application to this user
    next_app.locked_by = user.id
    next_app.locked_at = datetime.now(timezone.utc)
    db.commit()

    # Fetch resume URL if available
    resume_url = None
    resume_response = (
        db.query(Response)
        .filter(Response.application_id == next_app.id)
        .filter(Response.question_id == UUID(RESUME_QUESTION_ID))
        .first()
    )
    if resume_response and resume_response.file_s3_key:
        # normalized_key = unquote(resume_response.file_s3_key)
        encoded_key = quote(resume_response.file_s3_key, safe='/')
        resume_url = RESUME_S3_BASE_URL + encoded_key

    return ApplicationResponse(
        id=str(next_app.id),
        user_id=str(next_app.user_id),
        form_key=next_app.form_key,
        status=next_app.status.value,
        submission_json=next_app.submission_json,
        created_at=next_app.created_at.isoformat(),
        resume_url=resume_url,
    )


@router.post("/application/{app_id}/decision", response_model=ApplicationResponse)
async def submit_decision(
    app_id: str,
    decision_request: DecisionRequest,
    session_id: str,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    """
    Submit a decision (accept/reject/pending) on an application.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    # Get user and verify admin status
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    admin_user = (
        db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    )
    if not admin_user:
        raise HTTPException(status_code=403, detail="User is not an admin")

    # Validate session
    if not _validate_session(db, user.id, session_id):
        raise HTTPException(status_code=403, detail="Session invalidated")

    # Get application
    try:
        app_uuid = UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")

    app = db.query(Application).filter(Application.id == app_uuid).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Verify this admin has the lock
    if app.locked_by != user.id:
        raise HTTPException(status_code=403, detail="You do not have the lock on this application")

    # Process decision
    decision = decision_request.decision.lower()
    if decision == "accept":
        app.status = ApplicationStatus.ACCEPTED
        app.decided_by = user.id
        app.decided_at = datetime.now(timezone.utc)
    elif decision == "reject":
        app.status = ApplicationStatus.REJECTED
        app.decided_by = user.id
        app.decided_at = datetime.now(timezone.utc)
    elif decision == "pending":
        # Mark as pending, clear decided_by and decided_at
        app.status = ApplicationStatus.PENDING
        app.decided_by = None
        app.decided_at = None
        # Keep locked_at updated so this app goes to back of queue
        app.locked_by = None
        app.locked_at = datetime.now(timezone.utc)
        db.commit()
        return ApplicationResponse(
            id=str(app.id),
            user_id=str(app.user_id),
            form_key=app.form_key,
            status=app.status.value,
            submission_json=app.submission_json,
            created_at=app.created_at.isoformat(),
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid decision")

    # Unlock the application (for accept/reject)
    app.locked_by = None
    app.locked_at = None
    db.commit()

    return ApplicationResponse(
        id=str(app.id),
        user_id=str(app.user_id),
        form_key=app.form_key,
        status=app.status.value,
        submission_json=app.submission_json,
        created_at=app.created_at.isoformat(),
    )


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    session_id: str,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    """
    Get judging statistics.
    Global stats and per-admin stats.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    # Get user and verify admin status
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    admin_user = (
        db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    )
    if not admin_user:
        raise HTTPException(status_code=403, detail="User is not an admin")

    # Validate session
    if not _validate_session(db, user.id, session_id):
        raise HTTPException(status_code=403, detail="Session invalidated")

    # Get global stats (only for current form)
    total_pending = (
        db.query(Application)
        .filter(Application.form_key == CURRENT_FORM_KEY)
        .filter(Application.status == ApplicationStatus.PENDING)
        .count()
    )
    total_accepted = (
        db.query(Application)
        .filter(Application.form_key == CURRENT_FORM_KEY)
        .filter(Application.status == ApplicationStatus.ACCEPTED)
        .count()
    )
    total_rejected = (
        db.query(Application)
        .filter(Application.form_key == CURRENT_FORM_KEY)
        .filter(Application.status == ApplicationStatus.REJECTED)
        .count()
    )

    # Get per-user stats (only for current form)
    user_accepted = (
        db.query(Application)
        .filter(Application.form_key == CURRENT_FORM_KEY)
        .filter(
            Application.status == ApplicationStatus.ACCEPTED,
            Application.decided_by == user.id,
        )
        .count()
    )
    user_rejected = (
        db.query(Application)
        .filter(Application.form_key == CURRENT_FORM_KEY)
        .filter(
            Application.status == ApplicationStatus.REJECTED,
            Application.decided_by == user.id,
        )
        .count()
    )

    return AdminStatsResponse(
        total_pending=total_pending,
        total_accepted=total_accepted,
        total_rejected=total_rejected,
        user_accepted=user_accepted,
        user_rejected=user_rejected,
    )


@router.get("/applications", response_model=ApplicationListResponse)
async def list_applications(
    session_id: str,
    status: Optional[str] = None,
    search: Optional[str] = None,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    """
    List all applications with optional filtering and search.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    # Get user and verify admin status
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    admin_user = (
        db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    )
    if not admin_user:
        raise HTTPException(status_code=403, detail="User is not an admin")

    # Validate session
    if not _validate_session(db, user.id, session_id):
        raise HTTPException(status_code=403, detail="Session invalidated")

    # Build query
    query = db.query(Application).filter(Application.form_key == CURRENT_FORM_KEY)

    # Filter by status
    if status:
        status_upper = status.upper()
        if status_upper == "PENDING":
            query = query.filter(Application.status == ApplicationStatus.PENDING)
        elif status_upper == "ACCEPTED":
            query = query.filter(Application.status == ApplicationStatus.ACCEPTED)
        elif status_upper == "REJECTED":
            query = query.filter(Application.status == ApplicationStatus.REJECTED)

    # Get all applications
    applications = query.order_by(Application.created_at.desc()).all()

    # Build response with search filtering (done in Python for JSON field search)
    result = []
    for app in applications:
        submission = app.submission_json or {}
        first_name = submission.get("first_name", "")
        last_name = submission.get("last_name", "")
        pref_name = submission.get("pref_name", "")
        email = submission.get("email", "")
        university = submission.get("university", "")
        major = submission.get("major", "")
        graduation_year = str(submission.get("graduation_year", ""))
        country = submission.get("country", "")

        # Search filter
        if search:
            search_lower = search.lower()
            searchable = f"{first_name} {last_name} {pref_name} {email} {university} {major} {country}".lower()
            if search_lower not in searchable:
                continue

        result.append(ApplicationListItem(
            id=str(app.id),
            status=app.status.value,
            first_name=first_name,
            last_name=last_name,
            pref_name=pref_name,
            email=email,
            university=university,
            major=major,
            graduation_year=graduation_year,
            country=country,
            created_at=app.created_at.isoformat(),
            decided_by=str(app.decided_by) if app.decided_by else None,
        ))

    return ApplicationListResponse(
        applications=result,
        total=len(result),
    )


@router.get("/application/{app_id}", response_model=SingleApplicationResponse)
async def get_application(
    app_id: str,
    session_id: str,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    """
    Get a specific application by ID.
    Attempts to acquire lock if available, otherwise returns read-only view.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    # Get user and verify admin status
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    admin_user = (
        db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    )
    if not admin_user:
        raise HTTPException(status_code=403, detail="User is not an admin")

    # Validate session
    if not _validate_session(db, user.id, session_id):
        raise HTTPException(status_code=403, detail="Session invalidated")

    # Get application
    try:
        app_uuid = UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")

    app = db.query(Application).filter(Application.id == app_uuid).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Release expired locks first
    _release_expired_locks(db)

    # Check lock status
    is_locked_by_other = False
    locked_by_email = None

    if app.locked_by and app.locked_by != user.id:
        # Someone else has the lock and it's not expired
        is_locked_by_other = True
        locked_by_email = "another admin"
    else:
        # Lock is available or already ours - acquire it
        app.locked_by = user.id
        app.locked_at = datetime.now(timezone.utc)
        db.commit()

    # Fetch resume URL if available
    resume_url = None
    resume_response = (
        db.query(Response)
        .filter(Response.application_id == app.id)
        .filter(Response.question_id == UUID(RESUME_QUESTION_ID))
        .first()
    )
    if resume_response and resume_response.file_s3_key:
        encoded_key = quote(resume_response.file_s3_key, safe='/')
        resume_url = RESUME_S3_BASE_URL + encoded_key

    return SingleApplicationResponse(
        id=str(app.id),
        user_id=str(app.user_id),
        form_key=app.form_key,
        status=app.status.value,
        submission_json=app.submission_json,
        created_at=app.created_at.isoformat(),
        resume_url=resume_url,
        is_locked_by_other=is_locked_by_other,
        locked_by_email=locked_by_email,
    )


@router.post("/application/{app_id}/release-lock")
async def release_application_lock(
    app_id: str,
    session_id: str,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    """
    Release the lock on a specific application.
    Used when returning to the applicants table.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    # Get user and verify admin status
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    admin_user = (
        db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    )
    if not admin_user:
        raise HTTPException(status_code=403, detail="User is not an admin")

    # Validate session
    if not _validate_session(db, user.id, session_id):
        raise HTTPException(status_code=403, detail="Session invalidated")

    # Get application
    try:
        app_uuid = UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")

    app = db.query(Application).filter(Application.id == app_uuid).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Only release if we own the lock
    if app.locked_by == user.id:
        app.locked_by = None
        app.locked_at = None
        db.commit()

    return {"status": "released"}


@router.get("/ping")
async def ping(
    session_id: str,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    """
    Ping endpoint to validate session is still active.
    Useful for detecting timeout on multi-tab scenarios.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    # Get user
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Validate session
    if not _validate_session(db, user.id, session_id):
        raise HTTPException(status_code=403, detail="Session invalidated")

    return {"status": "ok"}


@router.post("/release-locks-beacon")
async def release_locks_beacon(
    session_id: str = Form(None),
    db: Session = Depends(get_db),
):
    """
    Release all locks for a session when the browser tab/window is closed.
    Used with navigator.sendBeacon() which cannot send auth headers.
    Authenticates via session_id only.
    """
    if not session_id:
        return {"status": "no session"}

    # Find the admin user with this active session
    admin_user = (
        db.query(AdminUser)
        .filter(AdminUser.current_session_id == session_id)
        .first()
    )

    if not admin_user:
        # Session is invalid or already replaced by another tab
        return {"status": "invalid session"}

    # Release all locks held by this user
    locked_apps = (
        db.query(Application)
        .filter(Application.locked_by == admin_user.user_id)
        .all()
    )

    for app in locked_apps:
        app.locked_by = None
        app.locked_at = None

    if locked_apps:
        db.commit()

    return {"status": "released", "count": len(locked_apps)}


@router.post("/logout")
async def logout(
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    """
    Logout - clear all locks held by this user and clear their session.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    # Get user
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Clear session
    admin_user = (
        db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    )
    if admin_user:
        admin_user.current_session_id = None
        db.commit()

    # Clear all locks held by this user
    locked_apps = db.query(Application).filter(Application.locked_by == user.id).all()
    for app in locked_apps:
        app.locked_by = None
        app.locked_at = None
    db.commit()

    return {"status": "logged out"}


@router.post("/export-to-sheets", response_model=ExportResponse)
async def export_to_sheets(
    session_id: str,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    """
    Export accepted and rejected applicants to Google Sheets.
    Creates two new tabs with today's date.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    # Get user and verify admin status
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    admin_user = (
        db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    )
    if not admin_user:
        raise HTTPException(status_code=403, detail="User is not an admin")

    # Validate session
    if not _validate_session(db, user.id, session_id):
        raise HTTPException(status_code=403, detail="Session invalidated")

    # Get accepted applications ordered by decided_at
    accepted_apps = (
        db.query(Application)
        .filter(Application.form_key == CURRENT_FORM_KEY)
        .filter(Application.status == ApplicationStatus.ACCEPTED)
        .order_by(Application.decided_at.asc().nullslast())
        .all()
    )

    # Get rejected applications ordered by decided_at
    rejected_apps = (
        db.query(Application)
        .filter(Application.form_key == CURRENT_FORM_KEY)
        .filter(Application.status == ApplicationStatus.REJECTED)
        .order_by(Application.decided_at.asc().nullslast())
        .all()
    )

    # Build applicant data for export
    accepted_applicants = []
    for app in accepted_apps:
        submission = app.submission_json or {}
        accepted_applicants.append({
            "user_id": str(app.user_id),
            "email": submission.get("email", ""),
        })

    rejected_applicants = []
    for app in rejected_apps:
        submission = app.submission_json or {}
        rejected_applicants.append({
            "user_id": str(app.user_id),
            "email": submission.get("email", ""),
        })

    # Export to Google Sheets
    try:
        result = export_applicants_to_sheets(accepted_applicants, rejected_applicants)
        return ExportResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export to Google Sheets: {str(e)}")
