from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .base import BaseEvent


class PositionOpenedPayload(BaseModel):
    position_id: str
    strategy_id: str
    symbol: str
    side: Literal["long", "short"]
    quantity: float = Field(gt=0)
    average_price: float = Field(gt=0)
    opened_at: datetime


class PositionClosedPayload(BaseModel):
    position_id: str
    symbol: str
    quantity: float = Field(gt=0)
    average_exit_price: float = Field(gt=0)
    realized_pnl: float
    closed_at: datetime


class PositionOpenedEvent(BaseEvent):
    event_type: Literal["position.opened"] = "position.opened"
    payload: PositionOpenedPayload


class PositionClosedEvent(BaseEvent):
    event_type: Literal["position.closed"] = "position.closed"
    payload: PositionClosedPayload
