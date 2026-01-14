from sqlalchemy import text
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base
from sqlalchemy import Enum
import enum


class QuestionType(enum.Enum):
    TEXT = "text"
    BOOLEAN = "boolean"
    FILE = "file"
    INTEGER = "integer"
    FLOAT = "float"


class Question(Base):
    __tablename__ = "question"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    form_key = Column(
        String, ForeignKey("form.form_key", ondelete="CASCADE"), nullable=False
    )
    question_key = Column(String, nullable=False)  # must be unique within the form
    # question_text = Column(Text, nullable=False) # not used for now, add back if we want to pull questions from db and render frontend with them
    question_type = Column(Enum(QuestionType), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
