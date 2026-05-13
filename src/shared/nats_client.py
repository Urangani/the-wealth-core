from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlparse

from nats.aio.client import Client as NatsConnection

from shared.events import BaseEvent

MessageCallback = Callable[[Any], Awaitable[None]]


class OrderPublishPermissionError(PermissionError):
    pass


class NatsClient:
    def __init__(self, url: str = "nats://localhost:4222", service_name: str = "unknown"):
        self.nc = NatsConnection()
        self.url = url
        self.service_name = service_name

    @property
    def is_connected(self) -> bool:
        return self.nc.is_connected

    async def connect(self) -> None:
        if not self.nc.is_connected:
            parsed = urlparse(self.url)
            kwargs: dict[str, Any] = {"servers": [self.url], "name": self.service_name}
            if parsed.username:
                kwargs["user"] = parsed.username
            if parsed.password:
                kwargs["password"] = parsed.password
            await self.nc.connect(**kwargs)

    async def close(self) -> None:
        if self.nc.is_connected:
            await self.nc.drain()

    async def publish(self, subject: str, data: bytes) -> None:
        self._assert_can_publish(subject)
        await self.nc.publish(subject, data)

    async def publish_event(self, event: BaseEvent) -> None:
        subject = event.subject
        self._assert_can_publish(subject)
        await self.nc.publish(subject, event.model_dump_json().encode("utf-8"))

    async def subscribe(self, subject: str, callback: MessageCallback) -> None:
        await self.nc.subscribe(subject, cb=callback)

    def _assert_can_publish(self, subject: str) -> None:
        tokens = subject.split(".")
        event_type = ".".join(tokens[1:]) if tokens and tokens[0].startswith("v") else subject
        if event_type.startswith("order.") and self.service_name != "execution-service":
            raise OrderPublishPermissionError('Only execution-service can publish "order.*" events')
