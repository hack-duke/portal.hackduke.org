from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.dialects.postgresql import ARRAY
from models.base import Base
import sqlalchemy as sa


class Form(Base):
    __tablename__ = "form"
    form_key = Column(String, primary_key=True)
    year = Column(Integer, nullable=False)
    title = Column(String, nullable=True)
    closed_message_title = Column(String, nullable=True)
    closed_message_body = Column(Text, nullable=True)
    is_open = Column(
        Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
    is_db_driven = Column(
        Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
    exception_emails = Column(
        ARRAY(String), nullable=False, default=[], server_default="{}"
    )
