# The Wealth Core

Distributed event-driven trading system backbone with a live market-data ingestion path.

This repository currently contains:

- Docker Compose infrastructure for NATS, TimescaleDB, Redis, market-service, and gateway
- authenticated NATS with versioned event subjects
- TimescaleDB initialization schemas (single database handles app state + market data)
- shared, versioned Pydantic event schemas
- a shared NATS client wrapper
- FastAPI health endpoints for every service
- Deriv WebSocket market connector (ticks + candles), NATS publication, Timescale persistence, and fallback feed in `market-service`
- REST API gateway for UI consumption
- local connectivity verification scripts

No strategy execution logic, broker order integration, or machine learning models are implemented yet.

## Quick Start

```bash
docker compose up --build
```

Service health endpoints:

- market-service: http://localhost:8001/health
- gateway-service: http://localhost:8005/health
- Aggregated system health: http://localhost:8005/api/v1/system/health

Database port:

- TimescaleDB (single DB for all state): `localhost:5433`

Run connectivity checks once the stack is healthy:

```bash
bash src/infrastructure/scripts/check_connectivity.sh
```

To test Deriv `active_symbols` directly without the full service:

```bash
python src/infrastructure/scripts/fetch_deriv_active_symbols.py
```

## Deriv API Setup

The system can connect to Deriv public market data without authentication by setting:

```bash
DERIV_WS_URL=wss://api.derivws.com/trading/v1/options/ws/public
DERIV_API_TOKEN=
```

If you want authenticated trading access later, provide your own `DERIV_APP_ID` and `DERIV_API_TOKEN`.

1. Get your own Deriv App ID and API Token from [Deriv API Dashboard](https://app.deriv.com/account/api-token)
2. Run the setup script: `./setup_deriv.sh`
3. Or manually update the `.env` file with your credentials

See `src/docs/deriv-api.md` for detailed API documentation.

**Note:** The demo App ID (1089) included in the configuration is rate-limited and may not work reliably for extended use.

Run contract tests locally:

```bash
PYTHONPATH=src pytest src/tests
```
