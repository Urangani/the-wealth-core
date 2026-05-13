from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient

SERVICE_UPSTREAMS = {
    "market-service": os.getenv("MARKET_SERVICE_URL", "http://market-service:8000"),
    "execution-service": os.getenv("EXECUTION_SERVICE_URL", "http://execution-service:8000"),
    "strategy-service": os.getenv("STRATEGY_SERVICE_URL", "http://strategy-service:8000"),
    "analytics-service": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000"),
}

TIMESCALE_URL = os.getenv("TIMESCALE_URL", "postgresql://thewealth:thewealth@timescaledb:5432/market")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
LOGGER = logging.getLogger("gateway")


def create_gateway_app() -> FastAPI:
    started_at = time.monotonic()
    pool: asyncpg.Pool | None = None
    http = AsyncClient(timeout=5)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal pool
        try:
            pool = await asyncpg.create_pool(TIMESCALE_URL, min_size=1, max_size=5, timeout=10)
        except Exception:
            LOGGER.exception("Failed to connect to TimescaleDB")
            pool = None
        yield
        if pool:
            await pool.close()
        await http.aclose()

    app = FastAPI(title="gateway-service", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, Any]:
        db_ok = pool is not None and not pool._closed
        return {
            "service": "gateway-service",
            "status": "healthy" if db_ok else "degraded",
            "timescaledb_connected": db_ok,
            "uptime": round(time.monotonic() - started_at, 3),
        }

    @app.get("/ready")
    async def ready() -> dict[str, bool | str]:
        return {
            "service": "gateway-service",
            "ready": pool is not None and not pool._closed,
        }

    @app.get(f"{API_PREFIX}/market/status")
    async def market_status() -> dict[str, Any]:
        url = f"{SERVICE_UPSTREAMS['market-service']}/market/status"
        try:
            resp = await http.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            return {"error": f"market-service unreachable: {exc}"}

    @app.get(f"{API_PREFIX}/market/ticks")
    async def get_ticks(
        symbol: str = Query(...),
        limit: int = Query(default=100, ge=1, le=5000),
        since: str | None = Query(default=None),
    ) -> list[dict[str, Any]]:
        if pool is None:
            return []
        query = """
            SELECT time, symbol, bid, ask, last, volume, source
            FROM ticks
            WHERE symbol = $1
            AND ($2::timestamptz IS NULL OR time >= $2::timestamptz)
            ORDER BY time DESC
            LIMIT $3
        """
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, symbol, since, limit)
        return [
            {
                "time": r["time"].isoformat(),
                "symbol": r["symbol"],
                "bid": float(r["bid"]) if r["bid"] else None,
                "ask": float(r["ask"]) if r["ask"] else None,
                "last": float(r["last"]) if r["last"] else None,
                "volume": float(r["volume"]) if r["volume"] else None,
                "source": r["source"],
            }
            for r in rows
        ]

    @app.get(f"{API_PREFIX}/market/candles")
    async def get_candles(
        symbol: str = Query(...),
        timeframe: str = Query(default="60s"),
        limit: int = Query(default=100, ge=1, le=5000),
        since: str | None = Query(default=None),
    ) -> list[dict[str, Any]]:
        if pool is None:
            return []
        query = """
            SELECT time, symbol, timeframe, open, high, low, close, volume, source
            FROM candles
            WHERE symbol = $1 AND timeframe = $2
            AND ($3::timestamptz IS NULL OR time >= $3::timestamptz)
            ORDER BY time DESC
            LIMIT $4
        """
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, symbol, timeframe, since, limit)
        return [
            {
                "time": r["time"].isoformat(),
                "symbol": r["symbol"],
                "timeframe": r["timeframe"],
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r["volume"]),
                "source": r["source"],
            }
            for r in rows
        ]

    @app.get(f"{API_PREFIX}/system/health")
    async def system_health() -> dict[str, Any]:
        results: dict[str, Any] = {}
        all_healthy = True
        for name, upstream in SERVICE_UPSTREAMS.items():
            try:
                resp = await http.get(f"{upstream}/health", timeout=3)
                data = resp.json() if resp.status_code == 200 else {"status": "unhealthy"}
                results[name] = data
                if data.get("status") != "healthy":
                    all_healthy = False
            except Exception:
                results[name] = {"status": "unreachable"}
                all_healthy = False
        return {"status": "healthy" if all_healthy else "degraded", "services": results}

    return app


app = create_gateway_app()
