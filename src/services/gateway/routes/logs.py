from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from services.gateway.envelope import ok
from services.gateway.providers.base import LogProvider

router = APIRouter(tags=["logs"])


def _get_log_provider(request: Request) -> LogProvider:
    return request.app.state.log_provider


@router.get("/logs")
async def logs(
    limit: int = Query(default=300, ge=1, le=2000),
    severity: str = Query(default="ALL", description="ALL | INFO | WARN | ERROR"),
    provider: LogProvider = Depends(_get_log_provider),
) -> dict[str, Any]:
    data = await provider.get_logs(limit, severity.upper())
    return ok(data)
