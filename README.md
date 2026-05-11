# The Wealth Core

Distributed event-driven trading system backbone with a live market-data ingestion path.

This repository currently contains:

- Docker Compose infrastructure for NATS, PostgreSQL, TimescaleDB, Redis, and service skeletons
- authenticated NATS with versioned event subjects
- PostgreSQL and TimescaleDB initialization schemas
- shared, versioned Pydantic event schemas
- a shared NATS client wrapper
- FastAPI health endpoints for every core service
- Deriv WebSocket market connector (ticks + candles), NATS publication, Timescale persistence, and fallback feed in `market-service`
- local connectivity verification scripts

No strategy execution logic, broker order integration, or machine learning models are implemented yet.

## Quick Start

```bash
docker compose up --build
```

Service health endpoints:

- market-service: http://localhost:8001/health
- execution-service: http://localhost:8002/health
- strategy-service: http://localhost:8003/health
- analytics-service: http://localhost:8004/health
- gateway-service: http://localhost:8005/health

Database ports:

- PostgreSQL: `localhost:15432`
- TimescaleDB: `localhost:5433`

Run connectivity checks once the stack is healthy:

```bash
bash src/infrastructure/scripts/check_connectivity.sh
```

See `src/docs/infrastructure.md` for the full infrastructure notes.
See `src/docs/testing-and-debugging.md` for test, debug, Docker, and Docker Compose command snippets.
See `src/docs/market-service.md` for Deriv connector, failover, and market persistence details.

Run contract tests locally:

```bash
PYTHONPATH=src pytest src/tests
```
