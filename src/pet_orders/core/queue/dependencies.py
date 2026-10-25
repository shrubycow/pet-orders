from typing import Annotated

from aio_pika.abc import AbstractChannel
from fastapi import Depends, Request


def get_broker(request: Request) -> AbstractChannel:
    return request.app.state.broker


BrokerDep = Annotated[AbstractChannel, Depends(get_broker)]
