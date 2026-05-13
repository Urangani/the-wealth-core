from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from typing import Any

from .base import AccountProvider, LogProvider, TradeProvider


def _usd(v: float) -> float:
    return round(v, 2)


def _ts(days_ago: int = 0) -> str:
    return (datetime.now(UTC) - timedelta(days=days_ago)).isoformat()


class MockAccountProvider(AccountProvider):
    BASE_BALANCE = 50_000.0

    def __init__(self) -> None:
        self._balance = self.BASE_BALANCE
        self._equity = self.BASE_BALANCE
        self._open_pnl = 0.0

    def _tick(self) -> None:
        shift = random.gauss(0, 15)
        self._open_pnl = max(-3000.0, min(5000.0, self._open_pnl + shift))
        self._equity = max(1000.0, self._balance + self._open_pnl)

    async def get_summary(self) -> dict[str, Any]:
        self._tick()
        margin = random.uniform(800, 2000)
        margin_free = self._equity - margin
        margin_level = (self._equity / margin * 100) if margin > 0 else 0
        return {
            "name": "Demo Account",
            "login": 12345678,
            "balance": _usd(self._balance),
            "equity": _usd(self._equity),
            "profit": _usd(self._open_pnl),
            "margin": _usd(margin),
            "margin_free": _usd(max(0, margin_free)),
            "margin_level": round(margin_level, 2),
            "currency": "USD",
            "leverage": 100,
        }


class MockTradeProvider(TradeProvider):
    _ticket_counter = 10000

    def __init__(self) -> None:
        self._positions: list[dict[str, Any]] = [
            {
                "ticket": 1001,
                "symbol": "EURUSD",
                "type": "BUY",
                "volume": 0.1,
                "open_price": 1.0840,
                "current_price": 1.0865,
                "profit": 25.00,
                "sl": 1.0800,
                "tp": 1.0900,
                "time": _ts(0),
                "close_price": None,
                "status": "OPEN",
            },
            {
                "ticket": 1002,
                "symbol": "GBPUSD",
                "type": "SELL",
                "volume": 0.2,
                "open_price": 1.2560,
                "current_price": 1.2545,
                "profit": 30.00,
                "sl": 1.2600,
                "tp": 1.2500,
                "time": _ts(0),
                "close_price": None,
                "status": "OPEN",
            },
            {
                "ticket": 1003,
                "symbol": "USDJPY",
                "type": "BUY",
                "volume": 0.05,
                "open_price": 151.200,
                "current_price": 151.350,
                "profit": 7.50,
                "sl": 151.000,
                "tp": 151.600,
                "time": _ts(0),
                "close_price": None,
                "status": "OPEN",
            },
        ]

        self._history: list[dict[str, Any]] = []
        self._seed_history()

    def _tick_prices(self) -> None:
        for p in self._positions:
            drift = random.gauss(0, 0.0003)
            if p["type"] == "BUY":
                p["current_price"] = _usd(p["current_price"] + drift) if isinstance(p["current_price"], float) else p["current_price"]
            else:
                p["current_price"] = _usd(p["current_price"] - drift) if isinstance(p["current_price"], float) else p["current_price"]
            diff = (p["current_price"] - p["open_price"]) if p["type"] == "BUY" else (p["open_price"] - p["current_price"])
            p["profit"] = _usd(diff * p["volume"] * 100000)

    def _seed_history(self) -> None:
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
        for i in range(20):
            side = random.choice(["BUY", "SELL"])
            sym = random.choice(symbols)
            days = random.randint(1, 30)
            vol = random.choice([0.1, 0.2, 0.05, 0.5])
            open_p = round(random.uniform(1.05, 1.50) if sym != "USDJPY" else random.uniform(148, 155), 5)
            close_p = _usd(open_p + random.gauss(0, 0.01)) if sym != "USDJPY" else _usd(open_p + random.gauss(0, 0.5))
            profit = _usd((close_p - open_p) * vol * 100000) if side == "BUY" else _usd((open_p - close_p) * vol * 100000)
            self._history.append({
                "id": f"hist-{10000 + i}",
                "ticket": 9900 + i,
                "symbol": sym,
                "type": side,
                "volume": vol,
                "open_price": open_p,
                "close_price": close_p,
                "profit": profit,
                "status": "CLOSED",
                "created_at": _ts(days),
            })

    async def get_open_positions(self) -> list[dict[str, Any]]:
        self._tick_prices()
        return self._positions

    async def open_trade(
        self, symbol: str, lot: float, order_type: str
    ) -> dict[str, Any]:
        self._ticket_counter += 1
        price = round(random.uniform(1.08, 1.09) if symbol != "USDJPY" else random.uniform(150, 152), 5)
        ticket = self._ticket_counter
        self._positions.append({
            "ticket": ticket,
            "symbol": symbol,
            "type": order_type,
            "volume": lot,
            "open_price": price,
            "current_price": price,
            "profit": 0.0,
            "sl": None,
            "tp": None,
            "time": _ts(0),
            "close_price": None,
            "status": "OPEN",
        })
        return {"ticket": ticket, "price": price, "retcode": 10009}

    async def close_trade(self, ticket: int) -> dict[str, Any]:
        for i, p in enumerate(self._positions):
            if p["ticket"] == ticket:
                close_p = _usd(p["current_price"] + random.gauss(0, 0.002))
                profit = _usd(
                    (close_p - p["open_price"]) * p["volume"] * 100000
                    if p["type"] == "BUY"
                    else (p["open_price"] - close_p) * p["volume"] * 100000
                )
                closed = {**p, "close_price": close_p, "profit": profit, "status": "CLOSED", "created_at": _ts(0)}
                self._history.insert(0, closed)
                self._positions.pop(i)
                return {"ticket": ticket, "symbol": p["symbol"], "close_price": close_p, "profit": profit}
        return {"ticket": ticket, "symbol": "UNKNOWN", "close_price": 0, "profit": 0}

    async def get_trade_history(self) -> list[dict[str, Any]]:
        return self._history


class MockLogProvider(LogProvider):
    def __init__(self) -> None:
        self._logs: list[dict[str, Any]] = [
            {"time": _ts(0), "event": "Gateway service started", "severity": "INFO", "logger": "gateway"},
            {"time": _ts(0), "event": "Mock providers initialized", "severity": "INFO", "logger": "gateway"},
            {"time": _ts(0), "event": "WebSocket endpoint ready", "severity": "INFO", "logger": "gateway.stream"},
        ]
        self._counter = 0

    def push(self, event: str, severity: str = "INFO", logger: str = "gateway") -> None:
        self._logs.insert(0, {
            "time": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S,%f")[:-3],
            "event": event,
            "severity": severity,
            "logger": logger,
        })

    async def get_logs(self, limit: int, severity: str) -> list[dict[str, Any]]:
        result = self._logs if severity == "ALL" else [entry for entry in self._logs if entry["severity"] == severity]
        return result[:limit]
