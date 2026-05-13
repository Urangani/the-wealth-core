from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    event_version: str = "v1"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str
    correlation_id: str | None = None
    payload: Any

    @property
    def subject(self) -> str:
        return f"{self.event_version}.{self.event_type}"
