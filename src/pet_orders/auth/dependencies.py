from typing import Annotated

import jwt
from fastapi import Body, Depends, status
from pydantic import ValidationError
from sqlalchemy import select

from pet_orders.core.auth.auth import ALGORITHM, get_session_key, oauth2_scheme
from pet_orders.core.auth.schemas import (
    RedisFamilySession,
    RefreshToken,
    RotateRefreshTokenData,
    AccessToken,
)
from pet_orders.core.auth.settings import auth_settings
from pet_orders.core.db.dependencies import SessionDep
from pet_orders.core.errors import raise_api_error
from pet_orders.core.redis.client import redis
from pet_orders.users.models import User, UserStatus

REFRESH_TOKEN_EXPIRED = 'Refresh token expired'
ACCESS_TOKEN_EXPIRED = 'Access token expired'
INVALID_REFRESH_TOKEN = 'Invalid refresh token'
INVALID_ACCESS_TOKEN = 'Invalid access token'
USER_IS_INACTIVE = 'User is not active'
USER_IS_ACTIVE = 'User is already active'

async def check_refresh_token(refresh_token: Annotated[str, Body(embed=True)]) -> RotateRefreshTokenData:
    try:
        payload = jwt.decode(refresh_token, auth_settings.secret_key, algorithms=[ALGORITHM])
        refresh_token_payload = RefreshToken.model_validate(payload)
    except jwt.ExpiredSignatureError as exc:
        raise_api_error(status.HTTP_401_UNAUTHORIZED, REFRESH_TOKEN_EXPIRED, cause=exc)
    except (jwt.InvalidTokenError, ValidationError) as exc: # type: ignore
        raise_api_error(status.HTTP_401_UNAUTHORIZED, INVALID_REFRESH_TOKEN, cause=exc)

    session_key = get_session_key(refresh_token_payload.family)
    session_data = await redis.hgetall(session_key)

    try:
        session_data = RedisFamilySession.model_validate(session_data)
    except ValidationError as exc:
        raise_api_error(status.HTTP_401_UNAUTHORIZED, INVALID_REFRESH_TOKEN, cause=exc)

    if session_data.current_jti != refresh_token_payload.jti:
        await redis.delete(session_key)
        raise_api_error(status.HTTP_401_UNAUTHORIZED, INVALID_REFRESH_TOKEN)

    return RotateRefreshTokenData(refresh_token=refresh_token_payload, session_data=session_data)


RefreshTokenDependency = Annotated[RotateRefreshTokenData, Depends(check_refresh_token)]

async def get_access_token(token: Depends(oauth2_scheme)) -> AccessToken:
    try:
        payload = jwt.decode(token, auth_settings.secret_key, algorithms=[ALGORITHM])
        access_token_payload = AccessToken.model_validate(payload)
    except jwt.ExpiredSignatureError as exc:
        raise_api_error(status.HTTP_401_UNAUTHORIZED, ACCESS_TOKEN_EXPIRED, cause=exc)
    except (jwt.InvalidTokenError, ValidationError) as exc: # type: ignore
        raise_api_error(status.HTTP_401_UNAUTHORIZED, INVALID_ACCESS_TOKEN, cause=exc)

    return access_token_payload

GetAccessTokenDependency = Annotated[AccessToken, Depends(get_access_token)]

async def get_user_id(access_token: GetAccessTokenDependency) -> str:
    return str(access_token.sub)

UserId = Annotated[str, Depends(get_user_id)]

async def get_current_user(access_token: GetAccessTokenDependency, db_session: SessionDep) -> User:
    result = await db_session.execute(select(User).where(User.id == access_token.sub))
    user = result.scalar_one_or_none()
    if user is None:
        raise_api_error(status.HTTP_401_UNAUTHORIZED, INVALID_ACCESS_TOKEN)
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

async def get_active_user(user: CurrentUser) -> User:
    if user.status is not UserStatus.ACTIVE:
        raise_api_error(status.HTTP_403_FORBIDDEN, USER_IS_INACTIVE)
    return user

ActiveUser = Annotated[User, Depends(get_active_user)]

async def get_inactive_user(user: CurrentUser) -> User:
    if user.status is not UserStatus.INACTIVE:
        raise_api_error(status.HTTP_403_FORBIDDEN, USER_IS_ACTIVE)
    return user

InactiveUser = Annotated[User, Depends(get_inactive_user)]
