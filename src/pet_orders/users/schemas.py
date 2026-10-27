from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from pet_orders.users.models import UserStatus


class UserCreateRequest(BaseModel):
    email: Annotated[EmailStr, Field(description="User email", examples=["test@example.com"])]
    password: Annotated[str, Field(description="User password", examples=["password"], max_length=255)]


class UserCreatedEvent(BaseModel):
    email: EmailStr
    user_id: UUID


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    status: UserStatus

class UserLoginRequest(UserCreateRequest):
    pass