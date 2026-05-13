from typing import Literal

from pydantic import BaseModel, Field

from .base import BaseEvent


class SystemHealthPayload(BaseModel):
    service: str
    status: Literal["healthy", "degraded", "unhealthy"]
    latency_ms: float = Field(ge=0)
    uptime: float = Field(ge=0)


class SystemHealthEvent(BaseEvent):
    event_type: Literal["system.health"] = "system.health"
    payload: SystemHealthPayload
