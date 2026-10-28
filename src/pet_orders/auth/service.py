from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from pet_orders.auth.schemas import LoginUserResponse
from pet_orders.core.auth.auth import authorize_user, rotate_refresh_token
from pet_orders.core.auth.password import DUMMY_PASSWORD_HASH, verify_auth_code, verify_password
from pet_orders.core.auth.schemas import RotateRefreshTokenData, TokenPair
from pet_orders.core.errors import raise_api_error
from pet_orders.core.redis.client import redis
from pet_orders.users.models import User, UserStatus
from pet_orders.users.service import get_user_created_key, send_user_created_email

INVALID_CODE = 'Invalid code'
INVALID_CREDENTIALS = 'Invalid email or password'


async def rotate_token_pair(refresh_token_data: RotateRefreshTokenData) -> TokenPair:
    access_token, refresh_token = await rotate_refresh_token(refresh_token_data.refresh_token.sub, refresh_token_data.refresh_token.family, refresh_token_data.session_data.family_exat)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)

async def verify_email(db_session: AsyncSession, user: User, code: str) -> None:
    user_created_key = get_user_created_key(user.id)
    hashed_code: str = (await redis.get(user_created_key)) or ''
    if not verify_auth_code(code, hashed_code):
        raise_api_error(status.HTTP_400_BAD_REQUEST, INVALID_CODE)
    user.status = UserStatus.ACTIVE
    await db_session.commit()
    await redis.delete(user_created_key)

async def resend_auth_code(user: User) -> None:
    await send_user_created_email(user.id, user.email)

async def login_user(db_session: AsyncSession, email: str, password: str) -> LoginUserResponse:
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    password_hash = user.password if user is not None else DUMMY_PASSWORD_HASH
    password_matches = await verify_password(password, password_hash)
    if user is None or not password_matches:
        raise_api_error(status.HTTP_401_UNAUTHORIZED, INVALID_CREDENTIALS)
    access_token, refresh_token = await authorize_user(user.id)
    return LoginUserResponse(access_token=access_token, refresh_token=refresh_token, status=user.status)
