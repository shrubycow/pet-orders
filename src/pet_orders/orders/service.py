from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from pet_orders.auth.dependencies import USER_IS_INACTIVE
from pet_orders.core.errors import raise_api_error
from pet_orders.orders.models import Product
from pet_orders.orders.schemas import ProductCreateRequest
from pet_orders.organizations.consts import (
    USER_NOT_IN_ORGANIZATION,
    OrganizationStatus,
)
from pet_orders.users.models import User, UserStatus

_PRODUCTS_SKU_CONSTRAINT = 'uq_products_organization_id_sku'
PRODUCT_SKU_TAKEN = 'Product with this SKU already exists'
ORGANIZATION_IS_NOT_ACTIVE = 'Organization is not active'


async def _commit_product(db_session: AsyncSession) -> None:
    try:
        await db_session.commit()
    except IntegrityError as exc:
        await db_session.rollback()
        driver_error = getattr(exc.orig, 'orig', None) or exc.orig
        if getattr(driver_error, 'constraint_name', None) != _PRODUCTS_SKU_CONSTRAINT:
            raise
        raise_api_error(status.HTTP_409_CONFLICT, PRODUCT_SKU_TAKEN, cause=exc)


async def create_product(
    db_session: AsyncSession,
    user: User,
    product: ProductCreateRequest,
) -> Product:
    result = await db_session.execute(
        select(User)
        .join(User.organization)
        .where(User.id == user.id)
        .options(contains_eager(User.organization))
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    locked_user = result.scalar_one_or_none()
    if locked_user is None or locked_user.organization_id is None:
        raise_api_error(status.HTTP_403_FORBIDDEN, USER_NOT_IN_ORGANIZATION)
    if locked_user.status is not UserStatus.ACTIVE:
        raise_api_error(status.HTTP_403_FORBIDDEN, USER_IS_INACTIVE)
    organization = locked_user.organization
    if organization is None:
        raise_api_error(status.HTTP_403_FORBIDDEN, USER_NOT_IN_ORGANIZATION)
    if organization.status is not OrganizationStatus.ACTIVE:
        raise_api_error(status.HTTP_403_FORBIDDEN, ORGANIZATION_IS_NOT_ACTIVE)

    created = Product(
        organization_id=organization.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        price=product.price,
        currency=product.currency,
        stock=product.stock,
        is_active=product.is_active,
    )
    db_session.add(created)
    await _commit_product(db_session)
    return created
