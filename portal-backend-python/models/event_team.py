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


class EventTeam(Base):
    """A team and its source preferences for one event."""

    __tablename__ = "event_team"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    event_id = Column(
        UUID(as_uuid=True), ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False)
    team_number = Column(String(50), nullable=True)

    # Preferences come from the team-formation form. Assignment fields are
    # deliberately separate so a preference is never presented as a decision.
    track_preference = Column(String(100), nullable=True)
    assigned_track = Column(String(100), nullable=True)
    challenge_preferences = Column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    assigned_challenge = Column(String(500), nullable=True)
    sponsor_name = Column(String(255), nullable=True)
    sponsor_contact_name = Column(String(255), nullable=True)
    sponsor_contact_email = Column(String(320), nullable=True)
    requested_additional_teammates = Column(Integer, nullable=True)

    source = Column(String(100), nullable=False, default="google_forms_xlsx")
    source_record_id = Column(String(64), nullable=False)
    source_submitted_at = Column(DateTime(timezone=True), nullable=False)
    active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    event = relationship("Event", backref="teams")
    members = relationship(
        "EventTeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
        order_by="EventTeamMember.member_position.asc()",
        overlaps="registration,team_membership",
    )

    __table_args__ = (
        UniqueConstraint("id", "event_id", name="uq_event_team_id_event"),
        UniqueConstraint(
            "event_id", "normalized_name", name="uq_event_team_event_name"
        ),
        CheckConstraint(
            "requested_additional_teammates IS NULL OR "
            "requested_additional_teammates BETWEEN 0 AND 4",
            name="ck_event_team_additional_teammates",
        ),
        Index("ix_event_team_event_active", "event_id", "active"),
        Index("ix_event_team_event_name", "event_id", "normalized_name"),
    )
