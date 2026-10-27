from typing import Annotated

import jwt
from fastapi import Body, Depends, status
from pydantic import ValidationError

from pet_orders.core.auth.auth import ALGORITHM, get_session_key
from pet_orders.core.auth.schemas import (
    RedisFamilySession,
    RefreshToken,
    RotateRefreshTokenData,
)
from pet_orders.core.auth.settings import auth_settings
from pet_orders.core.errors import raise_api_error
from pet_orders.core.redis.client import redis

REFRESH_TOKEN_EXPIRED = 'Refresh token expired'
INVALID_REFRESH_TOKEN = 'Invalid refresh token'

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
