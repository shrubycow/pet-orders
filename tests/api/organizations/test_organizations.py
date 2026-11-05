from datetime import timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.auth.dependencies import (
    ACCESS_TOKEN_EXPIRED,
    INVALID_ACCESS_TOKEN,
    USER_IS_INACTIVE,
)
from pet_orders.core.auth.auth import ALGORITHM, authorize_user
from pet_orders.core.auth.consts import TokenType
from pet_orders.core.auth.settings import auth_settings
from pet_orders.core.utils import now
from pet_orders.main import app
from pet_orders.organizations.consts import OrganizationRole, OrganizationStatus
from pet_orders.organizations.models import Organization
from pet_orders.organizations.service import (
    ORGANIZATION_NAME_TAKEN,
    USER_ALREADY_IN_ORGANIZATION,
    create_organization,
)
from pet_orders.users.models import User, UserStatus
from tests.factories import make_organization


def _bearer(access_token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {access_token}'}


def _expired_access_token() -> str:
    issued_at = now() - timedelta(hours=1)
    return jwt.encode(
        {
            'sub': str(uuid4()),
            'typ': TokenType.ACCESS,
            'exp': issued_at + timedelta(minutes=1),
            'iat': issued_at,
            'jti': str(uuid4()),
        },
        auth_settings.secret_key,
        algorithm=ALGORITHM,
    )


async def _create_organization(
    client: AsyncClient, headers: dict[str, str], name: str = 'Acme'
):
    return await client.post(
        app.url_path_for('create_organization_endpoint'),
        json={'name': name},
        headers=headers,
    )


async def test_create_organization(
    client: AsyncClient,
    db_session: AsyncSession,
    active_user: User,
    active_user_headers: dict[str, str],
):
    response = await _create_organization(client, active_user_headers, 'Acme')

    assert response.status_code == 201
    body = response.json()
    assert body['name'] == 'Acme'
    assert body['status'] == OrganizationStatus.ACTIVE

    await db_session.refresh(active_user)
    organization = await db_session.get(Organization, UUID(body['id']))
    assert organization is not None
    assert organization.name == 'Acme'
    assert organization.status is OrganizationStatus.ACTIVE
    assert active_user.organization_id == organization.id
    assert active_user.role is OrganizationRole.OWNER


async def test_create_organization_duplicate_name(
    client: AsyncClient,
    db_session: AsyncSession,
    active_user_headers: dict[str, str],
):
    created = await _create_organization(client, active_user_headers, 'Acme')
    assert created.status_code == 201

    other = User(
        email='other@example.com',
        password='hash',
        status=UserStatus.ACTIVE,
    )
    db_session.add(other)
    await db_session.commit()
    access_token, _ = await authorize_user(other.id)

    response = await _create_organization(client, _bearer(access_token), 'Acme')

    assert response.status_code == 409
    assert response.json()['detail'] == ORGANIZATION_NAME_TAKEN
    await db_session.refresh(other)
    assert other.organization_id is None
    assert other.role is None
    names = await db_session.scalars(
        select(Organization.name).where(Organization.name == 'Acme')
    )
    assert list(names) == ['Acme']


async def test_create_organization_when_user_already_belongs(
    client: AsyncClient,
    db_session: AsyncSession,
    active_user: User,
    active_user_headers: dict[str, str],
):
    active_user.organization = make_organization(name='Existing')
    active_user.role = OrganizationRole.MEMBER
    await db_session.commit()

    response = await _create_organization(client, active_user_headers, 'Acme')

    assert response.status_code == 409
    assert response.json()['detail'] == USER_ALREADY_IN_ORGANIZATION
    await db_session.refresh(active_user)
    assert active_user.role is OrganizationRole.MEMBER
    created = await db_session.scalar(
        select(Organization).where(Organization.name == 'Acme')
    )
    assert created is None


async def test_create_organization_inactive_user(
    client: AsyncClient, inactive_user_headers: dict[str, str]
):
    response = await _create_organization(client, inactive_user_headers)

    assert response.status_code == 403
    assert response.json()['detail'] == USER_IS_INACTIVE


async def test_create_organization_without_token(client: AsyncClient):
    response = await _create_organization(client, {})

    assert response.status_code == 401


@pytest.mark.parametrize(
    ('token', 'detail'),
    [
        (_expired_access_token(), ACCESS_TOKEN_EXPIRED),
        ('not-a-jwt', INVALID_ACCESS_TOKEN),
    ],
)
async def test_create_organization_bad_access_token(
    client: AsyncClient, token: str, detail: str
):
    response = await _create_organization(client, _bearer(token))

    assert response.status_code == 401
    assert response.json()['detail'] == detail


async def test_create_organization_unknown_user(client: AsyncClient):
    access_token, _ = await authorize_user(uuid4())

    response = await _create_organization(client, _bearer(access_token))

    assert response.status_code == 401
    assert response.json()['detail'] == INVALID_ACCESS_TOKEN


async def test_create_organization_strips_name(
    client: AsyncClient,
    db_session: AsyncSession,
    active_user_headers: dict[str, str],
):
    response = await _create_organization(client, active_user_headers, '  Acme  ')

    assert response.status_code == 201
    assert response.json()['name'] == 'Acme'
    organization = await db_session.get(Organization, UUID(response.json()['id']))
    assert organization is not None
    assert organization.name == 'Acme'


async def test_create_organization_strips_before_length_check(
    client: AsyncClient, active_user_headers: dict[str, str]
):
    response = await _create_organization(
        client, active_user_headers, f'  {"a" * 255}  '
    )

    assert response.status_code == 201
    assert response.json()['name'] == 'a' * 255


async def test_create_organization_duplicate_name_ignores_case_and_spaces(
    client: AsyncClient,
    db_session: AsyncSession,
    active_user_headers: dict[str, str],
):
    created = await _create_organization(client, active_user_headers, 'Acme')
    assert created.status_code == 201

    other = User(
        email='case@example.com',
        password='hash',
        status=UserStatus.ACTIVE,
    )
    db_session.add(other)
    await db_session.commit()
    access_token, _ = await authorize_user(other.id)

    response = await _create_organization(client, _bearer(access_token), '  aCmE  ')

    assert response.status_code == 409
    assert response.json()['detail'] == ORGANIZATION_NAME_TAKEN


async def test_create_organization_sees_membership_written_after_load(
    db_session: AsyncSession, active_user: User
):
    organization = make_organization(name='Existing')
    db_session.add(organization)
    await db_session.flush()
    await db_session.execute(
        text(
            'UPDATE users SET organization_id = :organization_id, role = :role '
            'WHERE id = :user_id'
        ),
        {
            'organization_id': organization.id,
            'role': OrganizationRole.MEMBER,
            'user_id': active_user.id,
        },
    )
    assert active_user.organization_id is None

    with pytest.raises(HTTPException) as exc_info:
        await create_organization(db_session, active_user, 'Acme')

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == USER_ALREADY_IN_ORGANIZATION
    assert active_user.organization_id == organization.id


async def test_create_organization_sees_deactivation_after_load(
    db_session: AsyncSession, active_user: User
):
    await db_session.execute(
        text('UPDATE users SET status = :status WHERE id = :user_id'),
        {'status': UserStatus.INACTIVE, 'user_id': active_user.id},
    )
    assert active_user.status is UserStatus.ACTIVE

    with pytest.raises(HTTPException) as exc_info:
        await create_organization(db_session, active_user, 'Acme')

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == USER_IS_INACTIVE
    assert active_user.status is UserStatus.INACTIVE


@pytest.mark.parametrize('name', ['', '   ', 'a' * 256])
async def test_create_organization_invalid_name(
    client: AsyncClient, active_user_headers: dict[str, str], name: str
):
    response = await _create_organization(client, active_user_headers, name)

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', 'name']


async def test_create_organization_without_name(
    client: AsyncClient, active_user_headers: dict[str, str]
):
    response = await client.post(
        app.url_path_for('create_organization_endpoint'),
        json={},
        headers=active_user_headers,
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', 'name']
