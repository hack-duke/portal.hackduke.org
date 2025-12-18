from sqlalchemy import text, Column, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base
from sqlalchemy import func


class AdminUser(Base):
    __tablename__ = "admin_user"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    current_session_id = Column(
        String, nullable=True
    )  # For multi-tab invalidation
