from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from shared.events import MarketCandleEvent, MarketTickEvent


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True, frozen=True)
class TickRecord:
    symbol: str
    bid: float | None
    ask: float | None
    last: float | None
    volume: float | None
    exchange_timestamp: datetime
    source: str


@dataclass(slots=True, frozen=True)
class CandleRecord:
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    candle_start: datetime
    candle_end: datetime
    source: str


@dataclass(slots=True, frozen=True)
class StreamTick:
    kind: Literal["tick"] = "tick"
    data: dict[str, Any] | None = None
    source: str = "deriv"


@dataclass(slots=True, frozen=True)
class StreamCandle:
    kind: Literal["candle"] = "candle"
    data: dict[str, Any] | None = None
    source: str = "deriv"


@dataclass(slots=True, frozen=True)
class ProviderStatus:
    kind: Literal["provider_status"] = "provider_status"
    provider: str = "deriv"
    status: Literal["connected", "disconnected", "fallback", "primary", "error"] = "connected"
    detail: str = ""


@dataclass(slots=True, frozen=True)
class NormalizedMarketEvent:
    event: MarketTickEvent | MarketCandleEvent
    tick_record: TickRecord | None = None
    candle_record: CandleRecord | None = None
