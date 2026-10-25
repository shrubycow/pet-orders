from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from pet_orders.core.redis.client import redis


def get_redis() -> Redis:
    return redis


RedisDep = Annotated[Redis, Depends(get_redis)]
