from sqlalchemy import Column, ForeignKey, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
from models.base import Base


class CheckInLog(Base):
    """Check-in log model for tracking event check-ins"""
    __tablename__ = "check_in_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    check_in_time = Column(DateTime, nullable=False, server_default=func.now())

    def to_dict(self):
        """Convert to dictionary format"""
        return {
            "user_id": str(self.user_id),
            "name": self.name,
            "event_type": self.event_type,
            "time": self.check_in_time.strftime('%H:%M')
        }
