from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from services.gateway.envelope import ok

router = APIRouter(tags=["review"])


@router.get("/review/summary")
async def review_summary() -> dict[str, Any]:
    data = {
        "window_days": 7,
        "trades": 15,
        "win_rate": 66.67,
        "net_pnl": 120.50,
    }
    return ok(data)
