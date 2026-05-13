from __future__ import annotations

import asyncio
import random
from datetime import UTC, datetime, timedelta
from typing import Any

from config import MarketServiceSettings
from models import ProviderStatus, StreamCandle, StreamTick


class FallbackMarketProvider:
    def __init__(self, settings: MarketServiceSettings):
        self.settings = settings
        self._prices: dict[str, float] = {symbol: self._seed_price(symbol) for symbol in settings.fallback_symbols}

    async def run(self, out_queue: asyncio.Queue[Any], stop_event: asyncio.Event) -> None:
        await out_queue.put(
            ProviderStatus(
                provider="fallback",
                status="fallback",
                detail="fallback-provider-active",
            )
        )
        while not stop_event.is_set():
            try:
                now = datetime.now(UTC)
                for symbol in self.settings.fallback_symbols:
                    last = self._next_price(symbol)
                    bid = max(last - 0.0001, 0.0001)
                    ask = last + 0.0001
                    tick_payload = {
                        "tick": {
                            "symbol": symbol,
                            "quote": last,
                            "bid": bid,
                            "ask": ask,
                            "epoch": now.timestamp(),
                            "volume": random.uniform(1, 1000),
                        }
                    }
                    await out_queue.put(StreamTick(data=tick_payload, source="fallback"))

                    granularity = max(self.settings.candle_granularities[0], 1)
                    candle_payload = {
                        "symbol": symbol,
                        "open": last,
                        "high": last + random.uniform(0, 0.0005),
                        "low": max(last - random.uniform(0, 0.0005), 0.0001),
                        "close": last + random.uniform(-0.0003, 0.0003),
                        "volume": random.uniform(1, 1000),
                        "open_time": (now - timedelta(seconds=granularity)).timestamp(),
                        "epoch": now.timestamp(),
                        "granularity": granularity,
                    }
                    await out_queue.put(StreamCandle(data=candle_payload, source="fallback"))

                await asyncio.sleep(self.settings.fallback_interval_seconds)
            except asyncio.CancelledError:
                return

    def _seed_price(self, symbol: str) -> float:
        if symbol.startswith("frx"):
            return random.uniform(1.0, 1.5)
        if symbol.startswith("R_"):
            return random.uniform(100, 1000)
        return random.uniform(10, 100)

    def _next_price(self, symbol: str) -> float:
        drift = random.uniform(-0.0008, 0.0008)
        previous = self._prices[symbol]
        next_price = max(previous + drift, 0.0001)
        self._prices[symbol] = next_price
        return next_price
