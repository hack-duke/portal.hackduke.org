from sqlalchemy import Column, Integer, String, DateTime, func
from models.base import Base


class Form(Base):
    __tablename__ = "form"

    form_key = Column(String, primary_key=True)
    year = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
