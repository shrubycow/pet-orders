from aio_pika.abc import AbstractChannel, AbstractIncomingMessage

from pet_orders.users.producers import USER_CREATED_QUEUE
from pet_orders.users.schemas import UserCreatedEvent
from pet_orders.users.service import send_user_created_email


async def consume_user_created(channel: AbstractChannel) -> None:
    await channel.set_qos(prefetch_count=10)
    queue = await channel.declare_queue(USER_CREATED_QUEUE, durable=True)

    async def on_message(message: AbstractIncomingMessage) -> None:
        async with message.process():
            event = UserCreatedEvent.model_validate_json(message.body)
            await send_user_created_email(event.user_id, event.email)

    await queue.consume(on_message)
