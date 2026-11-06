from contextlib import asynccontextmanager

from fastapi import FastAPI

import pet_orders.models  # noqa: F401
from pet_orders.auth.routers import router as auth_router
from pet_orders.core.queue.queue import connect
from pet_orders.core.redis.client import redis
from pet_orders.orders.routers import router as orders_router
from pet_orders.organizations.routers import router as organizations_router
from pet_orders.settings import Environment, settings
from pet_orders.users.routers import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.environment is Environment.test:
        yield
        return

    async with connect() as connection:
        app.state.broker = await connection.channel()
        try:
            yield
        finally:
            await redis.aclose()


app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(organizations_router)
app.include_router(orders_router)


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
