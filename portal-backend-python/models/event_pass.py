import secrets

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import Base


def generate_event_pass_public_id() -> str:
    """Generate a non-sequential credential suitable for encoding in a QR code."""

    return f"evt_{secrets.token_urlsafe(32)}"


class EventPass(Base):
    __tablename__ = "event_pass"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    registration_id = Column(
        UUID(as_uuid=True),
        ForeignKey("event_registration.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    public_id = Column(
        String(100), nullable=False, unique=True, default=generate_event_pass_public_id
    )
    state = Column(String(20), nullable=False, default="active")
    version = Column(Integer, nullable=False, default=1)
    issued_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    registration = relationship("EventRegistration", back_populates="event_pass")

    __table_args__ = (
        CheckConstraint("state IN ('active', 'revoked')", name="ck_event_pass_state"),
        CheckConstraint("version >= 1", name="ck_event_pass_version"),
    )
