from sqlalchemy import (
    Boolean,
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


class EventPushSubscription(Base):
    """A browser push capability owned by one claimed event registration."""

    __tablename__ = "event_push_subscription"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    event_id = Column(
        UUID(as_uuid=True), ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    registration_id = Column(UUID(as_uuid=True), nullable=False)
    endpoint = Column(Text, nullable=False)
    endpoint_hash = Column(String(64), nullable=False)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    user_agent = Column(String(500), nullable=True)
    active = Column(Boolean, nullable=False, default=True, server_default="true")
    disabled_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    registration = relationship(
        "EventRegistration", back_populates="push_subscriptions"
    )
    deliveries = relationship(
        "EventNotificationDelivery",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["registration_id", "event_id"],
            ["event_registration.id", "event_registration.event_id"],
            name="fk_event_push_subscription_registration_event",
            ondelete="CASCADE",
        ),
        UniqueConstraint("id", "event_id", name="uq_event_push_subscription_id_event"),
        UniqueConstraint(
            "event_id",
            "endpoint_hash",
            name="uq_event_push_subscription_event_endpoint",
        ),
        Index("ix_event_push_subscription_event_active", "event_id", "active"),
        Index("ix_event_push_subscription_registration", "registration_id"),
    )
