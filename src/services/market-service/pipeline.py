from __future__ import annotations

import asyncio
import logging
from typing import Any

from config import MarketServiceSettings
from deriv_connector import DerivWebSocketConnector
from fallback_provider import FallbackMarketProvider
from models import NormalizedMarketEvent, ProviderStatus, StreamCandle, StreamTick
from normalization import normalize_deriv_candle, normalize_deriv_tick
from timescale_writer import BatchBuffer, TimescaleWriter, periodic_flush

from shared.nats_client import NatsClient

LOGGER = logging.getLogger(__name__)


class MarketPipeline:
    def __init__(self, *, settings: MarketServiceSettings, nats_client: NatsClient):
        self.settings = settings
        self.nats = nats_client
        self.stream_queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=settings.stream_queue_size)
        self.stop_event = asyncio.Event()

        self.deriv = DerivWebSocketConnector(settings)
        self.fallback = FallbackMarketProvider(settings)
        self.writer = TimescaleWriter(settings)
        self.buffer = BatchBuffer()

        self._consumer_task: asyncio.Task[None] | None = None
        self._flush_task: asyncio.Task[None] | None = None
        self._primary_task: asyncio.Task[None] | None = None
        self._fallback_task: asyncio.Task[None] | None = None

        self.provider_mode = "starting"
        self.last_error = ""
        self.processed_ticks = 0
        self.processed_candles = 0

    async def start(self) -> None:
        await self.writer.connect()
        self._consumer_task = asyncio.create_task(self._consume(), name="market-consumer")
        self._flush_task = asyncio.create_task(
            periodic_flush(
                self.writer,
                self.buffer,
                stop_event=self.stop_event,
                interval_seconds=self.settings.batch_flush_interval_seconds,
            ),
            name="market-db-flush",
        )
        self._primary_task = asyncio.create_task(
            self.deriv.stream(self.stream_queue, self.stop_event),
            name="deriv-stream",
        )

    async def stop(self) -> None:
        self.stop_event.set()
        tasks = [
            task
            for task in [
                self._primary_task,
                self._fallback_task,
                self._consumer_task,
                self._flush_task,
            ]
            if task is not None
        ]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await self._flush_remaining()
        await self.writer.close()

    async def _consume(self) -> None:
        while not self.stop_event.is_set():
            item = await self.stream_queue.get()
            try:
                if isinstance(item, ProviderStatus):
                    await self._handle_provider_status(item)
                    continue
                if isinstance(item, StreamTick):
                    normalized = normalize_deriv_tick(item.data or {}, source=item.source)
                    await self._handle_event(normalized)
                    self.processed_ticks += 1
                    continue
                if isinstance(item, StreamCandle):
                    normalized = normalize_deriv_candle(item.data or {}, source=item.source)
                    await self._handle_event(normalized)
                    self.processed_candles += 1
                    continue
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                LOGGER.exception("Market pipeline consume error: %s", exc)
                self.last_error = str(exc)
            finally:
                self.stream_queue.task_done()

    async def _handle_provider_status(self, status: ProviderStatus) -> None:
        if status.provider == "deriv" and status.status == "connected":
            self.provider_mode = "primary"
            self.last_error = ""
            if self._fallback_task:
                self._fallback_task.cancel()
                await asyncio.gather(self._fallback_task, return_exceptions=True)
                self._fallback_task = None
            return

        if status.provider == "deriv" and status.status in {"disconnected", "error"}:
            self.provider_mode = "degraded"
            self.last_error = status.detail
            if self.settings.fallback_enabled and not self._fallback_task:
                self._fallback_task = asyncio.create_task(
                    self.fallback.run(self.stream_queue, self.stop_event),
                    name="fallback-stream",
                )
            return

        if status.provider == "fallback":
            self.provider_mode = "fallback"

    async def _handle_event(self, normalized: NormalizedMarketEvent) -> None:
        await self.nats.publish_event(normalized.event)
        if normalized.tick_record is not None:
            self.buffer.add_tick(normalized.tick_record)
        if normalized.candle_record is not None:
            self.buffer.add_candle(normalized.candle_record)

        if (
            len(self.buffer.ticks) >= self.settings.batch_flush_size
            or len(self.buffer.candles) >= self.settings.batch_flush_size
        ):
            await self._flush_buffer()

    async def _flush_buffer(self) -> None:
        if not self.buffer.has_data:
            return
        ticks = list(self.buffer.ticks)
        candles = list(self.buffer.candles)
        self.buffer.clear()
        await self.writer.write_ticks(ticks)
        await self.writer.write_candles(candles)

    async def _flush_remaining(self) -> None:
        try:
            await self._flush_buffer()
        except Exception as exc:
            LOGGER.exception("Failed to flush market buffers on shutdown: %s", exc)
            self.last_error = str(exc)
