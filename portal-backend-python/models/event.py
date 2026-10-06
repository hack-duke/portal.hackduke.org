from sqlalchemy import CheckConstraint, Column, DateTime, String, func, text
from sqlalchemy.dialects.postgresql import UUID

from models.base import Base


class Event(Base):
    """A hackathon whose registrations and passes are isolated from other events."""

    __tablename__ = "event"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    slug = Column(String(100), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    start_at = Column(DateTime(timezone=True), nullable=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String(100), nullable=False, default="America/New_York")
    support_email = Column(String(320), nullable=True)
    public_site_url = Column(String(2048), nullable=True)
    brand_key = Column(String(100), nullable=True)
    state = Column(String(20), nullable=False, default="draft")
    pass_eligibility = Column(String(20), nullable=False, default="confirmed")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "state IN ('draft', 'active', 'archived')", name="ck_event_state"
        ),
        CheckConstraint(
            "pass_eligibility IN ('accepted', 'confirmed')",
            name="ck_event_pass_eligibility",
        ),
    )
