from typing import Protocol


class _Body(Protocol):
    body: bytes


class _Queue:
    def __init__(self, name: str) -> None:
        self.name = name


class _Exchange:
    def __init__(self, published: list[tuple[str, bytes]]) -> None:
        self._published = published

    async def publish(self, message: _Body, routing_key: str) -> None:
        self._published.append((routing_key, message.body))


class FakeChannel:
    def __init__(self) -> None:
        self.published: list[tuple[str, bytes]] = []
        self.default_exchange = _Exchange(self.published)

    async def declare_queue(self, name: str, *, durable: bool = True) -> _Queue:
        return _Queue(name)
