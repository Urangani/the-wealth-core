from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .base import BaseEvent


class SignalGeneratedPayload(BaseModel):
    signal_id: str
    strategy_id: str
    symbol: str
    side: Literal["buy", "sell", "hold"]
    strength: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    generated_at: datetime
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class SignalGeneratedEvent(BaseEvent):
    event_type: Literal["signal.generated"] = "signal.generated"
    payload: SignalGeneratedPayload
