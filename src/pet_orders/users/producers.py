from uuid import UUID

from aio_pika.abc import AbstractChannel

from pet_orders.core.queue.queue import publish
from pet_orders.users.schemas import UserCreatedEvent

USER_CREATED_QUEUE = "user_created"


async def send_user_created_event(channel: AbstractChannel, email: str, user_id: UUID) -> None:
    event = UserCreatedEvent(email=email, user_id=user_id)
    await publish(channel, USER_CREATED_QUEUE, event.model_dump_json().encode())
