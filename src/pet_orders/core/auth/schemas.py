from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from pet_orders.core.auth.consts import TokenType


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class TokenPayload(BaseModel):
    sub: UUID
    exp: int
    iat: int
    jti: UUID


class AccessToken(TokenPayload):
    typ: Literal[TokenType.ACCESS]


class RefreshToken(TokenPayload):
    typ: Literal[TokenType.REFRESH]
    family: UUID


class RedisFamilySession(BaseModel):
    current_jti: UUID
    family_exat: int


class RotateRefreshTokenData(BaseModel):
    refresh_token: RefreshToken
    session_data: RedisFamilySession


class Credentials(BaseModel):
    email: Annotated[
        EmailStr, Field(description='User email', examples=['test@example.com'])
    ]
    password: Annotated[
        str, Field(description='User password', examples=['password'], max_length=255)
    ]
