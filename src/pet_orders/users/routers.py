from fastapi import APIRouter, status

from pet_orders.core.auth.schemas import TokenPair
from pet_orders.core.db.dependencies import SessionDep
from pet_orders.core.dependencies import limit_by_ip
from pet_orders.core.queue.dependencies import BrokerDep
from pet_orders.users.schemas import UserCreateRequest
from pet_orders.users.service import register_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[limit_by_ip(window_seconds=60)],
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "User with this email already exists",
        },
    },
)
async def create_user(
    user: UserCreateRequest,
    db_session: SessionDep,
    broker: BrokerDep,
) -> TokenPair:
    token_pair = await register_user(
        db_session,
        broker,
        email=user.email,
        password=user.password,
    )
    return token_pair
