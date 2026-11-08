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


class EventAccountSetup(Base):
    """Single-use, hashed credential-setup capability for one registration."""

    __tablename__ = "event_account_setup"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    event_id = Column(
        UUID(as_uuid=True), ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    registration_id = Column(UUID(as_uuid=True), nullable=False)
    auth0_user_id = Column(String(255), nullable=False)
    token_digest = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    registration = relationship("EventRegistration", back_populates="account_setup")

    __table_args__ = (
        ForeignKeyConstraint(
            ["registration_id", "event_id"],
            ["event_registration.id", "event_registration.event_id"],
            name="fk_event_account_setup_registration_event",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "event_id",
            "registration_id",
            name="uq_event_account_setup_registration",
        ),
        Index("ix_event_account_setup_expires_at", "expires_at"),
    )
