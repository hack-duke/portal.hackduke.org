from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import Base


class EventNotificationDelivery(Base):
    """Idempotency and outcome record for one scheduled browser notification."""

    __tablename__ = "event_notification_delivery"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    event_id = Column(
        UUID(as_uuid=True), ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    subscription_id = Column(UUID(as_uuid=True), nullable=False)
    notification_key = Column(String(100), nullable=False)
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        String(20), nullable=False, default="queued", server_default="queued"
    )
    attempts = Column(Integer, nullable=False, default=1, server_default="1")
    provider_status = Column(Integer, nullable=True)
    error = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    sent_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    subscription = relationship("EventPushSubscription", back_populates="deliveries")

    __table_args__ = (
        ForeignKeyConstraint(
            ["subscription_id", "event_id"],
            ["event_push_subscription.id", "event_push_subscription.event_id"],
            name="fk_event_notification_delivery_subscription_event",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "status IN ('queued', 'sent', 'failed', 'skipped')",
            name="ck_event_notification_delivery_status",
        ),
        UniqueConstraint(
            "subscription_id",
            "notification_key",
            name="uq_event_notification_delivery_subscription_key",
        ),
        Index("ix_event_notification_delivery_event_status", "event_id", "status"),
    )
