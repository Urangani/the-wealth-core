from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .base import BaseEvent


class MarketTickPayload(BaseModel):
    symbol: str
    bid: float | None = Field(default=None, gt=0)
    ask: float | None = Field(default=None, gt=0)
    last: float | None = Field(default=None, gt=0)
    volume: float | None = Field(default=None, ge=0)
    exchange_timestamp: datetime

    @model_validator(mode="after")
    def require_price(self) -> "MarketTickPayload":
        if self.bid is None and self.ask is None and self.last is None:
            raise ValueError("market tick requires at least one of bid, ask, or last")
        return self


class MarketCandlePayload(BaseModel):
    symbol: str
    timeframe: str
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(default=0, ge=0)
    candle_start: datetime
    candle_end: datetime


class MarketTickEvent(BaseEvent):
    event_type: Literal["market.tick"] = "market.tick"
    payload: MarketTickPayload


class MarketCandleEvent(BaseEvent):
    event_type: Literal["market.candle"] = "market.candle"
    payload: MarketCandlePayload
