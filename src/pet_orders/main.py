from contextlib import asynccontextmanager

from fastapi import FastAPI

from pet_orders.core.queue.queue import connect
from pet_orders.core.redis.client import redis
from pet_orders.users.routers import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with connect() as connection:
        app.state.broker = await connection.channel()
        try:
            yield
        finally:
            await redis.aclose()


app = FastAPI(lifespan=lifespan)
app.include_router(users_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
