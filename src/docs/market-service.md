# Market Service: Deriv + NATS + Timescale

This document covers the market data pipeline implemented in `market-service`.

## What It Does

`market-service` now:

1. Connects to Deriv WebSocket and optionally authenticates (if `DERIV_API_TOKEN` is set).
2. Loads active symbols and filters for `forex` and `synthetic_index` markets by default.
3. Subscribes to live ticks (`ticks`) and live candles (`ticks_history` with `style=candles`).
4. Normalizes payloads into internal event contracts:
   - `v1.market.tick`
   - `v1.market.candle`
5. Publishes normalized events to NATS via `NatsClient.publish_event`.
6. Persists ticks/candles asynchronously to TimescaleDB.
7. Adds retention policies:
   - ticks: 30 days
   - candles: 180 days
8. Falls back to a synthetic provider when Deriv disconnects or errors.

## Key Files

- `src/services/market-service/main.py`: app lifecycle, health/readiness routes
- `src/services/market-service/deriv_connector.py`: Deriv WebSocket connector + reconnect loop
- `src/services/market-service/normalization.py`: raw payload -> event contract mapping
- `src/services/market-service/pipeline.py`: orchestration, publish, failover, batching
- `src/services/market-service/timescale_writer.py`: async persistence + retention setup
- `src/services/market-service/fallback_provider.py`: synthetic fallback stream

## Health and Runtime Status

Endpoints:

- `GET /health`
- `GET /ready`
- `GET /market/status`

`/market/status` exposes provider mode (`primary`, `fallback`, `degraded`), queue depth, and processed counters.

## Configuration

Primary settings (environment variables):

- `DERIV_APP_ID`
- `DERIV_WS_URL`
- `DERIV_API_TOKEN` (optional)
- `DERIV_MARKETS` (default: `forex,synthetic_index`)
- `MARKET_SYMBOLS` (optional allowlist override)
- `MARKET_CANDLE_GRANULARITIES` (default: `60`)
- `MARKET_RECONNECT_DELAY_SECONDS`
- `MARKET_FALLBACK_ENABLED`
- `MARKET_FALLBACK_INTERVAL_SECONDS`
- `FALLBACK_MARKET_SYMBOLS`
- `MARKET_BATCH_FLUSH_SIZE`
- `MARKET_BATCH_FLUSH_INTERVAL_SECONDS`
- `MARKET_TICK_RETENTION_DAYS`
- `MARKET_CANDLE_RETENTION_DAYS`

## Verification Commands

Start stack:

```bash
docker compose up -d --build
```

Health and status:

```bash
curl http://localhost:8001/health
curl http://localhost:8001/market/status
```

Watch market-service logs:

```bash
docker compose logs -f market-service
```

Confirm events are published:

```bash
docker compose exec market-service python /app/src/infrastructure/scripts/check_nats_pubsub.py
```

Query persisted market rows:

```bash
docker compose exec timescaledb psql -U thewealth -d market -c "SELECT symbol, time, last FROM ticks ORDER BY time DESC LIMIT 5;"
docker compose exec timescaledb psql -U thewealth -d market -c "SELECT symbol, timeframe, time, close FROM candles ORDER BY time DESC LIMIT 5;"
```
