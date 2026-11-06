from typing import Annotated, cast

from aio_pika.abc import AbstractChannel
from fastapi import Depends, Request


def get_broker(request: Request) -> AbstractChannel:
    return cast(AbstractChannel, request.app.state.broker)


BrokerDep = Annotated[AbstractChannel, Depends(get_broker)]
