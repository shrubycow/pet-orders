import os
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from pet_orders.core.db.db import Base, engine

ROOT = Path(__file__).resolve().parents[1]


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


async def migrate_database() -> None:
    await _create_database()
    async with engine.connect() as connection:
        await connection.run_sync(_upgrade)


def violated_constraint(exc: IntegrityError) -> str | None:
    driver_error = getattr(exc.orig, 'orig', None) or exc.orig
    return getattr(driver_error, 'constraint_name', None)


async def assert_flush_violates(session: AsyncSession, constraint: str) -> None:
    with pytest.raises(IntegrityError) as exc_info:
        await session.flush()
    assert violated_constraint(exc_info.value) == constraint
