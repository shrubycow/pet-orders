from uuid import uuid4

import jwt
import pytest
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.auth.dependencies import (
    ACCESS_TOKEN_EXPIRED,
    INVALID_ACCESS_TOKEN,
    INVALID_REFRESH_TOKEN,
    REFRESH_TOKEN_EXPIRED,
    USER_IS_ACTIVE,
)
from pet_orders.auth.service import INVALID_CODE, INVALID_CREDENTIALS
from pet_orders.core.auth.auth import ALGORITHM, authorize_user
from pet_orders.core.auth.consts import TokenType
from pet_orders.core.auth.password import hash_auth_code, verify_auth_code
from pet_orders.core.auth.settings import auth_settings
from pet_orders.core.redis.client import redis
from pet_orders.main import app
from pet_orders.users.models import User, UserStatus
from pet_orders.users.service import get_user_created_key
from tests.api.helpers import expired_token
from tests.factories import USER_EMAIL, USER_PASSWORD

CODE = '123456'


def _sub(token: str) -> str:
    payload = jwt.decode(token, auth_settings.secret_key, algorithms=[ALGORITHM])
    subject = payload['sub']
    assert isinstance(subject, str)
    return subject


async def _refresh(client: AsyncClient, refresh_token: str) -> Response:
    return await client.post(
        app.url_path_for('refresh_token'), json={'refresh_token': refresh_token}
    )


async def _verify_email(
    client: AsyncClient, headers: dict[str, str], code: str
) -> Response:
    return await client.post(
        app.url_path_for('verify_email_code'), json={'code': code}, headers=headers
    )


async def _resend_code(client: AsyncClient, headers: dict[str, str]) -> Response:
    return await client.post(
        app.url_path_for('resend_auth_code_email'), headers=headers
    )


async def test_login(client: AsyncClient, active_user: User) -> None:
    response = await client.post(
        app.url_path_for('login'),
        json={'email': USER_EMAIL, 'password': USER_PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == UserStatus.ACTIVE
    assert _sub(body['access_token']) == str(active_user.id)
    assert _sub(body['refresh_token']) == str(active_user.id)


@pytest.mark.parametrize(
    ('email', 'password'),
    [(USER_EMAIL, 'wrong-password'), ('unknown@example.com', USER_PASSWORD)],
)
async def test_login_invalid_credentials(
    client: AsyncClient, active_user: User, email: str, password: str
) -> None:
    response = await client.post(
        app.url_path_for('login'), json={'email': email, 'password': password}
    )

    assert response.status_code == 401
    assert response.json()['detail'] == INVALID_CREDENTIALS


async def test_refresh_rotates_token_pair(
    client: AsyncClient, active_user: User
) -> None:
    _, refresh_token = await authorize_user(active_user.id)

    response = await _refresh(client, refresh_token)

    assert response.status_code == 200
    body = response.json()
    assert body['refresh_token'] != refresh_token
    assert _sub(body['access_token']) == str(active_user.id)


async def test_refresh_token_reuse_revokes_family(
    client: AsyncClient, active_user: User
) -> None:
    _, old_refresh_token = await authorize_user(active_user.id)
    new_refresh_token = (await _refresh(client, old_refresh_token)).json()[
        'refresh_token'
    ]

    reused = await _refresh(client, old_refresh_token)
    after_reuse = await _refresh(client, new_refresh_token)

    assert reused.status_code == 401
    assert reused.json()['detail'] == INVALID_REFRESH_TOKEN
    assert after_reuse.status_code == 401
    assert after_reuse.json()['detail'] == INVALID_REFRESH_TOKEN


async def test_refresh_with_access_token(
    client: AsyncClient, active_user: User
) -> None:
    access_token, _ = await authorize_user(active_user.id)

    response = await _refresh(client, access_token)

    assert response.status_code == 401
    assert response.json()['detail'] == INVALID_REFRESH_TOKEN


async def test_refresh_expired_token(client: AsyncClient) -> None:
    token = expired_token(TokenType.REFRESH, family=str(uuid4()))

    response = await _refresh(client, token)

    assert response.status_code == 401
    assert response.json()['detail'] == REFRESH_TOKEN_EXPIRED


async def test_verify_email(
    client: AsyncClient,
    db_session: AsyncSession,
    inactive_user: User,
    inactive_user_headers: dict[str, str],
) -> None:
    key = get_user_created_key(inactive_user.id)
    await redis.set(key, hash_auth_code(CODE))

    response = await _verify_email(client, inactive_user_headers, CODE)

    assert response.status_code == 204
    await db_session.refresh(inactive_user)
    assert inactive_user.status is UserStatus.ACTIVE
    assert await redis.exists(key) == 0


@pytest.mark.parametrize('stored_code', [CODE, None])
async def test_verify_email_invalid_code(
    client: AsyncClient,
    db_session: AsyncSession,
    inactive_user: User,
    inactive_user_headers: dict[str, str],
    stored_code: str | None,
) -> None:
    if stored_code is not None:
        await redis.set(
            get_user_created_key(inactive_user.id), hash_auth_code(stored_code)
        )

    response = await _verify_email(client, inactive_user_headers, '000000')

    assert response.status_code == 400
    assert response.json()['detail'] == INVALID_CODE
    await db_session.refresh(inactive_user)
    assert inactive_user.status is UserStatus.INACTIVE


async def test_verify_email_active_user(
    client: AsyncClient, active_user_headers: dict[str, str]
) -> None:
    response = await _verify_email(client, active_user_headers, CODE)

    assert response.status_code == 403
    assert response.json()['detail'] == USER_IS_ACTIVE


async def test_verify_email_rate_limit(
    client: AsyncClient, inactive_user_headers: dict[str, str]
) -> None:
    first = await _verify_email(client, inactive_user_headers, '000000')
    second = await _verify_email(client, inactive_user_headers, '000000')

    assert first.status_code == 400
    assert second.status_code == 429


async def test_verify_email_without_token(client: AsyncClient) -> None:
    response = await _verify_email(client, {}, CODE)

    assert response.status_code == 401


@pytest.mark.parametrize(
    ('token', 'detail'),
    [
        (expired_token(TokenType.ACCESS), ACCESS_TOKEN_EXPIRED),
        ('not-a-jwt', INVALID_ACCESS_TOKEN),
    ],
)
async def test_verify_email_bad_access_token(
    client: AsyncClient, token: str, detail: str
) -> None:
    response = await _verify_email(client, {'Authorization': f'Bearer {token}'}, CODE)

    assert response.status_code == 401
    assert response.json()['detail'] == detail


async def test_verify_email_unknown_user(client: AsyncClient) -> None:
    access_token, _ = await authorize_user(uuid4())

    response = await _verify_email(
        client, {'Authorization': f'Bearer {access_token}'}, CODE
    )

    assert response.status_code == 401
    assert response.json()['detail'] == INVALID_ACCESS_TOKEN


@pytest.fixture
def sent_emails(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    sent: list[tuple[str, str]] = []

    async def send_email(email: str, subject: str, body: str) -> None:
        sent.append((email, body))

    monkeypatch.setattr('pet_orders.users.service.send_email', send_email)
    return sent


async def test_resend_auth_code(
    client: AsyncClient,
    inactive_user: User,
    inactive_user_headers: dict[str, str],
    sent_emails: list[tuple[str, str]],
) -> None:
    response = await _resend_code(client, inactive_user_headers)

    assert response.status_code == 204
    [(email, body)] = sent_emails
    code = body.rsplit(' ', 1)[-1]
    hashed_code = await redis.get(get_user_created_key(inactive_user.id))
    assert isinstance(hashed_code, str)
    assert email == inactive_user.email
    assert verify_auth_code(code, hashed_code)


async def test_resend_auth_code_active_user(
    client: AsyncClient,
    active_user_headers: dict[str, str],
    sent_emails: list[tuple[str, str]],
) -> None:
    response = await _resend_code(client, active_user_headers)

    assert response.status_code == 403
    assert response.json()['detail'] == USER_IS_ACTIVE
    assert sent_emails == []


async def test_resend_auth_code_rate_limit(
    client: AsyncClient,
    inactive_user_headers: dict[str, str],
    sent_emails: list[tuple[str, str]],
) -> None:
    first = await _resend_code(client, inactive_user_headers)
    second = await _resend_code(client, inactive_user_headers)

    assert first.status_code == 204
    assert second.status_code == 429
    assert len(sent_emails) == 1
