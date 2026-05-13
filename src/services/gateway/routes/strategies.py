from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from services.gateway.envelope import error, ok
from services.gateway.strategy_registry import get_strategy, list_strategies, toggle_strategy

router = APIRouter(tags=["strategies"])


class PromoteRequest(BaseModel):
    targetStage: str = ""
    mode: str = "promote"


@router.get("/strategies")
async def strategies() -> dict[str, Any]:
    return ok(list_strategies())


@router.post("/strategies/{strategy_id}/toggle")
async def toggle(strategy_id: str) -> dict[str, Any]:
    updated = toggle_strategy(strategy_id)
    if updated is None:
        return error(f"Strategy '{strategy_id}' not found")
    return ok(updated, message=f"Strategy '{updated['name']}' toggled {'on' if updated['enabled'] else 'off'}")


@router.post("/strategies/{strategy_id}/run")
async def run_strategy(strategy_id: str) -> dict[str, Any]:
    s = get_strategy(strategy_id)
    if s is None:
        return error(f"Strategy '{strategy_id}' not found")
    if not s["enabled"]:
        return error(f"Strategy '{s['name']}' is disabled. Enable it first.")
    return ok(s, message=f"Strategy '{s['name']}' run triggered.")


@router.post("/strategies/{strategy_id}/promote")
async def promote_strategy(strategy_id: str, body: PromoteRequest) -> dict[str, Any]:
    s = get_strategy(strategy_id)
    if s is None:
        return error(f"Strategy '{strategy_id}' not found")
    return ok(s, message=f"Strategy '{s['name']}' promoted to {body.targetStage or 'next stage'}")
