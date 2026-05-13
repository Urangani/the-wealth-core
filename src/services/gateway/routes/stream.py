from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.gateway.state import has_changed

LOGGER = logging.getLogger("gateway.stream")
router = APIRouter(tags=["ws"])

_active_connections: list[WebSocket] = []
_price = {"symbol": "EURUSD", "bid": 1.0850, "ask": 1.0852}
_account = {
    "balance": 50000.0,
    "equity": 50000.0,
    "profit": 0.0,
    "margin": 0.0,
    "margin_free": 50000.0,
    "margin_level": 0.0,
}
_positions: list[dict[str, Any]] = []


def _build_price_tick() -> dict[str, Any]:
    _price["bid"] = round(_price["bid"] + random.gauss(0, 0.0002), 5)
    _price["ask"] = round(_price["bid"] + random.uniform(0.0001, 0.0005), 5)
    return dict(_price)


def _build_account_update() -> dict[str, Any] | None:
    equity_shift = random.gauss(0, 50)
    new_equity = round(max(1000, _account["equity"] + equity_shift), 2)
    if not has_changed("ws_equity", round(new_equity, 0)):
        return None
    _account["equity"] = new_equity
    _account["profit"] = round(_account["equity"] - _account["balance"], 2)
    _account["margin"] = round(random.uniform(500, 2000), 2)
    _account["margin_free"] = round(max(0, _account["equity"] - _account["margin"]), 2)
    _account["margin_level"] = round(
        (_account["equity"] / _account["margin"] * 100) if _account["margin"] > 0 else 0, 2
    )
    return dict(_account)


def _build_positions_update() -> list[dict[str, Any]] | None:
    if not _positions:
        return None
    for p in _positions:
        drift = random.gauss(0, 0.0003)
        p["current_price"] = round(p["current_price"] + drift, 5) if isinstance(p["current_price"], float) else p["current_price"]
        diff = (p["current_price"] - p["open_price"]) if p["type"] == "BUY" else (p["open_price"] - p["current_price"])
        p["profit"] = round(diff * p["volume"] * 100000, 2)
    if not has_changed("ws_positions", [p["ticket"] for p in _positions]):
        return None
    return list(_positions)


async def _broadcast(msg: dict[str, Any]) -> None:
    dead: list[WebSocket] = []
    for ws in _active_connections:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _active_connections.remove(ws)


async def _stream_loop() -> None:
    while True:
        try:
            await _broadcast({"type": "price", "data": _build_price_tick()})
            await _broadcast({"type": "status", "data": {"mt5_connected": True}})

            acc = _build_account_update()
            if acc:
                await _broadcast({"type": "account", "data": acc})

            pos = _build_positions_update()
            if pos:
                await _broadcast({"type": "positions", "data": pos})
        except Exception:
            LOGGER.exception("stream loop error")
        await asyncio.sleep(0.5)


@router.websocket("/ws/market")
async def market_stream(ws: WebSocket) -> None:
    await ws.accept()
    _active_connections.append(ws)
    LOGGER.info("WebSocket client connected")
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        LOGGER.info("WebSocket client disconnected")
    finally:
        if ws in _active_connections:
            _active_connections.remove(ws)
