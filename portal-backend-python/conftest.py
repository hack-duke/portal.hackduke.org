import os
import subprocess

import pytest_asyncio
from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
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


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def test_sessionmaker(postgresql_proc):
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
        dsn = URL.create(
            "postgresql+asyncpg",
            username=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port,
            database=pg_db,
        )
        # Tests may use separate event loops; do not reuse connections across them.
        engine = create_async_engine(dsn, poolclass=NullPool)

        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
                )  # needed for UUID generation
                await conn.run_sync(Base.metadata.create_all)

            yield async_sessionmaker(
                bind=engine, autoflush=False, expire_on_commit=False
            )
        finally:
            await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_sessionmaker):
    """
    Provide an isolated database session for each test.
    Bind the session to an outer transaction so application commits only
    release savepoints. Roll back all test data when the fixture exits.
    """
    async with test_sessionmaker.kw["bind"].connect() as conn:
        transaction = await conn.begin()
        try:
            async with test_sessionmaker(
                bind=conn, join_transaction_mode="create_savepoint"
            ) as session:
                yield session
        finally:
            await transaction.rollback()
