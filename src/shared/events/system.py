from typing import Literal

from .base import BaseEvent


class SystemHealthEvent(BaseEvent):
    event_type: Literal["system.health.v1"] = "system.health.v1"
    event_version: str = "v1"
    payload: dict
