from sqlalchemy import text
from sqlalchemy import Column, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base
from sqlalchemy import String


class Response(Base):
    __tablename__ = "response"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("question.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id = Column(  # not quite robust for arbitrary forms
        UUID(as_uuid=True),
        ForeignKey("application.id", ondelete="CASCADE"),
        nullable=False,
    )
    text_answer = Column(Text, nullable=True)
    bool_answer = Column(Boolean, nullable=True)
    file_s3_key = Column(String, nullable=True)
