import jwt
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.core.auth.auth import ALGORITHM
from pet_orders.core.auth.settings import auth_settings
from pet_orders.main import app
from pet_orders.users.models import User, UserStatus
from pet_orders.users.producers import USER_CREATED_QUEUE
from pet_orders.users.schemas import UserCreatedEvent, UserCreateRequest
from tests.fakes import FakeChannel


async def test_register_user(
    client: AsyncClient, db_session: AsyncSession, broker: FakeChannel
):
    email = 'test@example.com'
    response = await client.post(
        app.url_path_for('create_user'),
        json=UserCreateRequest(email=email, password='password').model_dump(),
    )
    assert response.status_code == 201

    access_token = jwt.decode(
        response.json()['access_token'],
        auth_settings.secret_key,
        algorithms=[ALGORITHM],
    )
    refresh_token = jwt.decode(
        response.json()['refresh_token'],
        auth_settings.secret_key,
        algorithms=[ALGORITHM],
    )

    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None
    assert user.status == UserStatus.INACTIVE

    assert access_token['sub'] == str(user.id)
    assert refresh_token['sub'] == str(user.id)

    queue, body = broker.published[0]
    event = UserCreatedEvent.model_validate_json(body)
    assert queue == USER_CREATED_QUEUE
    assert event.email == email
    assert event.user_id == user.id


async def test_register_user_invalid_email(
    client: AsyncClient,
):
    email = 'test'
    response = await client.post(
        app.url_path_for('create_user'),
        json={'email': email, 'password': 'password'},
    )
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', 'email']
