import sys
from datetime import UTC, datetime
from pathlib import Path

MARKET_SERVICE_PATH = Path(__file__).resolve().parents[1] / "services" / "market-service"
if str(MARKET_SERVICE_PATH) not in sys.path:
    sys.path.insert(0, str(MARKET_SERVICE_PATH))

from normalization import normalize_deriv_candle, normalize_deriv_tick  # noqa: E402


def test_normalize_deriv_tick_maps_to_versioned_market_event() -> None:
    message = {
        "tick": {
            "symbol": "frxEURUSD",
            "quote": "1.12345",
            "bid": "1.12340",
            "ask": "1.12350",
            "epoch": 1715000000,
            "volume": 123,
        }
    }

    normalized = normalize_deriv_tick(message, source="deriv")

    assert normalized.event.subject == "v1.market.tick"
    assert normalized.event.payload.symbol == "frxEURUSD"
    assert normalized.event.payload.last == 1.12345
    assert normalized.tick_record is not None
    assert normalized.tick_record.source == "deriv"


def test_normalize_deriv_candle_maps_to_contract() -> None:
    candle = {
        "symbol": "R_100",
        "open": "100.1",
        "high": "100.5",
        "low": "99.8",
        "close": "100.3",
        "volume": "55",
        "open_time": 1715000000,
        "epoch": 1715000060,
        "granularity": 60,
    }

    normalized = normalize_deriv_candle(candle, source="fallback")

    assert normalized.event.subject == "v1.market.candle"
    assert normalized.event.payload.symbol == "R_100"
    assert normalized.event.payload.timeframe == "60s"
    assert normalized.event.payload.candle_start.tzinfo == UTC
    assert isinstance(normalized.event.payload.candle_end, datetime)
    assert normalized.candle_record is not None
    assert normalized.candle_record.source == "fallback"
