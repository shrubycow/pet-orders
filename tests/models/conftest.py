import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.core.db.db import engine
from pet_orders.organizations.models import Organization
from tests.db import migrate_database
from tests.factories import make_organization


@pytest.fixture(scope='session')
async def migrated_database():
    await migrate_database()
    yield
    await engine.dispose()


@pytest.fixture
async def db_session(migrated_database: None):
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode='create_savepoint',
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def organization(db_session: AsyncSession) -> Organization:
    organization = make_organization()
    db_session.add(organization)
    await db_session.flush()
    return organization
