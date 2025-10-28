from sqlalchemy import Column, Integer, String, Boolean
from models.base import Base
import sqlalchemy as sa


class Form(Base):
    __tablename__ = "form"
    form_key = Column(String, primary_key=True)
    year = Column(Integer, nullable=False)
    is_open = Column(Boolean, nullable=False, default=False, server_default=sa.text("false"))
