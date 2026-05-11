from collections.abc import Awaitable, Callable
from typing import Any

from nats.aio.client import Client as NATS

from shared.events import BaseEvent


MessageCallback = Callable[[Any], Awaitable[None]]


class OrderPublishPermissionError(PermissionError):
    pass


class NatsClient:
    def __init__(self, url: str = "nats://localhost:4222", service_name: str = "unknown"):
        self.nc = NATS()
        self.url = url
        self.service_name = service_name

    @property
    def is_connected(self) -> bool:
        return self.nc.is_connected

    async def connect(self) -> None:
        if not self.nc.is_connected:
            await self.nc.connect(servers=[self.url], name=self.service_name)

    async def close(self) -> None:
        if self.nc.is_connected:
            await self.nc.drain()

    async def publish(self, subject: str, data: bytes) -> None:
        self._assert_can_publish(subject)
        await self.nc.publish(subject, data)

    async def publish_event(self, event: BaseEvent) -> None:
        subject = event.event_type
        self._assert_can_publish(subject)
        await self.nc.publish(subject, event.model_dump_json().encode("utf-8"))

    async def subscribe(self, subject: str, callback: MessageCallback) -> None:
        await self.nc.subscribe(subject, cb=callback)

    def _assert_can_publish(self, subject: str) -> None:
        if subject.startswith("order.") and self.service_name != "execution-service":
            raise OrderPublishPermissionError(
                'Only execution-service can publish "order.*" events'
            )
