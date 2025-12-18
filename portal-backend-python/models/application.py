from sqlalchemy import text
from sqlalchemy import Column, ForeignKey, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from models.base import Base
import enum
from sqlalchemy import func


class ApplicationStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CONFIRMED = "confirmed"


class Application(Base):
    __tablename__ = "application"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    form_key = Column(
        String, ForeignKey("form.form_key", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    status = Column(
        Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.PENDING
    )
    submission_json = Column(
        JSONB, nullable=True
    )  # redundant but makes fetching form data easier
    locked_by = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )  # FK to user (admin) who is currently reviewing
    locked_at = Column(
        DateTime, nullable=True
    )  # Timestamp when lock was acquired
    decided_by = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )  # FK to admin user who made the decision
