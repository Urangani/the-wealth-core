import asyncio
import os

from shared.events import MarketTickEvent, MarketTickPayload
from shared.nats_client import NatsClient


async def main() -> None:
    client = NatsClient(
        url=os.getenv("NATS_URL", "nats://thewealth:thewealth_nats@localhost:4222"),
        service_name="connectivity-check",
    )
    await client.connect()

    received = asyncio.Event()

    async def on_message(message):
        if message.subject == "v1.market.tick":
            received.set()

    await client.subscribe("v1.market.tick", on_message)
    await client.publish_event(
        MarketTickEvent(
            source="connectivity-check",
            payload=MarketTickPayload(
                symbol="EURUSD",
                bid=1.1,
                ask=1.1002,
                volume=1000,
                exchange_timestamp="2026-01-01T00:00:00Z",
            ),
        )
    )

    try:
        await asyncio.wait_for(received.wait(), timeout=2)
    except TimeoutError as exc:
        raise SystemExit("NATS pub/sub check timed out") from exc
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
