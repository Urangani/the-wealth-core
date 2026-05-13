from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from services.gateway.envelope import ok
from services.gateway.providers.base import TradeProvider

router = APIRouter(tags=["trades"])


class OpenTradeRequest(BaseModel):
    symbol: str
    lot: float
    order_type: str = "BUY"


class CloseTradeRequest(BaseModel):
    ticket: int


def _get_trade_provider(request: Request) -> TradeProvider:
    return request.app.state.trade_provider


@router.get("/trades/open")
async def open_positions(
    provider: TradeProvider = Depends(_get_trade_provider),
) -> dict[str, Any]:
    data = await provider.get_open_positions()
    return ok(data)


@router.get("/trades/history")
async def trade_history(
    provider: TradeProvider = Depends(_get_trade_provider),
) -> dict[str, Any]:
    data = await provider.get_trade_history()
    return ok(data)


@router.post("/trade/open")
async def open_trade(
    payload: OpenTradeRequest,
    provider: TradeProvider = Depends(_get_trade_provider),
) -> dict[str, Any]:
    result = await provider.open_trade(payload.symbol, payload.lot, payload.order_type)
    return ok(result, message=f"{payload.order_type} {payload.symbol} @ {payload.lot} lot opened")


@router.post("/trade/close")
async def close_trade(
    payload: CloseTradeRequest,
    provider: TradeProvider = Depends(_get_trade_provider),
) -> dict[str, Any]:
    result = await provider.close_trade(payload.ticket)
    return ok(result, message=f"Trade #{payload.ticket} closed")
