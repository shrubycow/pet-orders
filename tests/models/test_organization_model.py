import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.organizations.consts import OrganizationRole, OrganizationStatus
from pet_orders.organizations.models import Organization
from tests.db import assert_flush_violates
from tests.factories import make_organization, make_product, make_user


async def _reload(db_session: AsyncSession, organization: Organization) -> Organization:
    organization_id = organization.id
    db_session.expunge_all()
    reloaded = await db_session.get(Organization, organization_id)
    assert reloaded is not None
    return reloaded


async def test_defaults(db_session: AsyncSession, organization: Organization):
    await db_session.refresh(organization)

    assert organization.status is OrganizationStatus.ACTIVE
    assert organization.created_at is not None
    assert organization.updated_at is not None


async def test_status_is_stored_as_value(
    db_session: AsyncSession, organization: Organization
):
    status = await db_session.scalar(
        text('SELECT status FROM organizations WHERE id = :id'),
        {'id': organization.id},
    )

    assert status == 'active'


async def test_name_is_unique(db_session: AsyncSession, organization: Organization):
    db_session.add(make_organization(name=organization.name))

    await assert_flush_violates(db_session, 'uq_organizations_name')


async def test_delete_without_dependents(
    db_session: AsyncSession, organization: Organization
):
    await db_session.delete(organization)
    await db_session.flush()

    assert await db_session.get(Organization, organization.id) is None


async def _with_children(
    db_session: AsyncSession,
    organization: Organization,
    children: str,
    reload: bool,
) -> Organization:
    if reload:
        return await _reload(db_session, organization)
    await db_session.refresh(organization, [children])
    assert getattr(organization, children)
    return organization


restricted_delete = pytest.mark.parametrize(
    'reload', [True, False], ids=['children_not_loaded', 'children_loaded']
)


@restricted_delete
async def test_delete_with_users_is_restricted(
    db_session: AsyncSession, organization: Organization, reload: bool
):
    db_session.add(make_user(organization=organization, role=OrganizationRole.MEMBER))
    await db_session.flush()

    organization = await _with_children(db_session, organization, 'users', reload)
    await db_session.delete(organization)

    await assert_flush_violates(
        db_session, 'fk_users_organization_id_organizations'
    )


@restricted_delete
async def test_delete_with_products_is_restricted(
    db_session: AsyncSession, organization: Organization, reload: bool
):
    db_session.add(make_product(organization))
    await db_session.flush()

    organization = await _with_children(db_session, organization, 'products', reload)
    await db_session.delete(organization)

    await assert_flush_violates(
        db_session, 'fk_products_organization_id_organizations'
    )
