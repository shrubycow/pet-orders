from typing import Annotated, Any

from fastapi import Depends, Request, status

from pet_orders.core.errors import raise_api_error
from pet_orders.core.redis.client import redis


async def get_ip_address(request: Request) -> str:
    if request.client is None:
        return 'unknown'
    return request.client.host


IpAddress = Annotated[str, Depends(get_ip_address)]


def rate_limit(window_seconds: int, subject: Any) -> Any:
    async def dependency(request: Request, value: subject) -> None:
        route = request.scope['route']
        key = f'rate:{request.method}:{route.path}:{value}'
        allowed = await redis.set(key, '1', nx=True, ex=window_seconds)
        if not allowed:
            raise_api_error(status.HTTP_429_TOO_MANY_REQUESTS, 'Too many requests')

    return Depends(dependency)
