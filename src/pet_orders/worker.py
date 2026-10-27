import asyncio
import signal

from pet_orders.core.queue.queue import connect
from pet_orders.core.redis.client import redis
from pet_orders.users.consumers import consume_user_created


async def run() -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass

    try:
        async with connect() as connection:
            channel = await connection.channel()
            await consume_user_created(channel)
            print('worker started')
            await stop.wait()
    finally:
        await redis.aclose()


def main() -> None:
    asyncio.run(run())


if __name__ == '__main__':
    main()
