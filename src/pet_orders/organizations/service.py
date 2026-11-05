from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.core.errors import raise_api_error
from pet_orders.organizations.consts import OrganizationRole
from pet_orders.organizations.models import Organization
from pet_orders.users.models import User

_ORGANIZATIONS_NAME_CONSTRAINT = 'uq_organizations_name'
ORGANIZATION_NAME_TAKEN = 'Organization with this name already exists'
USER_ALREADY_IN_ORGANIZATION = 'User already belongs to an organization'


async def _commit_organization(db_session: AsyncSession) -> None:
    try:
        await db_session.commit()
    except IntegrityError as exc:
        await db_session.rollback()
        driver_error = getattr(exc.orig, 'orig', None) or exc.orig
        if (
            getattr(driver_error, 'constraint_name', None)
            != _ORGANIZATIONS_NAME_CONSTRAINT
        ):
            raise
        raise_api_error(status.HTTP_409_CONFLICT, ORGANIZATION_NAME_TAKEN, cause=exc)


async def create_organization(
    db_session: AsyncSession, user: User, name: str
) -> Organization:
    result = await db_session.execute(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    locked_user = result.scalar_one()
    if locked_user.organization_id is not None:
        raise_api_error(status.HTTP_409_CONFLICT, USER_ALREADY_IN_ORGANIZATION)

    organization = Organization(name=name)
    locked_user.organization = organization
    locked_user.role = OrganizationRole.OWNER
    db_session.add(organization)
    await _commit_organization(db_session)
    return organization
