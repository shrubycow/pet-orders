from typing import Annotated, Any

from fastapi import Depends, Request, status

from pet_orders.core.errors import raise_api_error
from pet_orders.core.redis.client import redis


async def get_ip_address(request: Request) -> str:
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        # TODO: change to more secure way
        return forwarded.split(',')[0].strip()
    return request.client.host

IpAddress = Annotated[str, Depends(get_ip_address)]

def limit_by_ip(window_seconds: int) -> Any:
    async def dependency(request: Request, ip: IpAddress) -> None:
        route = request.scope['route']
        key = f'rate:{request.method}:{route.path}:{ip}'
        allowed = await redis.set(key, '1', nx=True, ex=window_seconds)
        if not allowed:
            raise_api_error(status.HTTP_429_TOO_MANY_REQUESTS, 'Too many requests')

    return Depends(dependency)
