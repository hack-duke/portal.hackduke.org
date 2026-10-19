from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
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


class EventTeamMember(Base):
    """A source team-member row, optionally linked to one registration."""

    __tablename__ = "event_team_member"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    event_id = Column(UUID(as_uuid=True), nullable=False)
    team_id = Column(UUID(as_uuid=True), nullable=False)
    registration_id = Column(UUID(as_uuid=True), nullable=True)
    member_position = Column(Integer, nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(320), nullable=True)
    normalized_email = Column(String(320), nullable=True)
    discord_username = Column(String(255), nullable=True)
    match_status = Column(String(20), nullable=False, default="unmatched")
    match_method = Column(String(50), nullable=True)
    match_detail = Column(String(100), nullable=False)
    source_row_number = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    team = relationship(
        "EventTeam",
        back_populates="members",
        overlaps="registration,team_membership",
    )
    registration = relationship(
        "EventRegistration",
        back_populates="team_membership",
        overlaps="members,team",
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["team_id", "event_id"],
            ["event_team.id", "event_team.event_id"],
            name="fk_event_team_member_team_event",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["registration_id", "event_id"],
            ["event_registration.id", "event_registration.event_id"],
            name="fk_event_team_member_registration_event",
        ),
        UniqueConstraint(
            "team_id", "member_position", name="uq_event_team_member_position"
        ),
        UniqueConstraint(
            "event_id", "registration_id", name="uq_event_team_member_registration"
        ),
        CheckConstraint(
            "member_position BETWEEN 1 AND 4",
            name="ck_event_team_member_position",
        ),
        CheckConstraint(
            "match_status IN ('matched', 'unmatched', 'ambiguous')",
            name="ck_event_team_member_match_status",
        ),
        CheckConstraint(
            "match_method IS NULL OR match_method IN "
            "('email', 'name', 'exact_unique_name_email_mismatch')",
            name="ck_event_team_member_match_method",
        ),
        Index("ix_event_team_member_team", "team_id"),
        Index("ix_event_team_member_registration", "registration_id"),
        Index("ix_event_team_member_event_status", "event_id", "match_status"),
    )
