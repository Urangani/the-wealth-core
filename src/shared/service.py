import os
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from shared.events import SystemHealthEvent
from shared.nats_client import NatsClient


def create_service_app(service_name: str) -> FastAPI:
    started_at = time.monotonic()
    nats = NatsClient(
        url=os.getenv("NATS_URL", "nats://localhost:4222"),
        service_name=service_name,
    )
    state: dict[str, Any] = {"nats_connected": False}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await nats.connect()
        state["nats_connected"] = True
        app.state.nats = nats
        await nats.publish_event(
            SystemHealthEvent(
                source=service_name,
                payload={
                    "service": service_name,
                    "status": "healthy",
                    "latency_ms": 0,
                    "uptime": 0,
                },
            )
        )
        yield
        await nats.close()

    app = FastAPI(title=service_name, lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, Any]:
        status = "healthy" if state["nats_connected"] and nats.is_connected else "degraded"
        return {
            "service": service_name,
            "status": status,
            "nats_connected": nats.is_connected,
            "uptime": round(time.monotonic() - started_at, 3),
        }

    @app.get("/ready")
    def ready() -> dict[str, bool | str]:
        return {"service": service_name, "ready": nats.is_connected}

    return app
