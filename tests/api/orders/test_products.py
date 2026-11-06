from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.auth.dependencies import (
    ACCESS_TOKEN_EXPIRED,
    INVALID_ACCESS_TOKEN,
    USER_IS_INACTIVE,
)
from pet_orders.core.auth.auth import authorize_user
from pet_orders.core.auth.consts import TokenType
from pet_orders.main import app
from pet_orders.orders.consts import CurrencyEnum
from pet_orders.orders.models import Product
from pet_orders.orders.schemas import ProductCreateRequest
from pet_orders.orders.service import (
    ORGANIZATION_IS_NOT_ACTIVE,
    PRODUCT_SKU_TAKEN,
    create_product,
)
from pet_orders.organizations.consts import (
    USER_NOT_IN_ORGANIZATION,
    OrganizationStatus,
)
from pet_orders.organizations.models import Organization
from pet_orders.users.models import User, UserStatus
from tests.api.helpers import bearer, expired_token
from tests.factories import add_user_to_organization, make_organization


def _product_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        'sku': 'PRD-000001',
        'name': 'Dog food',
        'description': 'Dry food for adult dogs',
        'price': '10.5000',
        'currency': CurrencyEnum.USD,
    }
    payload.update(overrides)
    return payload


def _product_request() -> ProductCreateRequest:
    return ProductCreateRequest(
        sku='PRD-000001',
        name='Dog food',
        description='Dry food for adult dogs',
        price=Decimal('10.5000'),
        currency=CurrencyEnum.USD,
    )


async def _create_product(
    client: AsyncClient,
    headers: dict[str, str],
    **overrides: object,
):
    return await client.post(
        app.url_path_for('create_product_endpoint'),
        json=_product_payload(**overrides),
        headers=headers,
    )


async def _products_with_sku(db_session: AsyncSession, sku: str) -> int:
    count = await db_session.scalar(
        select(func.count()).select_from(Product).where(Product.sku == sku)
    )
    return count or 0


async def test_create_product(
    client: AsyncClient,
    db_session: AsyncSession,
    member_organization: Organization,
    active_user_headers: dict[str, str],
):
    response = await _create_product(
        client,
        active_user_headers,
        stock=4,
        is_active=False,
    )

    assert response.status_code == 201
    body = response.json()
    assert body['organization_id'] == str(member_organization.id)
    assert body['sku'] == 'PRD-000001'
    assert body['name'] == 'Dog food'
    assert body['description'] == 'Dry food for adult dogs'
    assert body['price'] == '10.5000'
    assert body['currency'] == CurrencyEnum.USD
    assert body['stock'] == 4
    assert body['is_active'] is False

    product = await db_session.get(Product, UUID(body['id']))
    assert product is not None
    assert product.organization_id == member_organization.id
    assert product.price == Decimal('10.5000')
    assert product.currency is CurrencyEnum.USD
    assert product.stock == 4
    assert product.is_active is False


async def test_create_product_defaults(
    client: AsyncClient,
    member_organization: Organization,
    active_user_headers: dict[str, str],
):
    response = await _create_product(client, active_user_headers)

    assert response.status_code == 201
    body = response.json()
    assert body['stock'] == 0
    assert body['is_active'] is True
    assert body['organization_id'] == str(member_organization.id)


async def test_create_product_strips_text(
    client: AsyncClient,
    db_session: AsyncSession,
    member_organization: Organization,
    active_user_headers: dict[str, str],
):
    response = await _create_product(
        client,
        active_user_headers,
        sku='  PRD-000001  ',
        name='  Dog food  ',
        description='  Dry food  ',
    )

    assert response.status_code == 201
    body = response.json()
    assert body['sku'] == 'PRD-000001'
    assert body['name'] == 'Dog food'
    assert body['description'] == 'Dry food'
    product = await db_session.get(Product, UUID(body['id']))
    assert product is not None
    assert product.sku == 'PRD-000001'
    assert product.name == 'Dog food'
    assert product.description == 'Dry food'
    assert product.organization_id == member_organization.id


async def test_create_product_duplicate_sku(
    client: AsyncClient,
    db_session: AsyncSession,
    member_organization: Organization,
    active_user_headers: dict[str, str],
):
    created = await _create_product(client, active_user_headers)
    assert created.status_code == 201

    response = await _create_product(client, active_user_headers, name='Other name')

    assert response.status_code == 409
    assert response.json()['detail'] == PRODUCT_SKU_TAKEN
    assert await _products_with_sku(db_session, 'PRD-000001') == 1
    assert created.json()['organization_id'] == str(member_organization.id)


async def test_create_product_same_sku_in_another_organization(
    client: AsyncClient,
    db_session: AsyncSession,
    active_user: User,
    active_user_headers: dict[str, str],
):
    add_user_to_organization(active_user, make_organization(name='Acme'))
    other = User(
        email='other@example.com',
        password='hash',
        status=UserStatus.ACTIVE,
    )
    add_user_to_organization(other, make_organization(name='Other'))
    db_session.add(other)
    await db_session.commit()
    access_token, _ = await authorize_user(other.id)

    first = await _create_product(client, active_user_headers)
    second = await _create_product(client, bearer(access_token))

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()['organization_id'] != second.json()['organization_id']
    assert await _products_with_sku(db_session, 'PRD-000001') == 2


async def test_create_product_without_organization(
    client: AsyncClient, active_user_headers: dict[str, str]
):
    response = await _create_product(client, active_user_headers)

    assert response.status_code == 403
    assert response.json()['detail'] == USER_NOT_IN_ORGANIZATION


@pytest.mark.parametrize(
    'organization_status',
    [OrganizationStatus.SUSPENDED, OrganizationStatus.ARCHIVED],
)
async def test_create_product_when_organization_is_not_active(
    client: AsyncClient,
    db_session: AsyncSession,
    active_user: User,
    active_user_headers: dict[str, str],
    organization_status: OrganizationStatus,
):
    organization = make_organization()
    organization.status = organization_status
    add_user_to_organization(active_user, organization)
    await db_session.commit()

    response = await _create_product(client, active_user_headers)

    assert response.status_code == 403
    assert response.json()['detail'] == ORGANIZATION_IS_NOT_ACTIVE
    assert await _products_with_sku(db_session, 'PRD-000001') == 0


async def test_create_product_inactive_user(
    client: AsyncClient, inactive_user_headers: dict[str, str]
):
    response = await _create_product(client, inactive_user_headers)

    assert response.status_code == 403
    assert response.json()['detail'] == USER_IS_INACTIVE


async def test_create_product_without_token(client: AsyncClient):
    response = await _create_product(client, {})

    assert response.status_code == 401


@pytest.mark.parametrize(
    ('token', 'detail'),
    [
        (expired_token(TokenType.ACCESS), ACCESS_TOKEN_EXPIRED),
        ('not-a-jwt', INVALID_ACCESS_TOKEN),
    ],
)
async def test_create_product_bad_access_token(
    client: AsyncClient, token: str, detail: str
):
    response = await _create_product(client, bearer(token))

    assert response.status_code == 401
    assert response.json()['detail'] == detail


async def test_create_product_unknown_user(client: AsyncClient):
    access_token, _ = await authorize_user(uuid4())

    response = await _create_product(client, bearer(access_token))

    assert response.status_code == 401
    assert response.json()['detail'] == INVALID_ACCESS_TOKEN


@pytest.mark.usefixtures('member_organization')
@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('sku', ''),
        ('sku', '   '),
        ('sku', 'a' * 65),
        ('name', ''),
        ('name', '   '),
        ('name', 'a' * 256),
        ('description', ''),
        ('description', '   '),
        ('price', '-0.0001'),
        ('price', '1.12345'),
        ('stock', -1),
        ('currency', 'GBP'),
    ],
)
async def test_create_product_invalid_field(
    client: AsyncClient,
    active_user_headers: dict[str, str],
    field: str,
    value: object,
):
    response = await _create_product(client, active_user_headers, **{field: value})

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', field]


@pytest.mark.usefixtures('member_organization')
async def test_create_product_without_sku(
    client: AsyncClient,
    active_user_headers: dict[str, str],
):
    payload = _product_payload()
    payload.pop('sku')

    response = await client.post(
        app.url_path_for('create_product_endpoint'),
        json=payload,
        headers=active_user_headers,
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', 'sku']


async def test_create_product_sees_inactive_organization_after_load(
    db_session: AsyncSession,
    active_user: User,
    member_organization: Organization,
):
    await db_session.execute(
        text('UPDATE organizations SET status = :status WHERE id = :organization_id'),
        {
            'status': OrganizationStatus.SUSPENDED,
            'organization_id': member_organization.id,
        },
    )
    assert member_organization.status is OrganizationStatus.ACTIVE

    with pytest.raises(HTTPException) as exc_info:
        await create_product(db_session, active_user, _product_request())

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == ORGANIZATION_IS_NOT_ACTIVE
    assert member_organization.status is OrganizationStatus.SUSPENDED


@pytest.mark.usefixtures('member_organization')
async def test_create_product_sees_deactivation_after_load(
    db_session: AsyncSession,
    active_user: User,
):
    await db_session.execute(
        text('UPDATE users SET status = :status WHERE id = :user_id'),
        {'status': UserStatus.INACTIVE, 'user_id': active_user.id},
    )
    assert active_user.status is UserStatus.ACTIVE

    with pytest.raises(HTTPException) as exc_info:
        await create_product(db_session, active_user, _product_request())

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == USER_IS_INACTIVE
    assert active_user.status is UserStatus.INACTIVE


async def test_create_product_sees_removed_membership_after_load(
    db_session: AsyncSession,
    active_user: User,
    member_organization: Organization,
):
    await db_session.execute(
        text(
            'UPDATE users SET organization_id = NULL, role = NULL WHERE id = :user_id'
        ),
        {'user_id': active_user.id},
    )
    assert active_user.organization_id == member_organization.id

    with pytest.raises(HTTPException) as exc_info:
        await create_product(db_session, active_user, _product_request())

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == USER_NOT_IN_ORGANIZATION
    assert await _products_with_sku(db_session, 'PRD-000001') == 0
