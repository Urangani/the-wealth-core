from __future__ import annotations

import os
from typing import Any

import asyncpg

from .base import MarketDataProvider

TIMEFRAME_MAP: dict[str, str] = {
    "M1": "60s",
    "M5": "300s",
    "M15": "900s",
    "M30": "1800s",
    "H1": "3600s",
    "H4": "14400s",
    "D1": "86400s",
}

DEFAULT_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
    "R_100", "R_50", "volatility_10", "volatility_25",
]

TIMESCALE_URL = os.getenv("TIMESCALE_URL", "postgresql://thewealth:thewealth@timescaledb:5432/market")


class TimescaleMarketDataProvider(MarketDataProvider):
    def __init__(self, pool: asyncpg.Pool | None = None) -> None:
        self._pool = pool

    def set_pool(self, pool: asyncpg.Pool | None) -> None:
        self._pool = pool

    async def get_candles(
        self, symbol: str, timeframe: str, count: int
    ) -> list[dict[str, Any]]:
        if self._pool is None:
            return []
        tf = TIMEFRAME_MAP.get(timeframe.upper(), timeframe)
        query = """
            SELECT time, symbol, timeframe, open, high, low, close, volume, source
            FROM candles
            WHERE symbol = $1 AND timeframe = $2
            ORDER BY time DESC
            LIMIT $3
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, symbol.upper(), tf, count)
        return [
            {
                "time": int(r["time"].timestamp()),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r["volume"]),
            }
            for r in rows
        ]

    async def get_ticks(
        self, symbol: str, limit: int
    ) -> list[dict[str, Any]]:
        if self._pool is None:
            return []
        query = """
            SELECT time, symbol, bid, ask, last, volume, source
            FROM ticks
            WHERE symbol = $1
            ORDER BY time DESC
            LIMIT $2
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, symbol.upper(), limit)
        return [
            {
                "time": r["time"].isoformat(),
                "symbol": r["symbol"],
                "bid": float(r["bid"]) if r["bid"] else None,
                "ask": float(r["ask"]) if r["ask"] else None,
                "last": float(r["last"]) if r["last"] else None,
                "volume": float(r["volume"]) if r["volume"] else None,
            }
            for r in rows
        ]

    async def get_symbols(self) -> list[str]:
        if self._pool is None:
            return DEFAULT_SYMBOLS
        try:
            query = "SELECT DISTINCT symbol FROM candles ORDER BY symbol"
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query)
            if rows:
                return [r["symbol"] for r in rows]
        except Exception:
            pass
        return DEFAULT_SYMBOLS
