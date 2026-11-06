from fastapi import APIRouter, status

from pet_orders.auth.dependencies import (
    ACCESS_TOKEN_EXPIRED,
    INVALID_ACCESS_TOKEN,
    USER_IS_INACTIVE,
)
from pet_orders.core.db.dependencies import SessionDep
from pet_orders.core.errors import error_response
from pet_orders.orders.schemas import ProductCreateRequest, ProductResponse
from pet_orders.orders.service import (
    ORGANIZATION_IS_NOT_ACTIVE,
    PRODUCT_SKU_TAKEN,
    create_product,
)
from pet_orders.organizations.consts import USER_NOT_IN_ORGANIZATION
from pet_orders.organizations.dependencies import OrganizationUser

router = APIRouter(
    prefix='/products',
    tags=['products'],
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
        status.HTTP_403_FORBIDDEN: error_response(
            'Product cannot be created',
            USER_IS_INACTIVE,
            USER_NOT_IN_ORGANIZATION,
            ORGANIZATION_IS_NOT_ACTIVE,
        ),
        status.HTTP_409_CONFLICT: error_response(PRODUCT_SKU_TAKEN),
    },
)
async def create_product_endpoint(
    product: ProductCreateRequest,
    db_session: SessionDep,
    user: OrganizationUser,
) -> ProductResponse:
    created = await create_product(db_session, user, product)
    return ProductResponse.model_validate(created)
