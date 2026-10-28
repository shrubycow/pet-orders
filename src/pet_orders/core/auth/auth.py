import uuid
from datetime import datetime, timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer

from pet_orders.core.auth.consts import TokenType
from pet_orders.core.auth.settings import auth_settings
from pet_orders.core.redis.client import redis
from pet_orders.core.utils import from_timestamp, now

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRATION_DELTA = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRATION_DELTA = timedelta(days=7)
FAMILY_TOKEN_EXPIRATION_DELTA = timedelta(days=30)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')

def get_session_key(family_id: uuid.UUID) -> str:
    return f'session:{str(family_id)}'

def _create_token_pair(
    user_id: uuid.UUID,
    access_id: uuid.UUID,
    refresh_id: uuid.UUID,
    family_id: uuid.UUID,
    refresh_exat: datetime | None = None,
) -> tuple[str, str, datetime, datetime]:
    iat = now()
    if refresh_exat is None:
        refresh_exat = iat + REFRESH_TOKEN_EXPIRATION_DELTA
    access_token = jwt.encode({'sub': str(user_id), 'typ': TokenType.ACCESS, 'exp': iat + ACCESS_TOKEN_EXPIRATION_DELTA, 'iat': iat, 'jti': str(access_id)}, auth_settings.secret_key, algorithm=ALGORITHM)
    refresh_token = jwt.encode({'sub': str(user_id), 'typ': TokenType.REFRESH, 'exp': refresh_exat, 'iat': iat, 'jti': str(refresh_id), 'family': str(family_id)}, auth_settings.secret_key, algorithm=ALGORITHM)
    return access_token, refresh_token, iat, refresh_exat

async def authorize_user(
    user_id: uuid.UUID,
) -> tuple[str, str]:
    tokens = {
        'access_id': uuid.uuid4(),
        'refresh_id': uuid.uuid4(),
        'family_id': uuid.uuid4(),
    }
    access_token, refresh_token, iat, refresh_exat = _create_token_pair(user_id, **tokens)
    family_exat = int((iat + FAMILY_TOKEN_EXPIRATION_DELTA).timestamp())
    session_key = get_session_key(tokens['family_id'])
    await redis.hsetex(session_key, mapping={'current_jti': str(tokens['refresh_id']), 'family_exat': family_exat}, exat=refresh_exat)
    return access_token, refresh_token

async def rotate_refresh_token(
    user_id: uuid.UUID,
    family_id: uuid.UUID,
    family_exat: int,
) -> tuple[str, str]:
    refresh_exat = min(now() + REFRESH_TOKEN_EXPIRATION_DELTA, from_timestamp(family_exat))
    access_id = uuid.uuid4()
    refresh_id = uuid.uuid4()
    access_token, refresh_token, _, refresh_exat = _create_token_pair(
        user_id,
        access_id,
        refresh_id,
        family_id,
        refresh_exat,
    )
    await redis.hsetex(
        get_session_key(family_id),
        mapping={'current_jti': str(refresh_id), 'family_exat': family_exat},
        exat=refresh_exat,
    )
    return access_token, refresh_token
