import asyncio
import json
import os

import websockets


async def main() -> None:
    ws_url = os.getenv(
        "DERIV_WS_URL",
        "wss://api.derivws.com/trading/v1/options/ws/public",
    )

    print(f"Connecting to {ws_url}")
    async with websockets.connect(ws_url) as ws:
        request = {
            "active_symbols": "brief",
            "product_type": "basic",
            "req_id": 1,
        }
        await ws.send(json.dumps(request))
        response = await ws.recv()
        print(response)


if __name__ == "__main__":
    asyncio.run(main())
