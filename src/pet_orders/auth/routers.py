from fastapi import APIRouter, status

from pet_orders.auth.dependencies import (
    INVALID_REFRESH_TOKEN,
    REFRESH_TOKEN_EXPIRED,
    RefreshTokenDependency,
)
from pet_orders.auth.service import rotate_token_pair
from pet_orders.core.auth.schemas import TokenPair

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)

@router.post(
    '/refresh',
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            'description': 'Refresh token is expired or invalid',
            'content': {
                'application/json': {
                    'examples': {
                        'expired': {
                            'summary': REFRESH_TOKEN_EXPIRED,
                            'value': {'detail': REFRESH_TOKEN_EXPIRED},
                        },
                        'invalid': {
                            'summary': INVALID_REFRESH_TOKEN,
                            'value': {'detail': INVALID_REFRESH_TOKEN},
                        },
                    },
                },
            },
        },
    },
)
async def refresh_token(
    refresh_token_data: RefreshTokenDependency,
) -> TokenPair:
    return await rotate_token_pair(refresh_token_data)
