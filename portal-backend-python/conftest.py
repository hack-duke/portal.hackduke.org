import os
import subprocess

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.base import Base
from pytest_postgresql.janitor import DatabaseJanitor


if os.name == "nt":
    # pytest-postgresql's nested POSIX quoting is passed literally by pg_ctl
    # on Windows and PostgreSQL 18 rejects values such as "'stderr'". Keep the
    # upstream command everywhere else and use Windows-safe parameter values
    # for local integration tests.
    from pytest_postgresql.executor import PostgreSQLExecutor

    PostgreSQLExecutor.BASE_PROC_START_COMMAND = (
        '{executable} start -D "{datadir}" '
        '-o "-F -p {port} -c log_destination=stderr '
        "-c logging_collector=off "
        '-c unix_socket_directories={unixsocketdir} {postgres_options}" '
        '-l "{logfile}" {startparams}'
    )

    def _windows_postgresql_stop(self, _sig=None, _expected_sig=None):
        if self.process is None:
            return self
        subprocess.run(
            [self.executable, "stop", "-D", self.datadir, "-m", "f"],
            check=True,
            capture_output=True,
        )
        self._clear_process()
        return self

    PostgreSQLExecutor.stop = _windows_postgresql_stop


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
    # Start a savepoint to ensure we can rollback even with explicit flushes
    session.begin_nested()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
