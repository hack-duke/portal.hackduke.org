import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
db_port = os.getenv("DB_PORT", "5432")

DB_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


engine = create_async_engine(
    DB_URL,
)

SessionLocal = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async session, committing on success and rolling back on error."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_local_session() -> AsyncSession:
    """
    Create an async session outside of FastAPI dependency injection.

    Use ``async with get_local_session() as session`` to ensure cleanup.
    The caller is responsible for awaiting commits and rollbacks.
    """
    return SessionLocal()
