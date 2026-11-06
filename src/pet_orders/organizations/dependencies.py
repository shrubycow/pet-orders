from typing import Annotated

from fastapi import Depends, status

from pet_orders.auth.dependencies import ActiveUser
from pet_orders.core.errors import raise_api_error
from pet_orders.organizations.consts import USER_NOT_IN_ORGANIZATION
from pet_orders.users.models import User


async def get_organization_user(user: ActiveUser) -> User:
    if user.organization_id is None:
        raise_api_error(status.HTTP_403_FORBIDDEN, USER_NOT_IN_ORGANIZATION)
    return user


OrganizationUser = Annotated[User, Depends(get_organization_user)]
