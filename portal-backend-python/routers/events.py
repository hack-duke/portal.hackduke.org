import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from auth import VerifyToken
from db import get_db
from models.event import Event
from models.event_check_in import EventCheckIn
from models.event_pass import EventPass
from models.event_registration import EventRegistration
from models.user import User
from models.user_role import RoleEnum
from routers.roles import require_admin, require_check_in
from services.auth0_management import get_auth0_management_client


router = APIRouter()
auth = VerifyToken()

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
CHECKPOINT_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,99}$")


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    timezone: str
    support_email: Optional[str]
    public_site_url: Optional[str]
    brand_key: Optional[str]
    state: str
    pass_eligibility: str


class PassResponse(BaseModel):
    public_id: str
    state: str
    version: int
    issued_at: datetime


class CheckInResponse(BaseModel):
    id: UUID
    checkpoint: str
    checked_in_at: datetime
    checked_in_by: Optional[UUID]


class EmailDeliveryResponse(BaseModel):
    id: UUID
    campaign_key: str
    recipient_email: str
    template_version: str
    status: str
    provider_message_id: Optional[str]
    error: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]


class MyRegistrationResponse(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    preferred_name: Optional[str]
    admission_status: str
    rsvp_status: str
    claimed_at: Optional[datetime]
    event_pass: Optional[PassResponse]
    check_ins: List[CheckInResponse]


class MyEventResponse(BaseModel):
    event: EventResponse
    claimed: bool
    claim_required: bool
    registration: Optional[MyRegistrationResponse]


class AdminRegistrationResponse(BaseModel):
    id: UUID
    event_id: UUID
    user_id: Optional[UUID]
    email: str
    normalized_email: str
    first_name: Optional[str]
    last_name: Optional[str]
    preferred_name: Optional[str]
    phone: Optional[str]
    age: Optional[int]
    university: Optional[str]
    degree_program: Optional[str]
    country: Optional[str]
    attendance_commitment: Optional[bool]
    photo_release_consent: Optional[bool]
    mlh_code_of_conduct_consent: Optional[bool]
    mlh_privacy_policy_consent: Optional[bool]
    data_sharing_consent: Optional[bool]
    mlh_marketing_opt_in: Optional[bool]
    admission_status: str
    rsvp_status: str
    source: str
    source_record_id: Optional[str]
    source_data: Dict[str, Any]
    claimed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    pass_state: Optional[str]
    pass_public_id: Optional[str]
    pass_issued_at: Optional[datetime]
    check_ins: List[CheckInResponse]
    email_deliveries: List[EmailDeliveryResponse]


class AdminRegistrationListResponse(BaseModel):
    registrations: List[AdminRegistrationResponse]
    total: int
    limit: int
    offset: int


class EventCheckInRequest(BaseModel):
    pass_id: str = Field(min_length=10, max_length=100)
    checkpoint: str = Field(default="arrival", min_length=1, max_length=100)


class EventCheckInResponse(BaseModel):
    id: UUID
    registration_id: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    preferred_name: Optional[str]
    checkpoint: str
    checked_in_at: datetime
    checked_in_by: Optional[UUID]


class EventCheckInListResponse(BaseModel):
    check_ins: List[EventCheckInResponse]
    total: int


def normalize_email(email: str) -> str:
    """Normalize only casing and surrounding whitespace; do not rewrite providers."""

    return email.strip().casefold()


def _get_claim(payload: Dict[str, Any], claim_name: str) -> Any:
    """Read either a standard claim or a URI-namespaced Auth0 custom claim."""

    if claim_name in payload:
        return payload[claim_name]

    for key, value in payload.items():
        key_tail = key.rstrip("/").rsplit("/", 1)[-1].rsplit("#", 1)[-1]
        if key_tail == claim_name:
            return value
        if isinstance(value, dict) and claim_name in value:
            return value[claim_name]
    return None


def get_verified_email(auth_payload: Dict[str, Any]) -> str:
    email = _get_claim(auth_payload, "email")
    email_verified = _get_claim(auth_payload, "email_verified")

    if isinstance(email, str) and EMAIL_PATTERN.match(email.strip()):
        if email_verified is not True:
            raise HTTPException(
                status_code=403,
                detail="A verified email address is required to claim a registration",
            )
        return normalize_email(email)

    # Auth0 access tokens do not include email by default. Look it up by the
    # validated token subject rather than accepting an email from the client.
    try:
        auth0_user = get_auth0_management_client().get_user_by_id(
            get_subject(auth_payload)
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to verify the account email at this time",
        )
    management_email = auth0_user.get("email") if auth0_user else None
    management_email_verified = (
        auth0_user.get("email_verified") if auth0_user else None
    )
    if not isinstance(management_email, str) or not EMAIL_PATTERN.match(
        management_email.strip()
    ):
        raise HTTPException(
            status_code=403,
            detail="A valid email claim is required to claim a registration",
        )
    if management_email_verified is not True:
        raise HTTPException(
            status_code=403,
            detail="A verified email address is required to claim a registration",
        )
    return normalize_email(management_email)


def get_subject(auth_payload: Dict[str, Any]) -> str:
    auth0_id = auth_payload.get("sub")
    if not isinstance(auth0_id, str) or not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")
    return auth0_id


def get_event_or_404(db: Session, slug: str) -> Event:
    event = db.query(Event).filter(Event.slug == slug).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


def get_role_user(auth_payload: Dict[str, Any], db: Session) -> User:
    user = db.query(User).filter(User.auth0_id == get_subject(auth_payload)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def registration_is_pass_eligible(event: Event, registration: EventRegistration) -> bool:
    if registration.admission_status != "accepted":
        return False
    if event.pass_eligibility == "confirmed":
        return registration.rsvp_status == "confirmed"
    return registration.rsvp_status != "declined"


def _pass_response(event_pass: Optional[EventPass]) -> Optional[PassResponse]:
    if event_pass is None:
        return None
    return PassResponse(
        public_id=event_pass.public_id,
        state=event_pass.state,
        version=event_pass.version,
        issued_at=event_pass.issued_at,
    )


def _check_in_response(check_in: EventCheckIn) -> CheckInResponse:
    return CheckInResponse(
        id=check_in.id,
        checkpoint=check_in.checkpoint,
        checked_in_at=check_in.checked_in_at,
        checked_in_by=check_in.checked_in_by,
    )


def _my_registration_response(registration: EventRegistration) -> MyRegistrationResponse:
    return MyRegistrationResponse(
        id=registration.id,
        email=registration.email,
        first_name=registration.first_name,
        last_name=registration.last_name,
        preferred_name=registration.preferred_name,
        admission_status=registration.admission_status,
        rsvp_status=registration.rsvp_status,
        claimed_at=registration.claimed_at,
        event_pass=_pass_response(registration.event_pass),
        check_ins=[_check_in_response(item) for item in registration.check_ins],
    )


def _admin_registration_response(
    registration: EventRegistration,
) -> AdminRegistrationResponse:
    event_pass = registration.event_pass
    return AdminRegistrationResponse(
        id=registration.id,
        event_id=registration.event_id,
        user_id=registration.user_id,
        email=registration.email,
        normalized_email=registration.normalized_email,
        first_name=registration.first_name,
        last_name=registration.last_name,
        preferred_name=registration.preferred_name,
        phone=registration.phone,
        age=registration.age,
        university=registration.university,
        degree_program=registration.degree_program,
        country=registration.country,
        attendance_commitment=registration.attendance_commitment,
        photo_release_consent=registration.photo_release_consent,
        mlh_code_of_conduct_consent=registration.mlh_code_of_conduct_consent,
        mlh_privacy_policy_consent=registration.mlh_privacy_policy_consent,
        data_sharing_consent=registration.data_sharing_consent,
        mlh_marketing_opt_in=registration.mlh_marketing_opt_in,
        admission_status=registration.admission_status,
        rsvp_status=registration.rsvp_status,
        source=registration.source,
        source_record_id=registration.source_record_id,
        source_data=registration.source_data or {},
        claimed_at=registration.claimed_at,
        created_at=registration.created_at,
        updated_at=registration.updated_at,
        pass_state=event_pass.state if event_pass else None,
        pass_public_id=event_pass.public_id if event_pass else None,
        pass_issued_at=event_pass.issued_at if event_pass else None,
        check_ins=[_check_in_response(item) for item in registration.check_ins],
        email_deliveries=[
            EmailDeliveryResponse(
                id=item.id,
                campaign_key=item.campaign_key,
                recipient_email=item.recipient_email,
                template_version=item.template_version,
                status=item.status,
                provider_message_id=item.provider_message_id,
                error=item.error,
                created_at=item.created_at,
                sent_at=item.sent_at,
            )
            for item in registration.email_deliveries
        ],
    )


@router.get("", response_model=List[EventResponse])
async def list_events(db: Session = Depends(get_db)):
    """List event metadata safe for the participant landing page."""

    return (
        db.query(Event)
        .filter(Event.state == "active")
        .order_by(Event.start_at.asc().nullslast(), Event.name.asc())
        .all()
    )


@router.get("/{slug}/me", response_model=MyEventResponse)
async def get_my_event_registration(
    slug: str,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    event = get_event_or_404(db, slug)
    auth0_id = get_subject(auth_payload)
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    registration = None
    if user is not None:
        registration = (
            db.query(EventRegistration)
            .options(
                joinedload(EventRegistration.event_pass),
                joinedload(EventRegistration.check_ins),
            )
            .filter(
                EventRegistration.event_id == event.id,
                EventRegistration.user_id == user.id,
            )
            .first()
        )

    return MyEventResponse(
        event=EventResponse.model_validate(event),
        claimed=registration is not None,
        claim_required=registration is None,
        registration=(
            _my_registration_response(registration) if registration is not None else None
        ),
    )


@router.post("/{slug}/claim", response_model=MyEventResponse)
async def claim_event_registration(
    slug: str,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    event = get_event_or_404(db, slug)
    if event.state != "active":
        raise HTTPException(status_code=409, detail="Event registration claiming is not active")

    auth0_id = get_subject(auth_payload)
    normalized_email = get_verified_email(auth_payload)
    registration = (
        db.query(EventRegistration)
        .filter(
            EventRegistration.event_id == event.id,
            EventRegistration.normalized_email == normalized_email,
        )
        .with_for_update()
        .first()
    )
    if registration is None:
        raise HTTPException(
            status_code=404,
            detail="No eligible registration was found for the verified account email",
        )

    user = db.query(User).filter(User.auth0_id == auth0_id).with_for_update().first()
    if user is None:
        user = User(
            auth0_id=auth0_id,
            email=registration.email,
            first_name=registration.first_name,
            last_name=registration.last_name,
        )
        db.add(user)
        db.flush()
    elif user.email is None:
        user.email = registration.email

    if registration.user_id is not None and registration.user_id != user.id:
        raise HTTPException(status_code=409, detail="Registration has already been claimed")

    other_registration = (
        db.query(EventRegistration)
        .filter(
            EventRegistration.event_id == event.id,
            EventRegistration.user_id == user.id,
            EventRegistration.id != registration.id,
        )
        .first()
    )
    if other_registration is not None:
        raise HTTPException(
            status_code=409,
            detail="This account is already linked to another event registration",
        )

    if registration.user_id is None:
        registration.user_id = user.id
        registration.claimed_at = datetime.now(timezone.utc)

    if registration_is_pass_eligible(event, registration):
        if registration.event_pass is None:
            registration.event_pass = EventPass()
    elif registration.event_pass is not None and registration.event_pass.state == "active":
        registration.event_pass.state = "revoked"
        registration.event_pass.revoked_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Registration was claimed by another account"
        )

    registration = (
        db.query(EventRegistration)
        .options(
            joinedload(EventRegistration.event_pass),
            joinedload(EventRegistration.check_ins),
            joinedload(EventRegistration.email_deliveries),
        )
        .filter(EventRegistration.id == registration.id)
        .first()
    )
    return MyEventResponse(
        event=EventResponse.model_validate(event),
        claimed=True,
        claim_required=False,
        registration=_my_registration_response(registration),
    )


@router.get("/{slug}/registrations", response_model=AdminRegistrationListResponse)
async def list_event_registrations(
    slug: str,
    q: str = "",
    admission_status: Optional[str] = None,
    rsvp_status: Optional[str] = None,
    claimed: Optional[bool] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    event = get_event_or_404(db, slug)
    admin = get_role_user(auth_payload, db)
    require_admin(db, admin.id)

    query = db.query(EventRegistration).filter(EventRegistration.event_id == event.id)
    if q.strip():
        pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                EventRegistration.first_name.ilike(pattern),
                EventRegistration.last_name.ilike(pattern),
                EventRegistration.preferred_name.ilike(pattern),
                EventRegistration.email.ilike(pattern),
                EventRegistration.university.ilike(pattern),
            )
        )
    if admission_status is not None:
        query = query.filter(EventRegistration.admission_status == admission_status)
    if rsvp_status is not None:
        query = query.filter(EventRegistration.rsvp_status == rsvp_status)
    if claimed is True:
        query = query.filter(EventRegistration.user_id.is_not(None))
    elif claimed is False:
        query = query.filter(EventRegistration.user_id.is_(None))

    total = query.with_entities(func.count(EventRegistration.id)).scalar() or 0
    registrations = (
        query.options(
            joinedload(EventRegistration.event_pass),
            joinedload(EventRegistration.check_ins),
            joinedload(EventRegistration.email_deliveries),
        )
        .order_by(
            EventRegistration.last_name.asc().nullslast(),
            EventRegistration.first_name.asc().nullslast(),
            EventRegistration.email.asc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return AdminRegistrationListResponse(
        registrations=[_admin_registration_response(item) for item in registrations],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/{slug}/check-ins", response_model=EventCheckInResponse)
async def create_event_check_in(
    slug: str,
    request: EventCheckInRequest,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    event = get_event_or_404(db, slug)
    scanner = get_role_user(auth_payload, db)
    require_check_in(db, scanner.id)

    checkpoint = request.checkpoint.strip().lower()
    if not CHECKPOINT_PATTERN.fullmatch(checkpoint):
        raise HTTPException(status_code=422, detail="Invalid checkpoint key")

    event_pass = (
        db.query(EventPass)
        .join(EventRegistration, EventPass.registration_id == EventRegistration.id)
        .filter(
            EventPass.public_id == request.pass_id.strip(),
            EventPass.state == "active",
            EventRegistration.event_id == event.id,
        )
        .with_for_update()
        .first()
    )
    if event_pass is None:
        raise HTTPException(status_code=404, detail="Active pass not found for this event")

    registration = event_pass.registration
    if not registration_is_pass_eligible(event, registration):
        raise HTTPException(status_code=403, detail="Registration is not eligible for check-in")

    existing = (
        db.query(EventCheckIn)
        .filter(
            EventCheckIn.event_id == event.id,
            EventCheckIn.registration_id == registration.id,
            EventCheckIn.checkpoint == checkpoint,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Attendee already checked in at this checkpoint",
                "checked_in_at": existing.checked_in_at.isoformat(),
            },
        )

    check_in = EventCheckIn(
        event_id=event.id,
        registration_id=registration.id,
        checkpoint=checkpoint,
        checked_in_by=scanner.id,
    )
    db.add(check_in)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Attendee already checked in at this checkpoint"
        )
    db.refresh(check_in)

    return EventCheckInResponse(
        id=check_in.id,
        registration_id=registration.id,
        first_name=registration.first_name,
        last_name=registration.last_name,
        preferred_name=registration.preferred_name,
        checkpoint=check_in.checkpoint,
        checked_in_at=check_in.checked_in_at,
        checked_in_by=check_in.checked_in_by,
    )


@router.get("/{slug}/check-ins", response_model=EventCheckInListResponse)
async def list_event_check_ins(
    slug: str,
    checkpoint: Optional[str] = None,
    limit: int = Query(default=500, ge=1, le=1000),
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: Session = Depends(get_db),
):
    event = get_event_or_404(db, slug)
    scanner = get_role_user(auth_payload, db)
    require_check_in(db, scanner.id)

    query = (
        db.query(EventCheckIn)
        .join(
            EventRegistration,
            EventCheckIn.registration_id == EventRegistration.id,
        )
        .filter(EventCheckIn.event_id == event.id)
    )
    if checkpoint:
        query = query.filter(EventCheckIn.checkpoint == checkpoint.strip().lower())
    total = query.with_entities(func.count(EventCheckIn.id)).scalar() or 0
    check_ins = query.order_by(EventCheckIn.checked_in_at.desc()).limit(limit).all()

    return EventCheckInListResponse(
        check_ins=[
            EventCheckInResponse(
                id=item.id,
                registration_id=item.registration_id,
                first_name=item.registration.first_name,
                last_name=item.registration.last_name,
                preferred_name=item.registration.preferred_name,
                checkpoint=item.checkpoint,
                checked_in_at=item.checked_in_at,
                checked_in_by=item.checked_in_by,
            )
            for item in check_ins
        ],
        total=total,
    )
