from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    return float(raw)


def _env_csv(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [token.strip() for token in raw.split(",") if token.strip()]


@dataclass(slots=True, frozen=True)
class MarketServiceSettings:
    deriv_ws_url: str
    deriv_api_token: str | None
    deriv_symbol_filter_markets: set[str]
    symbol_allowlist: list[str]
    candle_granularities: list[int]
    reconnect_delay_seconds: float
    fallback_enabled: bool
    fallback_interval_seconds: float
    fallback_symbols: list[str]
    timescale_url: str
    stream_queue_size: int
    batch_flush_size: int
    batch_flush_interval_seconds: float
    tick_retention_days: int
    candle_retention_days: int

    @classmethod
    def from_env(cls) -> MarketServiceSettings:
        app_id = os.getenv("DERIV_APP_ID", "1089")
        deriv_ws_url = os.getenv(
            "DERIV_WS_URL",
            f"wss://ws.derivws.com/websockets/v3?app_id={app_id}",
        )
        derived_markets = set(
            token.strip().lower()
            for token in os.getenv(
                "DERIV_MARKETS",
                "forex,synthetic_index",
            ).split(",")
            if token.strip()
        )

        granularities = [int(value) for value in _env_csv("MARKET_CANDLE_GRANULARITIES") or ["60"]]
        granularities = sorted(set(granularities))

        return cls(
            deriv_ws_url=deriv_ws_url,
            deriv_api_token=os.getenv("DERIV_API_TOKEN"),
            deriv_symbol_filter_markets=derived_markets,
            symbol_allowlist=_env_csv("MARKET_SYMBOLS"),
            candle_granularities=granularities,
            reconnect_delay_seconds=_env_float("MARKET_RECONNECT_DELAY_SECONDS", 3.0),
            fallback_enabled=_env_bool("MARKET_FALLBACK_ENABLED", True),
            fallback_interval_seconds=_env_float("MARKET_FALLBACK_INTERVAL_SECONDS", 1.0),
            fallback_symbols=_env_csv("FALLBACK_MARKET_SYMBOLS") or ["frxEURUSD", "R_100"],
            timescale_url=os.getenv(
                "TIMESCALE_URL",
                "postgresql://thewealth:thewealth@timescaledb:5432/market",
            ),
            stream_queue_size=_env_int("MARKET_STREAM_QUEUE_SIZE", 20000),
            batch_flush_size=_env_int("MARKET_BATCH_FLUSH_SIZE", 200),
            batch_flush_interval_seconds=_env_float("MARKET_BATCH_FLUSH_INTERVAL_SECONDS", 1.0),
            tick_retention_days=_env_int("MARKET_TICK_RETENTION_DAYS", 30),
            candle_retention_days=_env_int("MARKET_CANDLE_RETENTION_DAYS", 180),
        )
