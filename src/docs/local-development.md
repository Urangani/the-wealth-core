# Local Development

Run Python services directly on your host for fast iteration while Docker manages only the infrastructure (NATS, PostgreSQL, TimescaleDB, Redis).

## Architecture

```
┌────────────────────────────────────────────────┐
│  Host (your machine)            Docker          │
│                                             │
│  source .venv/bin/activate       ┌──────────────┐
│  uvicorn main:app --reload       │  nats:4222   │
│  pytest src/tests                 │  postgres:15432│
│                                  │  timescale:5433│
│  PYTHONPATH=src                   │  redis:6379   │
│                                  └──────────────┘
└────────────────────────────────────────────────┘
```

- **Dev** — services run via `uvicorn` on the host, connect to `localhost:*`
- **QA** — everything runs in Docker via `docker-compose.yaml` (unchanged)
- Both can coexist — they use separate Docker compose project names and don't interfere

## Prerequisites

- Python 3.12+
- Docker + Docker Compose
- `git`

## Quick Start

```bash
# 1. Run the setup script once
./setup_local.sh

# 2. Activate the virtual environment (sets PYTHONPATH=src automatically)
source .venv/bin/activate

# 3. Start infrastructure services
docker compose -f docker-compose.infra.yaml up -d

# 4. Run tests
pytest src/tests -v

# 5. Start a service
uvicorn main:app --reload --port 8001 --app-dir src/services/market-service
```

## Files

| File | Purpose |
|------|---------|
| `.venv/` | Python virtual environment (gitignored) |
| `.env` | Environment variables with `localhost:*` URLs (gitignored) |
| `docker-compose.infra.yaml` | Infrastructure-only Docker Compose (NATS, PostgreSQL, TimescaleDB, Redis) |
| `setup_local.sh` | One-time setup script — creates venv, installs deps, writes `.env`, configures `PYTHONPATH` |

## Workflow

### Activate the environment

```bash
source .venv/bin/activate
```

This sets `PYTHONPATH=src` automatically (appended to `.venv/bin/activate` by `setup_local.sh`).

### Manage infrastructure

```bash
# Start all infra services
docker compose -f docker-compose.infra.yaml up -d

# Check status
docker compose -f docker-compose.infra.yaml ps

# View logs
docker compose -f docker-compose.infra.yaml logs -f

# Restart one service (e.g., after changing NATS config)
docker compose -f docker-compose.infra.yaml restart nats

# Stop infra (data persists in Docker volumes)
docker compose -f docker-compose.infra.yaml down

# Stop and delete all data
docker compose -f docker-compose.infra.yaml down -v
```

### Run services

Each service runs as a standalone `uvicorn` process on the host:

```bash
# Market service (port 8001)
uvicorn main:app --reload --port 8001 --app-dir src/services/market-service

# Execution service (port 8002)
uvicorn main:app --reload --port 8002 --app-dir src/services/execution-service

# Strategy service (port 8003)
uvicorn main:app --reload --port 8003 --app-dir src/services/strategy-service

# Analytics service (port 8004)
uvicorn main:app --reload --port 8004 --app-dir src/services/analytics-service

# Gateway (port 8005)
uvicorn main:app --reload --port 8005 --app-dir src/services/gateway
```

Use `--reload` for hot-reload on file changes. Omit it in production-like runs.

### Run tests

```bash
# All tests
pytest src/tests -v

# Single file
pytest src/tests/test_event_contracts.py -v

# Single test
pytest src/tests/test_event_contracts.py -k "market_tick"
```

### Access databases

```bash
# PostgreSQL (app state)
psql -h localhost -p 15432 -U thewealth -d thewealth

# TimescaleDB (market data)
psql -h localhost -p 5433 -U thewealth -d market
```

Passwords are `thewealth`.

### Debug NATS

```bash
# NATS monitoring endpoint
curl http://localhost:8222/healthz
curl http://localhost:8222/varz

# Pub/sub test
python src/infrastructure/scripts/check_nats_pubsub.py
```

## Dev vs QA Comparison

| Aspect | Dev (this setup) | QA (docker compose) |
|--------|-----------------|---------------------|
| Python runner | `uvicorn` on host | Inside container |
| Code updates | Instant via `--reload` | Requires `docker compose up --build` |
| Dependencies | `pip install` in venv | Built into Docker image |
| Infrastructure | `docker-compose.infra.yaml` | `docker-compose.yaml` (full stack) |
| Data volumes | `thewealth-infra_*` | `thewealth-core_*` |
| Hot reload | Yes (`--reload`) | No |
| Debugger | Full host debugger support | Requires remote debugger |
| Reproducibility | System-dependent | Isolated, consistent |

Both can run simultaneously — they don't share ports or volumes.

## Syncing Changes to QA

When you're done iterating in dev and want to deploy to QA:

```bash
# Rebuild QA images with your changes
docker compose up --build

# Or rebuild just one service
docker compose up -d --build market-service
```

No manual file copying needed — the Dockerfile `COPY src /app/src` picks up whatever is on disk at build time.

## Adding Python Packages

```bash
# 1. Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# 2. Install locally
source .venv/bin/activate
pip install -r requirements.txt

# 3. For QA, rebuild the images
docker compose up --build
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Ensure `.venv/bin/activate` contains `PYTHONPATH=.../src` or run with `PYTHONPATH=src` prefix |
| Can't connect to NATS/Redis/DB | Run `docker compose -f docker-compose.infra.yaml ps` to verify infra is up |
| Port already in use | Check for conflicting services: `lsof -i :8001` |
| Tests fail with import error | Always run with `PYTHONPATH=src` or activate the venv |
| `.env` not loaded | `uvicorn` loads `.env` automatically if `python-dotenv` is installed (it's a dependency of `uvicorn[standard]`) |
