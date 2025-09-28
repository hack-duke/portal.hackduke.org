from sqlalchemy import text
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base


class User(Base):
    __tablename__ = "user"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    auth0_id = Column(
        String, unique=True, nullable=False
    )  # not using this as primary key right now in case we have multiple auth providers
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
