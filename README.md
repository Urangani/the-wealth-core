# The Wealth Core

Distributed event-driven trading system backbone.

This repository currently contains the foundation layer only:

- Docker Compose infrastructure for NATS, PostgreSQL, TimescaleDB, Redis, and service skeletons
- shared event schemas
- a shared NATS client wrapper
- FastAPI health endpoints for every core service
- local connectivity verification scripts

No trading logic, broker integration, strategies, or machine learning models are implemented yet.

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
