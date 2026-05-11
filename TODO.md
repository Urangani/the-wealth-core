Define Docker Compose Environment

Description

Create a docker-compose.yaml to orchestrate all core services (NATS, PostgreSQL, TimescaleDB, Redis) and provide service discovery. Ensure network isolation and healthcheck configuration. Acceptance: All containers start, are networked, and can be reached from each other.

Good. Next step is moving from design into **runnable infrastructure**.

We will build the **foundation layer of thewealth-core**:

* Docker topology
* NATS event bus
* PostgreSQL + TimescaleDB
* Redis cache
* service skeleton boot order
* shared event schema package

No trading logic yet. Only system spine.

---

# 1. Core Infrastructure (Docker Compose)

This is your local production-like environment.

## Stack

* Docker
* NATS
* PostgreSQL
* TimescaleDB
* Redis

---

# 2. docker-compose.yml (Core Backbone)

```yaml id="core-docker"
version: "3.9"

services:

  postgres:
    image: postgres:16
    container_name: thewealth-postgres
    environment:
      POSTGRES_USER: thewealth
      POSTGRES_PASSWORD: thewealth
      POSTGRES_DB: thewealth
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  timescaledb:
    image: timescale/timescaledb:latest-pg16
    container_name: thewealth-timescale
    environment:
      POSTGRES_USER: thewealth
      POSTGRES_PASSWORD: thewealth
      POSTGRES_DB: market
    ports:
      - "5433:5432"
    volumes:
      - tsdata:/var/lib/postgresql/data

  redis:
    image: redis:7
    container_name: thewealth-redis
    ports:
      - "6379:6379"

  nats:
    image: nats:2.10
    container_name: thewealth-nats
    ports:
      - "4222:4222"
      - "8222:8222"

volumes:
  pgdata:
  tsdata:
```

---

# 3. Service Boot Order (Critical)

Order matters.

```text id="boot-order"
1. NATS (event backbone)
2. PostgreSQL (state)
3. TimescaleDB (market data)
4. Redis (cache)
5. market-service
6. execution-service
7. strategy-service
8. analytics-service
9. gateway-service
```

Rule:

> If NATS is down, nothing else is allowed to start trading logic.

---

# 4. Shared Event Schema Package

This is the most important codebase in the system.

Create inside `thewealth-core/shared/`

---

## Event Base Model (Pydantic)

```python id="event-base"
from pydantic import BaseModel
from typing import Any, Dict
from datetime import datetime
import uuid

class BaseEvent(BaseModel):
    event_id: str = str(uuid.uuid4())
    event_type: str
    event_version: str = "v1"
    timestamp: datetime = datetime.utcnow()
    source: str
    correlation_id: str | None = None
    payload: Dict[str, Any]
```

---

## Example: Signal Event

```python id="signal-event"
class SignalGeneratedEvent(BaseEvent):
    event_type: str = "signal.generated"
    payload: dict  # strategy_id, symbol, side, confidence
```

---

## Example: Order Event

```python id="order-event"
class OrderSubmittedEvent(BaseEvent):
    event_type: str = "order.submitted"
    payload: dict  # order details
```

---

# 5. NATS Client Wrapper

All services must use ONE wrapper.

```python id="nats-wrapper"
import asyncio
from nats.aio.client import Client as NATS

class NatsClient:

    def __init__(self, url="nats://localhost:4222"):
        self.nc = NATS()
        self.url = url

    async def connect(self):
        await self.nc.connect(servers=[self.url])

    async def publish(self, subject: str, data: bytes):
        await self.nc.publish(subject, data)

    async def subscribe(self, subject: str, callback):
        await self.nc.subscribe(subject, cb=callback)
```

---

# 6. Service Skeleton Template

Every service in `thewealth-core` uses this pattern.

```python id="service-skeleton"
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup():
    print("service starting...")

@app.get("/health")
def health():
    return {"status": "ok"}
```

---

# 7. Environment Variables

Standardize across all services:

```text id="env"
NATS_URL=nats://nats:4222
POSTGRES_URL=postgresql://thewealth:thewealth@postgres:5432/thewealth
TIMESCALE_URL=postgresql://thewealth:thewealth@timescaledb:5432/market
REDIS_URL=redis://redis:6379
```

---

# 8. Execution Safety Layer (Core Principle)

Before ANY trading logic exists:

You must enforce:

## Hard rule

```text id="safety-rule"
No service can publish "order.*" events except execution-service
```

This becomes a guardrail later.

---

# 9. System Health Model

Each service must emit:

```text id="health-event"
system.health.v1
```

Example payload:

```json id="health-payload"
{
  "service": "market-service",
  "status": "healthy",
  "latency_ms": 12,
  "uptime": 1200
}
```

---

# 10. Minimal Working System (Target State)

After Sprint 1 you should be able to:

### Run system:

```text id="run-state"
docker-compose up
```

### Observe:

* NATS is running
* services boot successfully
* health endpoints respond
* dummy events flow through system

No trading yet.

But full backbone alive.

---

# 11. What We Are Building Now (Important Clarification)

At this stage:

You are NOT building:

* strategies
* trading logic
* ML models
* broker integration

You ARE building:

> a distributed event-driven trading operating system shell

Think:

* Linux kernel (not apps yet)
* networking layer (not websites)
* runtime (not features)

---

Checklist

- [x] Write docker-compose.yaml with all services

- [x] Configure healthchecks for each container

- [x] Test inter-container connectivity (e.g., psql, redis-cli, nats)

- [x] Everything is clearly and well documented in docs


