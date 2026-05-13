from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from services.gateway.envelope import ok
from services.gateway.providers.base import TradeProvider

router = APIRouter(tags=["journal"])


def _get_trade_provider(request: Request) -> TradeProvider:
    return request.app.state.trade_provider


@router.get("/journal/trades")
async def journal_trades(
    provider: TradeProvider = Depends(_get_trade_provider),
) -> dict[str, Any]:
    data = await provider.get_trade_history()
    return ok(data)
