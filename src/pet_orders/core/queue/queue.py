from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aio_pika
from aio_pika import DeliveryMode, Message
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

from pet_orders.settings import settings


@asynccontextmanager
async def connect() -> AsyncIterator[AbstractRobustConnection]:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        yield connection
    finally:
        await connection.close()


async def publish(
    channel: AbstractChannel,
    queue_name: str,
    body: bytes,
    *,
    durable: bool = True,
    persistent: bool = True,
) -> None:
    delivery_mode = DeliveryMode.PERSISTENT if persistent else DeliveryMode.NOT_PERSISTENT
    queue = await channel.declare_queue(queue_name, durable=durable)
    await channel.default_exchange.publish(
        Message(body, delivery_mode=delivery_mode),
        routing_key=queue.name,
    )
