from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from services.gateway.envelope import ok
from services.gateway.providers.base import AccountProvider

router = APIRouter(tags=["account"])


def _get_account_provider(request: Request) -> AccountProvider:
    return request.app.state.account_provider


@router.get("/account/summary")
async def account_summary(
    provider: AccountProvider = Depends(_get_account_provider),
) -> dict[str, Any]:
    data = await provider.get_summary()
    return ok(data)
