from datetime import timedelta
from uuid import uuid4

import jwt

from pet_orders.core.auth.auth import ALGORITHM
from pet_orders.core.auth.consts import TokenType
from pet_orders.core.auth.settings import auth_settings
from pet_orders.core.utils import now


def bearer(access_token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {access_token}'}


def expired_token(token_type: TokenType, **claims: str) -> str:
    issued_at = now() - timedelta(hours=1)
    return jwt.encode(
        {
            'sub': str(uuid4()),
            'typ': token_type,
            'exp': issued_at + timedelta(minutes=1),
            'iat': issued_at,
            'jti': str(uuid4()),
            **claims,
        },
        auth_settings.secret_key,
        algorithm=ALGORITHM,
    )
