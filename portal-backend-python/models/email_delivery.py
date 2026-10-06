from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import Base


class EmailDelivery(Base):
    """Idempotency and delivery audit record for an event email campaign."""

    __tablename__ = "email_delivery"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    event_id = Column(
        UUID(as_uuid=True), ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    registration_id = Column(
        UUID(as_uuid=True),
        nullable=False,
    )
    campaign_key = Column(String(100), nullable=False)
    recipient_email = Column(String(320), nullable=False)
    template_version = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="queued")
    provider_message_id = Column(String(255), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    sent_at = Column(DateTime(timezone=True), nullable=True)

    event = relationship("Event", viewonly=True)
    registration = relationship("EventRegistration", back_populates="email_deliveries")

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'sent', 'failed')", name="ck_email_delivery_status"
        ),
        ForeignKeyConstraint(
            ["registration_id", "event_id"],
            ["event_registration.id", "event_registration.event_id"],
            ondelete="CASCADE",
            name="fk_email_delivery_registration_event",
        ),
        UniqueConstraint(
            "event_id",
            "registration_id",
            "campaign_key",
            name="uq_email_delivery_campaign_registration",
        ),
        Index("ix_email_delivery_event_campaign", "event_id", "campaign_key"),
        Index("ix_email_delivery_status", "status"),
    )
