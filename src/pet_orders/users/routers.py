from fastapi import APIRouter

from pet_orders.db.dependencies import SessionDep
from pet_orders.users.schemas import UserCreateRequest

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/")
async def create_user(user: UserCreateRequest, session: SessionDep) -> None:
    pass