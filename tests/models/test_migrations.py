from typing import cast

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy.engine import Connection

from pet_orders.core.db.db import Base, engine


def _diff(connection: Connection) -> list[object]:
    context = MigrationContext.configure(connection, opts={'compare_type': True})
    return cast('list[object]', compare_metadata(context, Base.metadata))


async def test_migrations_match_models(migrated_database: None) -> None:
    async with engine.connect() as connection:
        diff = await connection.run_sync(_diff)

    assert diff == []
