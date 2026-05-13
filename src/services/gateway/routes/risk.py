from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter

from services.gateway.envelope import ok

router = APIRouter(tags=["risk"])


@router.get("/risk/limits")
async def risk_limits() -> dict[str, Any]:
    data = {
        "max_lot": float(os.getenv("RISK_MAX_LOT", "0.5")),
        "max_open_trades": int(os.getenv("RISK_MAX_OPEN_TRADES", "5")),
        "max_daily_loss": float(os.getenv("RISK_MAX_DAILY_LOSS", "-50")),
        "allowed_symbols": [
            s.strip()
            for s in os.getenv("RISK_ALLOWED_SYMBOLS", "EURUSD,GBPUSD,USDJPY").split(",")
            if s.strip()
        ],
    }
    return ok(data)
