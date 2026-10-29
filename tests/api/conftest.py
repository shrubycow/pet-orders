import os
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from pet_orders.core.db.db import Base, engine
from pet_orders.core.db.dependencies import get_db_session
from pet_orders.core.redis.client import redis
from pet_orders.main import app
from tests.fakes import FakeChannel

ROOT = Path(__file__).resolve().parents[2]


def _upgrade(connection) -> None:
    config = Config(str(ROOT / 'alembic.ini'))
    script = ScriptDirectory.from_config(config)

    def upgrade(revision, context):
        return script._upgrade_revs('head', revision)

    env_context = EnvironmentContext(
        config,
        script,
        fn=upgrade,
        destination_rev='head',
    )
    with env_context:
        env_context.configure(connection=connection, target_metadata=Base.metadata)
        with env_context.begin_transaction():
            env_context.run_migrations()


@pytest.fixture(scope='session')
async def migrated_database() -> None:
    await _create_database()
    async with engine.connect() as connection:
        await connection.run_sync(_upgrade)


async def _create_database() -> None:
    database = make_url(os.environ['DATABASE_URL']).database
    if not database:
        raise RuntimeError('DATABASE_URL has no database name')
    admin_engine = create_async_engine(
        os.environ['ADMIN_DATABASE_URL'],
        isolation_level='AUTOCOMMIT',
        poolclass=NullPool,
    )
    async with admin_engine.connect() as connection:
        exists = await connection.execute(
            text('SELECT 1 FROM pg_database WHERE datname = :name'),
            {'name': database},
        )
        if exists.scalar() is None:
            await connection.execute(text(f'CREATE DATABASE "{database}"'))
    await admin_engine.dispose()


@pytest.fixture(scope='session')
async def client(migrated_database: None):
    channel = FakeChannel()
    async with app.router.lifespan_context(app):
        app.state.broker = channel
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url='http://test'
        ) as http_client:
            yield http_client
    await engine.dispose()
    await redis.aclose()


@pytest.fixture
def broker(client: AsyncClient) -> FakeChannel:
    return app.state.broker


@pytest.fixture
async def db_sessions(client: AsyncClient):
    async with engine.connect() as connection:
        transaction = await connection.begin()
        sessions = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode='create_savepoint',
        )

        async def get_test_session():
            async with sessions() as session:
                yield session

        app.dependency_overrides[get_db_session] = get_test_session
        try:
            await redis.flushdb()
            app.state.broker.published.clear()
            yield sessions
        finally:
            app.dependency_overrides.pop(get_db_session, None)
            await transaction.rollback()


@pytest.fixture(autouse=True)
async def clean_state(db_sessions: async_sessionmaker[AsyncSession]) -> None:
    yield


@pytest.fixture
async def db_session(db_sessions: async_sessionmaker[AsyncSession]):
    async with db_sessions() as session:
        yield session
