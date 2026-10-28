from typing import Annotated
from fastapi import APIRouter, Body, Response, status

from pet_orders.auth.dependencies import (
    ACCESS_TOKEN_EXPIRED,
    INVALID_ACCESS_TOKEN,
    INVALID_REFRESH_TOKEN,
    REFRESH_TOKEN_EXPIRED,
    USER_IS_ACTIVE,
    InactiveUser,
    RefreshTokenDependency,
    UserId,
)
from pet_orders.auth.schemas import LoginUserResponse
from pet_orders.auth.service import (
    INVALID_CODE,
    INVALID_CREDENTIALS,
    login_user,
    resend_auth_code,
    rotate_token_pair,
    verify_email,
)
from pet_orders.core.auth.auth import oauth2_scheme
from pet_orders.core.auth.schemas import Credentials, TokenPair
from pet_orders.core.db.dependencies import SessionDep
from pet_orders.core.dependencies import rate_limit
from pet_orders.core.errors import error_response

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)

@router.post(
    '/refresh',
    responses={
        status.HTTP_401_UNAUTHORIZED: error_response(
            'Refresh token is expired or invalid',
            REFRESH_TOKEN_EXPIRED,
            INVALID_REFRESH_TOKEN,
        ),
    },
)
async def refresh_token(
    refresh_token_data: RefreshTokenDependency,
) -> TokenPair:
    return await rotate_token_pair(refresh_token_data)

@router.post(
    '/verify-email',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[rate_limit(window_seconds=7, subject=UserId)],
    responses={
        status.HTTP_400_BAD_REQUEST: error_response(INVALID_CODE),
        status.HTTP_401_UNAUTHORIZED: error_response(
            'Access token is expired or invalid',
            ACCESS_TOKEN_EXPIRED,
            INVALID_ACCESS_TOKEN,
        ),
        status.HTTP_403_FORBIDDEN: error_response(USER_IS_ACTIVE),
        status.HTTP_429_TOO_MANY_REQUESTS: error_response('Too many requests'),
    },
)
async def verify_email_code(db_session: SessionDep, user: InactiveUser, code: Annotated[str, Body(embed=True)]) -> None:
    await verify_email(db_session, user, code)

@router.post(
    '/login',
    responses={
        status.HTTP_401_UNAUTHORIZED: error_response(INVALID_CREDENTIALS),
    },
)
async def login(
    login_data: Credentials,
    db_session: SessionDep,
) -> LoginUserResponse:
    return await login_user(db_session, login_data.email, login_data.password)

@router.post(
    '/resend-auth-code',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[rate_limit(window_seconds=60, subject=UserId)],
    responses={
        status.HTTP_401_UNAUTHORIZED: error_response(
            'Access token is expired or invalid',
            ACCESS_TOKEN_EXPIRED,
            INVALID_ACCESS_TOKEN,
        ),
        status.HTTP_403_FORBIDDEN: error_response(USER_IS_ACTIVE),
        status.HTTP_429_TOO_MANY_REQUESTS: error_response('Too many requests'),
    },
)
async def resend_auth_code_email(user: InactiveUser) -> None:
    await resend_auth_code(user)