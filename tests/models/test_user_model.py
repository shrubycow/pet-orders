import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from pet_orders.organizations.consts import OrganizationRole
from pet_orders.organizations.models import Organization
from pet_orders.users.models import User, UserStatus
from tests.db import assert_flush_violates
from tests.factories import make_organization, make_user


async def test_defaults(db_session: AsyncSession):
    user = make_user()
    db_session.add(user)
    await db_session.flush()

    assert user.status is UserStatus.INACTIVE
    assert user.organization_id is None
    assert user.role is None


async def test_email_is_unique(db_session: AsyncSession):
    db_session.add(make_user(email='same@example.com'))
    await db_session.flush()
    db_session.add(make_user(email='same@example.com'))

    await assert_flush_violates(db_session, 'uq_users_email')


async def test_member_of_organization(
    db_session: AsyncSession, organization: Organization
):
    user = make_user(organization=organization, role=OrganizationRole.ADMIN)
    db_session.add(user)
    await db_session.flush()

    role = await db_session.scalar(
        text('SELECT role FROM users WHERE id = :id'), {'id': user.id}
    )
    assert user.organization_id == organization.id
    assert role == 'admin'


async def test_organization_without_role(
    db_session: AsyncSession, organization: Organization
):
    db_session.add(make_user(organization=organization))

    await assert_flush_violates(db_session, 'ck_users_organization_role')


async def test_role_without_organization(db_session: AsyncSession):
    db_session.add(make_user(role=OrganizationRole.MEMBER))

    await assert_flush_violates(db_session, 'ck_users_organization_role')


async def test_single_owner_per_organization(
    db_session: AsyncSession, organization: Organization
):
    db_session.add(make_user('owner@example.com', organization, OrganizationRole.OWNER))
    await db_session.flush()
    db_session.add(
        make_user('second@example.com', organization, OrganizationRole.OWNER)
    )

    await assert_flush_violates(db_session, 'ix_users_organization_owner')


async def test_owners_of_different_organizations(
    db_session: AsyncSession, organization: Organization
):
    other = make_organization(name='Other')
    db_session.add_all(
        [
            make_user('owner@example.com', organization, OrganizationRole.OWNER),
            make_user('other@example.com', other, OrganizationRole.OWNER),
        ]
    )

    await db_session.flush()


async def test_many_admins_per_organization(
    db_session: AsyncSession, organization: Organization
):
    db_session.add_all(
        [
            make_user('first@example.com', organization, OrganizationRole.ADMIN),
            make_user('second@example.com', organization, OrganizationRole.ADMIN),
        ]
    )

    await db_session.flush()


@pytest.fixture
async def member_id(db_session: AsyncSession, organization: Organization):
    user = make_user(organization=organization, role=OrganizationRole.MEMBER)
    db_session.add(user)
    await db_session.flush()
    db_session.expunge_all()
    return user.id


async def test_organization_is_not_lazy_loaded(db_session: AsyncSession, member_id):
    user = await db_session.scalar(select(User).where(User.id == member_id))

    with pytest.raises(InvalidRequestError):
        _ = user.organization


async def test_organization_with_eager_load(
    db_session: AsyncSession, organization: Organization, member_id
):
    user = await db_session.scalar(
        select(User)
        .where(User.id == member_id)
        .options(selectinload(User.organization))
    )

    assert user.organization.id == organization.id
