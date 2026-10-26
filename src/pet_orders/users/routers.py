from fastapi import APIRouter, status

from pet_orders.core.db.dependencies import SessionDep
from pet_orders.core.dependencies import limit_by_ip
from pet_orders.core.queue.dependencies import BrokerDep
from pet_orders.users.schemas import UserCreateRequest, UserResponse
from pet_orders.users.service import create_user as register_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[limit_by_ip(window_seconds=60)])
async def create_user(
    user: UserCreateRequest,
    session: SessionDep,
    broker: BrokerDep,
) -> UserResponse:
    created = await register_user(
        session,
        broker,
        email=user.email,
        password=user.password,
    )
    return UserResponse.model_validate(created)
