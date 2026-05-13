from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from models import CandleRecord, NormalizedMarketEvent, TickRecord

from shared.events import (
    MarketCandleEvent,
    MarketCandlePayload,
    MarketTickEvent,
    MarketTickPayload,
)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _epoch_to_dt(value: Any) -> datetime:
    if value is None:
        return datetime.now(UTC)
    return datetime.fromtimestamp(float(value), tz=UTC)


def normalize_deriv_tick(message: dict[str, Any], source: str = "deriv") -> NormalizedMarketEvent:
    tick = message["tick"]
    symbol = str(tick.get("symbol") or message.get("echo_req", {}).get("ticks") or "UNKNOWN")
    exchange_timestamp = _epoch_to_dt(tick.get("epoch"))
    bid = _as_float(tick.get("bid"))
    ask = _as_float(tick.get("ask"))
    last = _as_float(tick.get("quote"))
    volume = _as_float(tick.get("volume"))

    payload = MarketTickPayload(
        symbol=symbol,
        bid=bid,
        ask=ask,
        last=last,
        volume=volume,
        exchange_timestamp=exchange_timestamp,
    )
    event = MarketTickEvent(source=source, payload=payload)
    record = TickRecord(
        symbol=symbol,
        bid=bid,
        ask=ask,
        last=last,
        volume=volume,
        exchange_timestamp=exchange_timestamp,
        source=source,
    )
    return NormalizedMarketEvent(event=event, tick_record=record)


def normalize_deriv_candle(
    ohlc: dict[str, Any], *, source: str = "deriv", default_timeframe: str = "60s"
) -> NormalizedMarketEvent:
    symbol = str(ohlc.get("symbol") or "UNKNOWN")
    granularity = int(ohlc.get("granularity") or 60)
    timeframe = f"{granularity}s" if granularity > 0 else default_timeframe

    open_value = float(ohlc["open"])
    high = float(ohlc["high"])
    low = float(ohlc["low"])
    close = float(ohlc["close"])
    volume = float(ohlc.get("volume") or 0)

    candle_start = _epoch_to_dt(ohlc.get("open_time") or ohlc.get("epoch"))
    candle_end = candle_start + timedelta(seconds=max(granularity, 1))

    payload = MarketCandlePayload(
        symbol=symbol,
        timeframe=timeframe,
        open=open_value,
        high=high,
        low=low,
        close=close,
        volume=volume,
        candle_start=candle_start,
        candle_end=candle_end,
    )
    event = MarketCandleEvent(source=source, payload=payload)
    record = CandleRecord(
        symbol=symbol,
        timeframe=timeframe,
        open=open_value,
        high=high,
        low=low,
        close=close,
        volume=volume,
        candle_start=candle_start,
        candle_end=candle_end,
        source=source,
    )
    return NormalizedMarketEvent(event=event, candle_record=record)
