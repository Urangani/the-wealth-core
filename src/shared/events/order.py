from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .base import BaseEvent


class OrderSubmittedPayload(BaseModel):
    order_id: str
    strategy_id: str
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    quantity: float = Field(gt=0)
    limit_price: float | None = Field(default=None, gt=0)
    stop_price: float | None = Field(default=None, gt=0)
    submitted_at: datetime


class OrderFilledPayload(BaseModel):
    order_id: str
    fill_id: str
    symbol: str
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    commission: float = Field(default=0, ge=0)
    filled_at: datetime


class OrderSubmittedEvent(BaseEvent):
    event_type: Literal["order.submitted"] = "order.submitted"
    payload: OrderSubmittedPayload


class OrderFilledEvent(BaseEvent):
    event_type: Literal["order.filled"] = "order.filled"
    payload: OrderFilledPayload
