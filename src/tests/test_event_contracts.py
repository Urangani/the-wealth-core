from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from shared.events import (
    MarketTickEvent,
    MarketTickPayload,
    OrderSubmittedEvent,
    OrderSubmittedPayload,
    SignalGeneratedEvent,
    SignalGeneratedPayload,
)
from shared.nats_client import NatsClient, OrderPublishPermissionError


def test_market_tick_event_serializes_with_versioned_subject() -> None:
    event = MarketTickEvent(
        source="market-service",
        payload=MarketTickPayload(
            symbol="EURUSD",
            bid=1.1,
            ask=1.1002,
            exchange_timestamp=datetime.now(timezone.utc),
        ),
    )

    encoded = event.model_dump_json()
    decoded = MarketTickEvent.model_validate_json(encoded)

    assert decoded.subject == "v1.market.tick"
    assert decoded.payload.symbol == "EURUSD"


def test_signal_payload_validation() -> None:
    with pytest.raises(ValidationError):
        SignalGeneratedEvent(
            source="strategy-service",
            payload=SignalGeneratedPayload(
                signal_id="sig-1",
                strategy_id="strat-1",
                symbol="EURUSD",
                side="buy",
                strength=1.2,
                confidence=0.9,
                generated_at=datetime.now(timezone.utc),
            ),
        )


def test_only_execution_service_can_publish_order_subjects() -> None:
    order = OrderSubmittedEvent(
        source="strategy-service",
        payload=OrderSubmittedPayload(
            order_id="ord-1",
            strategy_id="strat-1",
            symbol="EURUSD",
            side="buy",
            order_type="market",
            quantity=1,
            submitted_at=datetime.now(timezone.utc),
        ),
    )

    strategy_client = NatsClient(service_name="strategy-service")
    execution_client = NatsClient(service_name="execution-service")

    with pytest.raises(OrderPublishPermissionError):
        strategy_client._assert_can_publish(order.subject)

    execution_client._assert_can_publish(order.subject)
