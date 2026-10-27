from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pet_orders.core.db.db import session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as db_session:
        yield db_session


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
