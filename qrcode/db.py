import os
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from datetime import datetime

load_dotenv()

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
db_port = os.getenv("DB_PORT", "5432")

DB_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# SQLAlchemy Models
class User(Base):
    """User model - matches the MongoDB 'cfg2025' collection structure"""
    __tablename__ = "check_in"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    pref_name = Column(String, nullable=True)

    def get_full_name(self) -> str:
        """Get the user's full name, preferring pref_name over first_name"""
        first = self.pref_name if self.pref_name else self.first_name
        return f"{first} {self.last_name}"


class CheckInLog(Base):
    """Check-in log model - replaces the JSON file storage"""
    __tablename__ = "check_in_logs"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    check_in_time = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convert to dictionary format matching the original JSON structure"""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "event_type": self.event_type,
            "time": self.check_in_time.strftime('%H:%M')
        }


# Database helper functions
def get_db() -> Session:
    """
    Dependency function to get database session.
    Use this in Flask routes or FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def application_to_checkin(db: Session, user_id: str):



def get_local_session() -> Session:
    """
    Get a database session directly.
    Use this when you need a session outside of dependency injection.
    Remember to close the session when done!
    """
    return SessionLocal()


def init_db():
    """Initialize the database by creating all tables"""
    Base.metadata.create_all(bind=engine)


def resolve_name(db: Session, user_id: str) -> str | None:
    """
    Resolve a user's name from their user_id.

    Args:
        db: Database session
        user_id: The user's ID

    Returns:
        Full name or None if user not found
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        return user.get_full_name() if user else None
    except Exception as e:
        print(f"Error resolving name: {e}")
        return None


def get_all_check_ins(db: Session) -> list[dict]:
    """
    Get all check-in logs ordered by most recent first.

    Args:
        db: Database session

    Returns:
        List of check-in dictionaries
    """
    logs = db.query(CheckInLog).order_by(CheckInLog.check_in_time.desc()).all()
    return [log.to_dict() for log in logs]


def get_check_in(db: Session, user_id: str, event_type: str) -> CheckInLog | None:
    """
    Get a specific check-in entry.

    Args:
        db: Database session
        user_id: The user's ID
        event_type: The event type

    Returns:
        CheckInLog object or None
    """
    return db.query(CheckInLog).filter(
        CheckInLog.user_id == user_id,
        CheckInLog.event_type == event_type
    ).first()


def create_check_in(db: Session, user_id: str, name: str, event_type: str) -> CheckInLog:
    """
    Create a new check-in entry.

    Args:
        db: Database session
        user_id: The user's ID
        name: The user's full name
        event_type: The event type

    Returns:
        The created CheckInLog object
    """
    check_in = CheckInLog(
        user_id=user_id,
        name=name,
        event_type=event_type,
        check_in_time=datetime.now()
    )
    db.add(check_in)
    db.commit()
    db.refresh(check_in)
    return check_in


def delete_check_in(db: Session, user_id: str, event_type: str) -> bool:
    """
    Delete a check-in entry.

    Args:
        db: Database session
        user_id: The user's ID
        event_type: The event type

    Returns:
        True if deleted, False if not found
    """
    check_in = get_check_in(db, user_id, event_type)
    if check_in:
        db.delete(check_in)
        db.commit()
        return True
    return False


def search_check_ins(db: Session, query: str) -> list[dict]:
    """
    Search check-in logs by name or user_id.

    Args:
        db: Database session
        query: Search query string

    Returns:
        List of matching check-in dictionaries
    """
    query_lower = query.lower()
    logs = db.query(CheckInLog).filter(
        (CheckInLog.name.ilike(f"%{query}%")) |
        (CheckInLog.user_id.ilike(f"%{query}%"))
    ).order_by(CheckInLog.check_in_time.desc()).all()
    return [log.to_dict() for log in logs]
