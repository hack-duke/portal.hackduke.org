from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from models.base import Base


class EventRegistration(Base):
    """An imported attendee record which can later be claimed by an Auth0 user."""

    __tablename__ = "event_registration"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    event_id = Column(
        UUID(as_uuid=True), ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    email = Column(String(320), nullable=False)
    normalized_email = Column(String(320), nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    preferred_name = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    university = Column(String(500), nullable=True)
    degree_program = Column(String(500), nullable=True)
    country = Column(String(255), nullable=True)
    attendance_commitment = Column(Boolean, nullable=True)
    photo_release_consent = Column(Boolean, nullable=True)
    mlh_code_of_conduct_consent = Column(Boolean, nullable=True)
    mlh_privacy_policy_consent = Column(Boolean, nullable=True)
    data_sharing_consent = Column(Boolean, nullable=True)
    mlh_marketing_opt_in = Column(Boolean, nullable=True)
    admission_status = Column(String(20), nullable=False, default="accepted")
    rsvp_status = Column(String(20), nullable=False, default="pending")
    source = Column(String(100), nullable=False, default="google_forms_csv")
    source_record_id = Column(String(255), nullable=True)
    source_data = Column(JSONB, nullable=False, default=dict)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    event = relationship("Event", backref="registrations")
    user = relationship("User", backref="event_registrations")
    event_pass = relationship(
        "EventPass",
        back_populates="registration",
        uselist=False,
        cascade="all, delete-orphan",
    )
    check_ins = relationship(
        "EventCheckIn",
        back_populates="registration",
        cascade="all, delete-orphan",
        order_by="EventCheckIn.checked_in_at.desc()",
    )
    email_deliveries = relationship(
        "EmailDelivery",
        back_populates="registration",
        cascade="all, delete-orphan",
        order_by="EmailDelivery.created_at.desc()",
    )
    account_setup = relationship(
        "EventAccountSetup",
        back_populates="registration",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "event_id", "normalized_email", name="uq_event_registration_email"
        ),
        UniqueConstraint("event_id", "user_id", name="uq_event_registration_user"),
        UniqueConstraint("id", "event_id", name="uq_event_registration_id_event"),
        CheckConstraint(
            "admission_status IN ('accepted', 'waitlisted', 'rejected', 'revoked')",
            name="ck_event_registration_admission_status",
        ),
        CheckConstraint(
            "rsvp_status IN ('pending', 'confirmed', 'declined')",
            name="ck_event_registration_rsvp_status",
        ),
        CheckConstraint("age IS NULL OR age >= 0", name="ck_event_registration_age"),
        Index("ix_event_registration_event_id", "event_id"),
        Index("ix_event_registration_user_id", "user_id"),
        Index("ix_event_registration_normalized_email", "normalized_email"),
    )
