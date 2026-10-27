from pet_orders.core.auth.auth import rotate_refresh_token
from pet_orders.core.auth.schemas import RotateRefreshTokenData, TokenPair


async def rotate_token_pair(refresh_token_data: RotateRefreshTokenData) -> TokenPair:
    access_token, refresh_token = await rotate_refresh_token(refresh_token_data.refresh_token.sub, refresh_token_data.refresh_token.family, refresh_token_data.session_data.family_exat)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)
