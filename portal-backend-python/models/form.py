from sqlalchemy import Column, Integer, String, Boolean, Text
from models.base import Base
import sqlalchemy as sa


class Form(Base):
    __tablename__ = "form"
    form_key = Column(String, primary_key=True)
    year = Column(Integer, nullable=False)
    is_open = Column(Boolean, nullable=False, default=False, server_default=sa.text("false"))
    title = Column(String, nullable=True)
    closed_message_title = Column(String, nullable=True)
    closed_message_body = Column(Text, nullable=True)
    is_db_driven = Column(Boolean, nullable=False, default=True, server_default=sa.text("true"))
