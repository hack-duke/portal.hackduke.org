from sqlalchemy import text
from sqlalchemy import Column, String, Text, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    question_type = Column(Enum(QuestionType), nullable=False)
    label = Column(Text, nullable=True)
    placeholder = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    required = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    page_number = Column(Integer, nullable=False, default=1, server_default=text("1"))
    page_title = Column(String, nullable=True)
    order_in_page = Column(Integer, nullable=False, default=0, server_default=text("0"))
    config = Column(JSONB, nullable=True)
