from sqlalchemy import text
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base


class User(Base):
    __tablename__ = "user"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
