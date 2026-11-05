import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.core.db.db import DeletionForbidden
from pet_orders.organizations.models import Organization


async def test_session_delete_is_forbidden(
    db_session: AsyncSession, organization: Organization
):
    await db_session.delete(organization)

    with pytest.raises(DeletionForbidden, match='Organization cannot be deleted'):
        await db_session.flush()


async def test_bulk_delete_is_forbidden(
    db_session: AsyncSession, organization: Organization
):
    with pytest.raises(DeletionForbidden, match='Organization cannot be deleted'):
        await db_session.execute(delete(Organization))

    assert await db_session.get(Organization, organization.id) is not None
