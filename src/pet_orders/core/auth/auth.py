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

async def _create_token_pair(user_id: uuid.UUID, access_id: uuid.UUID, refresh_id: uuid.UUID, family_id: uuid.UUID) -> tuple[str, str, datetime, datetime]:
    iat = now()
    refresh_exat = iat + REFRESH_TOKEN_EXPIRATION_DELTA
    access_token = jwt.encode({'sub': str(user_id), 'typ': 'access', 'exp': iat + ACCESS_TOKEN_EXPIRATION_DELTA, 'iat': iat, 'jti': str(access_id)}, auth_settings.secret_key, algorithm=ALGORITHM)
    refresh_token = jwt.encode({'sub': str(user_id), 'typ': 'refresh', 'exp': refresh_exat, 'iat': iat, 'jti': str(refresh_id), 'family': str(family_id)}, auth_settings.secret_key, algorithm=ALGORITHM)
    return access_token, refresh_token, iat, refresh_exat

async def authorize_user(
    user_id: uuid.UUID,
) -> tuple[str, str]:
    tokens = {
        'access_id': uuid.uuid4(),
        'refresh_id': uuid.uuid4(),
        'family_id': uuid.uuid4(),
    }
    access_token, refresh_token, iat, refresh_exat = await _create_token_pair(user_id, **tokens)
    family_exat = int((iat + FAMILY_TOKEN_EXPIRATION_DELTA).timestamp())
    await redis.hsetex(f'session:{str(tokens.get('family_id'))}', mapping={'current_jti': str(tokens.get('refresh_id')), 'family_exat': family_exat}, exat=refresh_exat)
    return access_token, refresh_token
