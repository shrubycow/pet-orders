from uuid import UUID

from aio_pika.abc import AbstractChannel
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.core.auth.auth import authorize_user
from pet_orders.core.auth.password import generate_auth_code, hash_password
from pet_orders.core.auth.schemas import TokenPair
from pet_orders.core.email import send_email
from pet_orders.core.redis.client import redis
from pet_orders.users.models import User
from pet_orders.users.producers import send_user_created_event
from pet_orders.users.settings import users_settings


async def create_user(
    db_session: AsyncSession,
    channel: AbstractChannel,
    email: str,
    password: str,
) -> User:
    user = User(email=email, password=await hash_password(password))
    db_session.add(user)
    await db_session.commit()
    await send_user_created_event(channel, user.email, user.id)
    return user

async def register_user(
    db_session: AsyncSession,
    channel: AbstractChannel,
    email: str,
    password: str,
) -> TokenPair:
    user = await create_user(db_session, channel, email, password)
    access_token, refresh_token = await authorize_user(user.id)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)

async def send_user_created_email(user_id: UUID, email: str) -> None:
    code = generate_auth_code()
    await redis.set(f"user_created:{user_id}", code, ex=users_settings.user_created_code_ttl)
    await send_email(email, "Welcome to Pet Orders", f"Here is your code: {code}")
