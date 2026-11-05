import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.organizations.consts import OrganizationStatus
from pet_orders.organizations.models import Organization
from tests.db import assert_flush_violates
from tests.factories import make_organization


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


@pytest.mark.parametrize('name', ['Acme', 'ACME', ' acme '])
async def test_name_is_unique(
    db_session: AsyncSession, organization: Organization, name: str
):
    db_session.add(make_organization(name=name))

    await assert_flush_violates(db_session, 'ix_organizations_name')


async def _delete_organization(db_session: AsyncSession, organization_id) -> None:
    await db_session.execute(
        text('DELETE FROM organizations WHERE id = :id'),
        {'id': organization_id},
    )


async def test_delete_without_dependents(
    db_session: AsyncSession, organization: Organization
):
    organization_id = organization.id
    await _delete_organization(db_session, organization_id)
    db_session.expunge_all()

    assert await db_session.get(Organization, organization_id) is None
