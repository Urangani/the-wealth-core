from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence

import asyncpg

from config import MarketServiceSettings
from models import CandleRecord, TickRecord


class TimescaleWriter:
    def __init__(self, settings: MarketServiceSettings):
        self.settings = settings
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self.pool:
            return
        self.pool = await asyncpg.create_pool(self.settings.timescale_url, min_size=1, max_size=5)
        await self._apply_retention_policies()

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def write_ticks(self, ticks: Sequence[TickRecord]) -> None:
        if not ticks:
            return
        if not self.pool:
            raise RuntimeError("Timescale pool is not connected")
        query = """
            INSERT INTO ticks (time, symbol, bid, ask, last, volume, source)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (time, symbol, source) DO NOTHING
        """
        async with self.pool.acquire() as conn:
            await conn.executemany(
                query,
                [
                    (
                        tick.exchange_timestamp,
                        tick.symbol,
                        tick.bid,
                        tick.ask,
                        tick.last,
                        tick.volume,
                        tick.source,
                    )
                    for tick in ticks
                ],
            )

    async def write_candles(self, candles: Sequence[CandleRecord]) -> None:
        if not candles:
            return
        if not self.pool:
            raise RuntimeError("Timescale pool is not connected")
        query = """
            INSERT INTO candles (time, symbol, timeframe, open, high, low, close, volume, source)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (time, symbol, timeframe, source)
            DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
        """
        async with self.pool.acquire() as conn:
            await conn.executemany(
                query,
                [
                    (
                        candle.candle_start,
                        candle.symbol,
                        candle.timeframe,
                        candle.open,
                        candle.high,
                        candle.low,
                        candle.close,
                        candle.volume,
                        candle.source,
                    )
                    for candle in candles
                ],
            )

    async def insert_raw_event(self, event_json: str) -> None:
        if not self.pool:
            return
        query = """
            INSERT INTO features (time, symbol, feature_set, values, source)
            VALUES (NOW(), 'market-service', 'raw_event', $1::jsonb, 'market-service')
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, json.dumps({"event": event_json}))

    async def _apply_retention_policies(self) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                SELECT add_retention_policy(
                    'ticks',
                    make_interval(days => $1::int),
                    if_not_exists => TRUE
                )
                """,
                self.settings.tick_retention_days,
            )
            await conn.execute(
                """
                SELECT add_retention_policy(
                    'candles',
                    make_interval(days => $1::int),
                    if_not_exists => TRUE
                )
                """,
                self.settings.candle_retention_days,
            )


class BatchBuffer:
    def __init__(self) -> None:
        self.ticks: list[TickRecord] = []
        self.candles: list[CandleRecord] = []

    def add_tick(self, tick: TickRecord) -> None:
        self.ticks.append(tick)

    def add_candle(self, candle: CandleRecord) -> None:
        self.candles.append(candle)

    def clear(self) -> None:
        self.ticks.clear()
        self.candles.clear()

    @property
    def has_data(self) -> bool:
        return bool(self.ticks or self.candles)


async def periodic_flush(
    writer: TimescaleWriter,
    buffer: BatchBuffer,
    *,
    stop_event: asyncio.Event,
    interval_seconds: float,
) -> None:
    while not stop_event.is_set():
        await asyncio.sleep(interval_seconds)
        if not buffer.has_data:
            continue
        ticks = list(buffer.ticks)
        candles = list(buffer.candles)
        buffer.clear()
        await writer.write_ticks(ticks)
        await writer.write_candles(candles)
