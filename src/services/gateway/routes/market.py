from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from services.gateway.envelope import ok
from services.gateway.providers.base import MarketDataProvider

router = APIRouter(tags=["market"])


def _get_market_provider(request: Request) -> MarketDataProvider:
    return request.app.state.market_provider


@router.get("/market/candles")
async def market_candles(
    symbol: str = Query(...),
    timeframe: str = Query(default="M5"),
    count: int = Query(default=80, ge=1, le=5000),
    provider: MarketDataProvider = Depends(_get_market_provider),
) -> dict[str, Any]:
    data = await provider.get_candles(symbol, timeframe, count)
    return ok(data)


@router.get("/market/ticks")
async def market_ticks(
    symbol: str = Query(...),
    limit: int = Query(default=100, ge=1, le=5000),
    provider: MarketDataProvider = Depends(_get_market_provider),
) -> dict[str, Any]:
    data = await provider.get_ticks(symbol, limit)
    return ok(data)


@router.get("/symbols")
async def symbols(
    provider: MarketDataProvider = Depends(_get_market_provider),
) -> dict[str, Any]:
    data = await provider.get_symbols()
    return ok(data)
