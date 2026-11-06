import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from pet_orders.core.auth.auth import authorize_user
from pet_orders.core.auth.password import hash_password
from pet_orders.core.db.db import engine
from pet_orders.core.db.dependencies import get_db_session
from pet_orders.core.redis.client import redis
from pet_orders.main import app
from pet_orders.organizations.models import Organization
from pet_orders.users.models import User, UserStatus
from tests.api.helpers import bearer
from tests.db import migrate_database
from tests.factories import (
    USER_EMAIL,
    USER_PASSWORD,
    add_user_to_organization,
    make_organization,
)
from tests.fakes import FakeChannel


@pytest.fixture(scope='session')
async def migrated_database() -> None:
    await migrate_database()


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


async def _create_user(db_session: AsyncSession, status: UserStatus) -> User:
    user = User(
        email=USER_EMAIL,
        password=await hash_password(USER_PASSWORD),
        status=status,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    return await _create_user(db_session, UserStatus.INACTIVE)


@pytest.fixture
async def active_user(db_session: AsyncSession) -> User:
    return await _create_user(db_session, UserStatus.ACTIVE)


@pytest.fixture
async def inactive_user_headers(inactive_user: User) -> dict[str, str]:
    access_token, _ = await authorize_user(inactive_user.id)
    return bearer(access_token)


@pytest.fixture
async def active_user_headers(active_user: User) -> dict[str, str]:
    access_token, _ = await authorize_user(active_user.id)
    return bearer(access_token)


@pytest.fixture
async def member_organization(
    db_session: AsyncSession, active_user: User
) -> Organization:
    organization = make_organization()
    add_user_to_organization(active_user, organization)
    await db_session.commit()
    return organization
