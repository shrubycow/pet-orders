from pet_orders.core.auth.schemas import TokenPair
from pet_orders.users.models import UserStatus


class LoginUserResponse(TokenPair):
    status: UserStatus
