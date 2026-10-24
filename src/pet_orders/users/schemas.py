from typing import Annotated
from pydantic import BaseModel, EmailStr, Field

class UserCreateRequest(BaseModel):
    email: Annotated[EmailStr, Field(description="User email", examples=["test@example.com"])]
    password: Annotated[str, Field(description="User password", examples=["password"])]