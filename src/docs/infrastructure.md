# The Wealth Core Infrastructure

This repository starts as a distributed, event-driven trading operating system shell. It does not contain strategies, broker integration, machine learning, or live trading behavior yet.

## Services

The local backbone is defined in `docker-compose.yaml`:

| Service | Purpose | Host port |
| --- | --- | --- |
| `nats` | Authenticated event backbone with JetStream enabled | `4222`, `8222` |
| `postgres` | Application state | `15432` |
| `timescaledb` | Market data storage | `5433` |
| `redis` | Cache and fast ephemeral state | `6379` |
| `market-service` | Market data service skeleton | `8001` |
| `execution-service` | Execution service skeleton | `8002` |
| `strategy-service` | Strategy service skeleton | `8003` |
| `analytics-service` | Analytics service skeleton | `8004` |
| `gateway-service` | Gateway service skeleton | `8005` |

All containers run on the isolated `core` Docker network and use Docker DNS service names for inter-container discovery.

## Boot Order

Infrastructure starts before service skeletons:

1. NATS
2. PostgreSQL
3. TimescaleDB
4. Redis
5. market-service
6. execution-service
7. strategy-service
8. analytics-service
9. gateway-service

The Compose file enforces health-gated startup through `depends_on` conditions. Service containers connect to NATS during startup; if NATS is unavailable, the service startup fails instead of pretending the event backbone is alive.

## Environment

Service containers receive these standard URLs:

```text
NATS_URL=nats://thewealth:thewealth_nats@nats:4222
POSTGRES_URL=postgresql://thewealth:thewealth@postgres:5432/thewealth
TIMESCALE_URL=postgresql://thewealth:thewealth@timescaledb:5432/market
REDIS_URL=redis://redis:6379
```

## NATS

NATS is configured by `src/infrastructure/nats/nats-server.conf`. Authentication is required; services use the `thewealth` application user through `NATS_URL`.

Event subjects are versioned with this format:

```text
v1.<event_type>
```

Examples:

- `v1.market.tick`
- `v1.signal.generated`
- `v1.order.submitted`
- `v1.order.filled`
- `v1.position.opened`
- `v1.system.health`

Publish typed events through `NatsClient.publish_event(event)`. Subscribe to explicit subjects or wildcard groups, for example `v1.market.*` for market data consumers and `v1.order.*` for execution/order projections.

## Event Contract

Shared event schemas live in `src/shared/events`.

Every event includes:

- `event_id`
- `event_type`
- `event_version`
- `timestamp`
- `source`
- `correlation_id`
- `payload`

The first concrete events are:

- `market.tick`
- `market.candle`
- `signal.generated`
- `order.submitted`
- `order.filled`
- `position.opened`
- `position.closed`
- `system.health`

The NATS wrapper in `src/shared/nats_client.py` enforces this hard rule:

```text
No service can publish "order.*" events except execution-service.
```

## Database Schemas

PostgreSQL initialization SQL lives in `src/infrastructure/postgres/init` and creates:

- `users`
- `strategies`
- `orders`
- `positions`
- `events`

TimescaleDB initialization SQL lives in `src/infrastructure/timescaledb/init` and creates hypertables for:

- `ticks`
- `candles`
- `features`
- `indicators`

The init scripts run automatically on first container startup when the Docker volumes are empty. If an existing local volume predates the scripts, recreate it with `docker compose down -v` before starting the stack again.

## Run

```bash
docker compose up --build
```

Health endpoints:

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

NATS monitoring:

```bash
curl http://localhost:8222/healthz
```

## Connectivity Checks

Run the helper script after the stack is up:

```bash
bash src/infrastructure/scripts/check_connectivity.sh
```

## Testing and Debugging

For copyable test commands, Docker Compose operations, log inspection, database checks, NATS debugging, and common failure flows, see `src/docs/testing-and-debugging.md`.
