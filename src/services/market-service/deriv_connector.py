from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

import websockets
from config import MarketServiceSettings
from models import ProviderStatus, StreamCandle, StreamTick

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class DerivSymbol:
    symbol: str
    market: str


class DerivWebSocketConnector:
    def __init__(self, settings: MarketServiceSettings):
        self.settings = settings
        self._req_id = 0

    async def stream(
        self,
        out_queue: asyncio.Queue[Any],
        stop_event: asyncio.Event,
    ) -> None:
        while not stop_event.is_set():
            try:
                await out_queue.put(
                    ProviderStatus(
                        provider="deriv",
                        status="connected",
                        detail="connecting",
                    )
                )
                await self._run_session(out_queue, stop_event)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                LOGGER.exception("Deriv connector error: %s", exc)
                await out_queue.put(
                    ProviderStatus(
                        provider="deriv",
                        status="error",
                        detail=str(exc),
                    )
                )
                await out_queue.put(
                    ProviderStatus(
                        provider="deriv",
                        status="disconnected",
                        detail="will-reconnect",
                    )
                )
                for _ in range(int(self.settings.reconnect_delay_seconds / 0.1)):
                    if stop_event.is_set():
                        return
                    await asyncio.sleep(0.1)

    async def _run_session(
        self,
        out_queue: asyncio.Queue[Any],
        stop_event: asyncio.Event,
    ) -> None:
        async with websockets.connect(self.settings.deriv_ws_url, ping_interval=20) as ws:
            if self.settings.deriv_api_token:
                await self._send(
                    ws,
                    {
                        "authorize": self.settings.deriv_api_token,
                    },
                )
                await self._expect(ws, allowed_msg_types={"authorize"})

            symbols = await self._load_symbols(ws)
            if not symbols:
                raise RuntimeError("No symbols returned for requested markets")

            await self._subscribe_ticks(ws, symbols)
            await self._subscribe_candles(ws, symbols)

            await out_queue.put(
                ProviderStatus(
                    provider="deriv",
                    status="connected",
                    detail=f"subscriptions={len(symbols)}",
                )
            )

            while not stop_event.is_set():
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                except TimeoutError:
                    pong_waiter = await ws.ping()
                    await asyncio.wait_for(pong_waiter, timeout=10)
                    continue
                message = json.loads(raw)

                if message.get("error"):
                    raise RuntimeError(f"Deriv WS error: {message['error']}")

                msg_type = message.get("msg_type")
                if msg_type == "tick" and message.get("tick"):
                    await out_queue.put(StreamTick(data=message, source="deriv"))
                    continue

                if msg_type == "ohlc" and message.get("ohlc"):
                    await out_queue.put(StreamCandle(data=message["ohlc"], source="deriv"))
                    continue

                if msg_type in {"candles", "history"} and message.get("candles"):
                    for candle in message["candles"]:
                        await out_queue.put(StreamCandle(data=candle, source="deriv"))
                    continue

    async def _load_symbols(self, ws: websockets.WebSocketClientProtocol) -> list[DerivSymbol]:
        if self.settings.symbol_allowlist:
            # If a symbol allowlist is configured, avoid active symbol discovery
            # and subscribe directly to the provided symbols.
            return [DerivSymbol(symbol=symbol, market="unknown") for symbol in self.settings.symbol_allowlist]

        await self._send(
            ws,
            {
                "active_symbols": "brief",
                "product_type": "basic",
            },
        )
        response = await self._expect(ws, allowed_msg_types={"active_symbols"})
        symbols = []
        for item in response.get("active_symbols", []):
            symbol = str(item.get("symbol") or "")
            market = str(item.get("market") or "").lower()
            if not symbol or not market:
                continue
            symbols.append(DerivSymbol(symbol=symbol, market=market))

        return [item for item in symbols if item.market in self.settings.deriv_symbol_filter_markets]

    async def _subscribe_ticks(self, ws: websockets.WebSocketClientProtocol, symbols: list[DerivSymbol]) -> None:
        for item in symbols:
            await self._send(
                ws,
                {
                    "ticks": item.symbol,
                    "subscribe": 1,
                },
            )

    async def _subscribe_candles(self, ws: websockets.WebSocketClientProtocol, symbols: list[DerivSymbol]) -> None:
        for item in symbols:
            for granularity in self.settings.candle_granularities:
                await self._send(
                    ws,
                    {
                        "ticks_history": item.symbol,
                        "style": "candles",
                        "granularity": granularity,
                        "end": "latest",
                        "count": 1,
                        "subscribe": 1,
                    },
                )

    async def _send(self, ws: websockets.WebSocketClientProtocol, payload: dict[str, Any]) -> None:
        self._req_id += 1
        request = dict(payload)
        request["req_id"] = self._req_id
        await ws.send(json.dumps(request))

    async def _expect(
        self,
        ws: websockets.WebSocketClientProtocol,
        *,
        allowed_msg_types: set[str],
    ) -> dict[str, Any]:
        while True:
            raw = await ws.recv()
            message = json.loads(raw)
            if message.get("error"):
                raise RuntimeError(f"Deriv request failed: {message['error']}")
            msg_type = message.get("msg_type")
            if msg_type in allowed_msg_types:
                return message
