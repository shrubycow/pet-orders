import uuid
from datetime import datetime, timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer

from pet_orders.core.auth.settings import auth_settings
from pet_orders.core.redis.client import redis
from pet_orders.core.utils import now

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION_DELTA = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRATION_DELTA = timedelta(days=7)
FAMILY_TOKEN_EXPIRATION_DELTA = timedelta(days=30)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

async def _create_token_pair(user_id: uuid.UUID, access_id: uuid.UUID, refresh_id: uuid.UUID, family_id: uuid.UUID) -> tuple[str, str, datetime]:
    iat = now()
    access_token = jwt.encode({'sub': str(user_id), 'typ': 'access', 'exp': now() + ACCESS_TOKEN_EXPIRATION_DELTA, 'iat': iat, 'jti': str(access_id)}, auth_settings.SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode({'sub': str(user_id), 'typ': 'refresh', 'exp': now() + REFRESH_TOKEN_EXPIRATION_DELTA, 'iat': iat, 'jti': str(refresh_id), 'family': str(family_id)}, auth_settings.SECRET_KEY, algorithm=ALGORITHM)
    return access_token, refresh_token, iat

async def authorize_user(
    user_id: uuid.UUID,
) -> tuple[str, str]:
    tokens = {
        'access_id': str(uuid.uuid4()),
        'refresh_id': str(uuid.uuid4()),
        'family_id': str(uuid.uuid4()),
    }
    access_token, refresh_token, iat = await _create_token_pair(user_id, **tokens)
    ex = int((iat + FAMILY_TOKEN_EXPIRATION_DELTA).timestamp())
    await redis.hsetex(f'session:{tokens.get('family_id')}', mapping={'current_jti': tokens.get('refresh_id'), 'absolute_exp': now() + FAMILY_TOKEN_EXPIRATION_DELTA}, ex=ex)
    return access_token, refresh_token
