from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from db import get_db
from models.check_in import CheckInLog
from models.application import Application, ApplicationStatus
from datetime import datetime

router = APIRouter()


# Pydantic schemas
class CheckInRequest(BaseModel):
    qr_code: str  # user_id as string
    event_type: str


class CheckInResponse(BaseModel):
    message: str
    user_id: str
    first_name: str
    last_name: str
    full_name: str
    event_type: str
    check_in_time: str
    status: str


class UserInfo(BaseModel):
    user_id: str
    name: str
    first_name: Optional[str]
    last_name: Optional[str]


class CheckedInUser(UserInfo):
    check_in_time: str
    check_in_timestamp: str
    status: str


class NotCheckedInUser(UserInfo):
    status: str


class AttendeesResponse(BaseModel):
    checked_in: List[CheckedInUser]
    not_checked_in: List[NotCheckedInUser]
    total_checked_in: int
    total_not_checked_in: int
    total_attendees: int


class SearchUsersResponse(BaseModel):
    users: List[UserInfo]


class CheckInLogEntry(BaseModel):
    user_id: str
    name: str
    event_type: str
    time: str


class AllCheckInsResponse(BaseModel):
    log: List[CheckInLogEntry]
    total_users: int


class DeleteCheckInRequest(BaseModel):
    user_id: str
    event_type: str


class NotCheckedInResponse(BaseModel):
    users: List[UserInfo]
    total: int


# Helper functions
def get_name_from_application(application: Application) -> str:
    """Extract full name from application's submission_json."""
    if not application or not application.submission_json:
        return "Unknown"

    submission = application.submission_json
    first_name = submission.get("first_name", "")
    last_name = submission.get("last_name", "")
    return f"{first_name} {last_name}".strip() or "Unknown"


def resolve_name(db: Session, user_id: str) -> Optional[str]:
    """Resolve a user's name from their application's submission_json."""
    try:
        # Look up application by user_id and get name from submission_json
        application = db.query(Application).filter(
            Application.user_id == user_id,
            Application.status.in_([ApplicationStatus.CONFIRMED, ApplicationStatus.ACCEPTED])
        ).first()

        if application:
            return get_name_from_application(application)
        return None
    except Exception as e:
        print(f"Error resolving name: {e}")
        return None


# Endpoints
@router.post("/log_user", response_model=CheckInResponse)
async def log_user(
    request: CheckInRequest,
    db: Session = Depends(get_db),
):
    """Check in a user for an event."""
    user_id = request.qr_code.strip()
    event_type = request.event_type

    # Validate user_id is not empty
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid QR code: empty user ID")

    # Validate user_id is a valid UUID format
    import re
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if not uuid_pattern.match(user_id):
        raise HTTPException(status_code=400, detail=f"Invalid QR code format: {user_id}")

    # Look up application by user_id
    application = db.query(Application).filter(
        Application.user_id == user_id,
        Application.status.in_([ApplicationStatus.ACCEPTED, ApplicationStatus.CONFIRMED])
    ).first()

    if not application:
        raise HTTPException(status_code=400, detail="User not found in DB")

    # Extract name from submission_json
    submission = application.submission_json or {}
    first_name = submission.get("first_name", "")
    last_name = submission.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip() or "Unknown"

    # Check if user has already checked in for this event type
    existing_check_in = db.query(CheckInLog).filter(
        CheckInLog.user_id == user_id,
        CheckInLog.event_type == event_type
    ).first()

    if existing_check_in:
        check_in_time = existing_check_in.check_in_time.strftime('%H:%M')
        raise HTTPException(
            status_code=400,
            detail=f"{full_name} already checked in at {check_in_time}"
        )

    # Create new check-in
    check_in = CheckInLog(
        user_id=user_id,
        name=full_name,
        event_type=event_type,
        check_in_time=datetime.now()
    )
    db.add(check_in)
    db.commit()
    db.refresh(check_in)

    return CheckInResponse(
        message="Check-in successful",
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        event_type=event_type,
        check_in_time=check_in.check_in_time.strftime('%H:%M'),
        status=application.status.value
    )


@router.get("/search_users", response_model=SearchUsersResponse)
async def search_users(
    q: str = "",
    db: Session = Depends(get_db),
):
    """Search for users by name for manual check-in."""
    query = q.strip().lower()
    if not query or len(query) < 2:
        return SearchUsersResponse(users=[])

    # Get all applications with ACCEPTED or CONFIRMED status
    applications = db.query(Application).filter(
        Application.status.in_([ApplicationStatus.ACCEPTED, ApplicationStatus.CONFIRMED])
    ).all()

    # Filter by name in submission_json
    matching_users = []
    for application in applications:
        submission = application.submission_json or {}
        first_name = submission.get("first_name", "")
        last_name = submission.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()

        # Check if query matches first_name, last_name, or full_name
        if (query in first_name.lower() or
            query in last_name.lower() or
            query in full_name.lower()):
            matching_users.append(UserInfo(
                user_id=str(application.user_id),
                name=full_name or "Unknown",
                first_name=first_name,
                last_name=last_name
            ))

        if len(matching_users) >= 10:
            break

    return SearchUsersResponse(users=matching_users)


@router.get("/log", response_model=AllCheckInsResponse)
async def get_all_check_ins(
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all check-in logs ordered by most recent first."""
    query = db.query(CheckInLog)
    if event_type:
        query = query.filter(CheckInLog.event_type == event_type)

    logs = query.order_by(CheckInLog.check_in_time.desc()).all()

    return AllCheckInsResponse(
        log=[
            CheckInLogEntry(
                user_id=str(log.user_id),
                name=log.name,
                event_type=log.event_type,
                time=log.check_in_time.strftime('%H:%M')
            )
            for log in logs
        ],
        total_users=len(logs)
    )


@router.post("/delete_log_entry")
async def delete_log_entry(
    request: DeleteCheckInRequest,
    db: Session = Depends(get_db),
):
    """Delete a check-in entry."""
    check_in = db.query(CheckInLog).filter(
        CheckInLog.user_id == request.user_id,
        CheckInLog.event_type == request.event_type
    ).first()

    if not check_in:
        raise HTTPException(status_code=404, detail="Log entry not found")

    db.delete(check_in)
    db.commit()

    return {"message": "Log entry deleted successfully"}


@router.get("/not_checked_in", response_model=NotCheckedInResponse)
async def get_not_checked_in(
    event_type: str = "check-in",
    db: Session = Depends(get_db),
):
    """Get all accepted users who have NOT checked in for a specific event type."""
    # Get all accepted/confirmed applications
    applications = db.query(Application).filter(
        Application.status.in_([ApplicationStatus.ACCEPTED, ApplicationStatus.CONFIRMED])
    ).all()

    # Get all user_ids that have checked in for this event type
    checked_in_user_ids = set(
        str(log.user_id) for log in db.query(CheckInLog).filter(
            CheckInLog.event_type == event_type
        ).all()
    )

    # Filter to users who haven't checked in
    not_checked_in = []
    for application in applications:
        user_id = str(application.user_id)
        if user_id not in checked_in_user_ids:
            submission = application.submission_json or {}
            first_name = submission.get("first_name", "")
            last_name = submission.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip() or "Unknown"
            not_checked_in.append(UserInfo(
                user_id=user_id,
                name=full_name,
                first_name=first_name,
                last_name=last_name
            ))

    # Sort alphabetically by name
    not_checked_in.sort(key=lambda u: u.name.lower())

    return NotCheckedInResponse(
        users=not_checked_in,
        total=len(not_checked_in)
    )
