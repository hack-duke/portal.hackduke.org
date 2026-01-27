from sqlalchemy import text, Column, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import Base
from sqlalchemy import func
import enum


class RoleEnum(enum.Enum):
    ADMIN = "admin"
    CHECK_IN = "check_in"


class UserRole(Base):
    __tablename__ = "user_role"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(
        SQLEnum(RoleEnum, name="role_enum", create_type=True),
        nullable=False
    )
    granted_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    granted_by = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="roles")
    granter = relationship("User", foreign_keys=[granted_by])

    # Ensure a user can't have duplicate roles
    __table_args__ = (
        UniqueConstraint('user_id', 'role', name='uq_user_role'),
    )
