from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from models.base import Base

class CheckIn(Base):
    __tablename__ = "check_in"

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    check_in_time = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)