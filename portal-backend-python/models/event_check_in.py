from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import Base


class EventCheckIn(Base):
    __tablename__ = "event_check_in"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    event_id = Column(UUID(as_uuid=True), nullable=False)
    registration_id = Column(UUID(as_uuid=True), nullable=False)
    checkpoint = Column(String(100), nullable=False, default="arrival")
    checked_in_by = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    checked_in_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    registration = relationship("EventRegistration", back_populates="check_ins")
    scanner = relationship("User")

    __table_args__ = (
        ForeignKeyConstraint(
            ["registration_id", "event_id"],
            ["event_registration.id", "event_registration.event_id"],
            ondelete="CASCADE",
            name="fk_event_check_in_registration_event",
        ),
        UniqueConstraint(
            "event_id",
            "registration_id",
            "checkpoint",
            name="uq_event_check_in_checkpoint",
        ),
        Index("ix_event_check_in_event_checkpoint", "event_id", "checkpoint"),
        Index("ix_event_check_in_registration_id", "registration_id"),
    )
