from __future__ import annotations

from typing import Any

_strategies: list[dict[str, Any]] = [
    {
        "id": "london_breakout",
        "name": "London Breakout",
        "enabled": True,
        "description": "Trades breakouts at the London session open.",
        "params": {"lot": 0.1, "sl_pips": 20, "tp_pips": 40},
    },
    {
        "id": "ny_reversal",
        "name": "NY Reversal",
        "enabled": False,
        "description": "Mean-reversion strategy at New York session open.",
        "params": {"lot": 0.05, "sl_pips": 15, "tp_pips": 30},
    },
    {
        "id": "trend_follow",
        "name": "Trend Following",
        "enabled": True,
        "description": "Multi-timeframe trend following using EMA crossovers.",
        "params": {"ema_fast": 12, "ema_slow": 26},
    },
]


def list_strategies() -> list[dict[str, Any]]:
    return _strategies


def get_strategy(strategy_id: str) -> dict[str, Any] | None:
    return next((s for s in _strategies if s["id"] == strategy_id), None)


def toggle_strategy(strategy_id: str) -> dict[str, Any] | None:
    s = get_strategy(strategy_id)
    if s:
        s["enabled"] = not s["enabled"]
    return s
