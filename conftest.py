import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.base import Base
from pytest_postgresql.janitor import DatabaseJanitor


@pytest.fixture(scope="session")
def test_sessionmaker(postgresql_proc):
    pg_host = postgresql_proc.host
    pg_port = postgresql_proc.port
    pg_user = postgresql_proc.user
    pg_password = postgresql_proc.password
    pg_db = postgresql_proc.dbname

    with DatabaseJanitor(
        user=pg_user,
        host=pg_host,
        port=pg_port,
        dbname=pg_db,
        version=postgresql_proc.version,
        password=pg_password,
    ):
        dsn = (
            f"postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
        )
        engine = create_engine(dsn)

        with engine.connect() as conn:
            conn.execute(
                text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            )  # needed for UUID generation
            conn.commit()

        Base.metadata.create_all(engine)

        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        yield SessionLocal
        engine.dispose()


@pytest.fixture
def test_session(test_sessionmaker):
    """
    Provide an isolated database session for each test.
    Creates a new session, yields it for the test, then rolls back
    any changes and closes the session to ensure test isolation.
    """
    session = test_sessionmaker()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
