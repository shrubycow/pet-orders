from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.orders.consts import CurrencyEnum
from pet_orders.organizations.models import Organization
from tests.db import assert_flush_violates
from tests.factories import make_organization, make_product


async def test_defaults(db_session: AsyncSession, organization: Organization):
    product = make_product(organization)
    db_session.add(product)
    await db_session.flush()
    await db_session.refresh(product)

    assert product.stock == 0
    assert product.is_active is True
    assert product.created_at is not None


async def test_price_and_currency_round_trip(
    db_session: AsyncSession, organization: Organization
):
    product = make_product(
        organization, price=Decimal('1234.5678'), currency=CurrencyEnum.EUR
    )
    db_session.add(product)
    await db_session.flush()

    row = (
        await db_session.execute(
            text('SELECT price, currency FROM products WHERE id = :id'),
            {'id': product.id},
        )
    ).one()
    assert row.price == Decimal('1234.5678')
    assert row.currency == 'EUR'


async def test_organization_is_required(db_session: AsyncSession):
    db_session.add(make_product(organization=None))

    with pytest.raises(IntegrityError, match='organization_id'):
        await db_session.flush()


async def test_sku_is_unique_within_organization(
    db_session: AsyncSession, organization: Organization
):
    db_session.add(make_product(organization, sku='PRD-000001'))
    await db_session.flush()
    db_session.add(make_product(organization, sku='PRD-000001'))

    await assert_flush_violates(db_session, 'uq_products_organization_id_sku')


async def test_same_sku_in_different_organizations(
    db_session: AsyncSession, organization: Organization
):
    other = make_organization(name='Other')
    db_session.add_all(
        [
            make_product(organization, sku='PRD-000001'),
            make_product(other, sku='PRD-000001'),
        ]
    )

    await db_session.flush()


async def test_zero_price_and_stock(
    db_session: AsyncSession, organization: Organization
):
    db_session.add(make_product(organization, price=Decimal(0), stock=0))

    await db_session.flush()


@pytest.mark.parametrize(
    ('field', 'value', 'constraint'),
    [
        ('price', Decimal('-0.0001'), 'ck_products_price_non_negative'),
        ('stock', -1, 'ck_products_stock_non_negative'),
    ],
)
async def test_negative_values(
    db_session: AsyncSession,
    organization: Organization,
    field: str,
    value: Decimal | int,
    constraint: str,
):
    db_session.add(make_product(organization, **{field: value}))

    await assert_flush_violates(db_session, constraint)
