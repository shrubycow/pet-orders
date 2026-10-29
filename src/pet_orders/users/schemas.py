from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from pet_orders.core.auth.schemas import Credentials
from pet_orders.users.models import UserStatus


class UserCreateRequest(Credentials):
    pass


class UserCreatedEvent(BaseModel):
    email: EmailStr
    user_id: UUID


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    status: UserStatus
