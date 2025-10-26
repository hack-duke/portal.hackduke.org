from sqlalchemy import Column, Integer, String
from models.base import Base, TimestampMixin


class Form(TimestampMixin, Base):
    __tablename__ = "form"

    form_key = Column(String, primary_key=True)
    year = Column(Integer, nullable=False)
