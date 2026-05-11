from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from config import MarketServiceSettings
from pipeline import MarketPipeline
from shared.events import SystemHealthEvent, SystemHealthPayload
from shared.nats_client import NatsClient
from shared.redis_client import RedisClient


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


def create_market_service_app() -> FastAPI:
    settings = MarketServiceSettings.from_env()
    started_at = time.monotonic()

    nats = NatsClient(
        url=os.getenv("NATS_URL", "nats://localhost:4222"),
        service_name="market-service",
    )
    redis = RedisClient(url=os.getenv("REDIS_URL", "redis://localhost:6379"))
    pipeline = MarketPipeline(settings=settings, nats_client=nats)

    state: dict[str, Any] = {
        "nats_connected": False,
        "redis_connected": False,
    }

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await nats.connect()
        state["nats_connected"] = True
        app.state.nats = nats

        await redis.connect()
        state["redis_connected"] = True
        app.state.redis = redis

        await pipeline.start()
        app.state.pipeline = pipeline

        await nats.publish_event(
            SystemHealthEvent(
                source="market-service",
                payload=SystemHealthPayload(
                    service="market-service",
                    status="healthy",
                    latency_ms=0,
                    uptime=0,
                ),
            )
        )

        try:
            yield
        finally:
            await pipeline.stop()
            await nats.close()
            await redis.close()

    app = FastAPI(title="market-service", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, Any]:
        service_status = "healthy"
        if not nats.is_connected or not redis.is_connected:
            service_status = "degraded"
        if pipeline.provider_mode in {"degraded"}:
            service_status = "degraded"
        if pipeline.provider_mode == "fallback":
            service_status = "degraded"
        return {
            "service": "market-service",
            "status": service_status,
            "nats_connected": nats.is_connected,
            "redis_connected": redis.is_connected,
            "provider_mode": pipeline.provider_mode,
            "processed_ticks": pipeline.processed_ticks,
            "processed_candles": pipeline.processed_candles,
            "last_error": pipeline.last_error,
            "uptime": round(time.monotonic() - started_at, 3),
        }

    @app.get("/ready")
    def ready() -> dict[str, bool | str]:
        return {
            "service": "market-service",
            "ready": nats.is_connected and redis.is_connected,
        }

    @app.get("/market/status")
    def market_status() -> dict[str, Any]:
        return {
            "provider_mode": pipeline.provider_mode,
            "processed_ticks": pipeline.processed_ticks,
            "processed_candles": pipeline.processed_candles,
            "queue_size": pipeline.stream_queue.qsize(),
            "last_error": pipeline.last_error,
            "fallback_enabled": settings.fallback_enabled,
            "candle_granularities": settings.candle_granularities,
        }

    return app


app = create_market_service_app()
