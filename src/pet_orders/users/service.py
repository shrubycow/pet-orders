from uuid import UUID

from aio_pika.abc import AbstractChannel
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.core.auth import generate_auth_code, hash_password
from pet_orders.core.email import send_email
from pet_orders.core.redis.client import redis
from pet_orders.users.models import User
from pet_orders.users.producers import send_user_created_event
from pet_orders.users.settings import users_settings


async def create_user(
    session: AsyncSession,
    channel: AbstractChannel,
    email: str,
    password: str,
) -> User:
    user = User(email=email, password=await hash_password(password))
    session.add(user)
    await session.commit()
    await send_user_created_event(channel, user.email, user.id)
    return user


async def send_user_created_email(user_id: UUID, email: str) -> None:
    code = generate_auth_code()
    await redis.set(f"user_created:{user_id}", code, ex=users_settings.user_created_code_ttl)
    await send_email(email, "Welcome to Pet Orders", f"Here is your code: {code}")
