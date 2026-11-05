from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from pet_orders.core.db.db import Base, engine


def _diff(connection) -> list:
    context = MigrationContext.configure(connection, opts={'compare_type': True})
    return compare_metadata(context, Base.metadata)


async def test_migrations_match_models(migrated_database: None):
    async with engine.connect() as connection:
        diff = await connection.run_sync(_diff)

    assert diff == []
