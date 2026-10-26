from datetime import UTC, datetime, timedelta
import uuid
from fastapi.security import OAuth2PasswordBearer
import jwt

from pet_orders.core.auth.settings import auth_settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION_DELTA = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRATION_DELTA = timedelta(days=7)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

async def create_token_pair(user_id: uuid.UUID, access_id: uuid.UUID, refresh_id: uuid.UUID, family_id: uuid.UUID) -> tuple[str, str]:
    iat = datetime.now(UTC)
    access_token = jwt.encode({'sub': str(user_id), 'typ': 'access', 'exp': datetime.now() + ACCESS_TOKEN_EXPIRATION_DELTA, 'iat': iat, 'jti': str(access_id)}, auth_settings.SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode({'sub': str(user_id), 'typ': 'refresh', 'exp': datetime.now() + REFRESH_TOKEN_EXPIRATION_DELTA, 'iat': iat, 'jti': str(refresh_id)}, auth_settings.SECRET_KEY, algorithm=ALGORITHM)
    return access_token, refresh_token