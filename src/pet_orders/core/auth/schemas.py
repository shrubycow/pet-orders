from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str

class TokenPayload(BaseModel):
    sub: UUID
    exp: int
    iat: int
    jti: UUID

class AccessToken(TokenPayload):
    typ: Literal['access']

class RefreshToken(TokenPayload):
    typ: Literal['refresh']
    family: UUID

class RedisFamilySession(BaseModel):
    current_jti: UUID
    family_exat: int

class RotateRefreshTokenData(BaseModel):
    refresh_token: RefreshToken
    session_data: RedisFamilySession
