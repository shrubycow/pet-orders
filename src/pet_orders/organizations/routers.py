from fastapi import APIRouter, status

from pet_orders.auth.dependencies import (
    ACCESS_TOKEN_EXPIRED,
    INVALID_ACCESS_TOKEN,
    USER_IS_INACTIVE,
    ActiveUser,
)
from pet_orders.core.db.dependencies import SessionDep
from pet_orders.core.errors import error_response
from pet_orders.organizations.schemas import (
    OrganizationCreateRequest,
    OrganizationResponse,
)
from pet_orders.organizations.service import (
    ORGANIZATION_NAME_TAKEN,
    USER_ALREADY_IN_ORGANIZATION,
    create_organization,
)

router = APIRouter(
    prefix='/organizations',
    tags=['organizations'],
)


@router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: error_response(
            'Access token is expired or invalid',
            ACCESS_TOKEN_EXPIRED,
            INVALID_ACCESS_TOKEN,
        ),
        status.HTTP_403_FORBIDDEN: error_response(USER_IS_INACTIVE),
        status.HTTP_409_CONFLICT: error_response(
            'Organization cannot be created',
            ORGANIZATION_NAME_TAKEN,
            USER_ALREADY_IN_ORGANIZATION,
        ),
    },
)
async def create_organization_endpoint(
    organization: OrganizationCreateRequest,
    db_session: SessionDep,
    user: ActiveUser,
) -> OrganizationResponse:
    created = await create_organization(db_session, user, organization.name)
    return OrganizationResponse.model_validate(created)
