# Testing and Docker Debugging

This guide collects the commands used to test, debug, analyze, and operate the local The Wealth Core Docker Compose stack.

Run commands from the repository root:

```bash
cd the-wealth-core
```

## Fast Checks

Validate the Compose file without starting containers:

```bash
docker compose config
```

Start or rebuild the whole stack:

```bash
docker compose up -d --build
```

Check container status and health:

```bash
docker compose ps
```

Run the infrastructure connectivity checks:

```bash
bash src/infrastructure/scripts/check_connectivity.sh
```

Run the Python contract tests inside the service image:

```bash
docker compose exec market-service pytest /app/src/tests
```

Run the same tests on the host if dependencies are installed locally:

```bash
PYTHONPATH=src pytest src/tests
```

## Docker Compose Operations

Start the stack in the background:

```bash
docker compose up -d
```

Rebuild service images after dependency or source changes:

```bash
docker compose build
docker compose up -d
```

Rebuild and recreate only one service:

```bash
docker compose up -d --build market-service
```

Stop containers without deleting volumes:

```bash
docker compose down
```

Stop containers and delete local database/cache volumes:

```bash
docker compose down -v
```

Use `down -v` only when you want PostgreSQL, TimescaleDB, Redis, and NATS local data recreated from scratch.

## Logs

Follow all logs:

```bash
docker compose logs -f
```

Follow one service:

```bash
docker compose logs -f market-service
```

Show the latest NATS logs:

```bash
docker compose logs --tail=100 nats
```

Show logs for database startup and init scripts:

```bash
docker compose logs --tail=200 postgres
docker compose logs --tail=200 timescaledb
```

## Health and HTTP Debugging

Check service health endpoints from the host:

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

Check readiness endpoints:

```bash
curl http://localhost:8001/ready
curl http://localhost:8002/ready
```

Check NATS monitoring:

```bash
curl http://localhost:8222/healthz
curl http://localhost:8222/varz
```

## Running Tests

Run all tests inside a running service container:

```bash
docker compose exec market-service pytest /app/src/tests
```

Run a single test file:

```bash
docker compose exec market-service pytest /app/src/tests/test_event_contracts.py
```

Run one test by name:

```bash
docker compose exec market-service pytest /app/src/tests/test_event_contracts.py -k "market_tick"
```

Run tests with verbose output:

```bash
docker compose exec market-service pytest -vv /app/src/tests
```

Run syntax checks for shared modules:

```bash
docker compose exec market-service python -m py_compile \
  /app/src/shared/events/base.py \
  /app/src/shared/events/market.py \
  /app/src/shared/events/order.py \
  /app/src/shared/events/position.py \
  /app/src/shared/events/signal.py \
  /app/src/shared/events/system.py \
  /app/src/shared/nats_client.py
```

## NATS Debugging

Verify authenticated pub/sub using the project script:

```bash
docker compose exec market-service python /app/src/infrastructure/scripts/check_nats_pubsub.py
```

Inspect the NATS server config mounted into the container:

```bash
docker compose exec nats cat /etc/nats/nats-server.conf
```

Confirm the service environment contains the authenticated URL:

```bash
docker compose exec market-service env | grep NATS_URL
```

Publish/subscribe behavior is normally tested through `NatsClient.publish_event`, which publishes versioned subjects such as:

```text
v1.market.tick
v1.signal.generated
v1.order.submitted
v1.order.filled
v1.position.opened
v1.system.health
```

If a service cannot connect to NATS, check:

```bash
docker compose ps nats
docker compose logs --tail=100 nats
docker compose exec market-service env | grep NATS_URL
```

## PostgreSQL Debugging

Open a PostgreSQL shell:

```bash
docker compose exec postgres psql -U thewealth -d thewealth
```

List application tables:

```bash
docker compose exec postgres psql -U thewealth -d thewealth -c "\dt"
```

Describe a table:

```bash
docker compose exec postgres psql -U thewealth -d thewealth -c "\d orders"
```

Count rows in core tables:

```bash
docker compose exec postgres psql -U thewealth -d thewealth -c "SELECT COUNT(*) FROM users;"
docker compose exec postgres psql -U thewealth -d thewealth -c "SELECT COUNT(*) FROM events;"
```

Apply the app schema to an existing volume:

```bash
docker compose exec postgres psql -U thewealth -d thewealth -f /docker-entrypoint-initdb.d/001_app_schema.sql
```

## TimescaleDB Debugging

Open a TimescaleDB shell:

```bash
docker compose exec timescaledb psql -U thewealth -d market
```

List market tables:

```bash
docker compose exec timescaledb psql -U thewealth -d market -c "\dt"
```

Confirm hypertables:

```bash
docker compose exec timescaledb psql -U thewealth -d market -c "SELECT hypertable_name FROM timescaledb_information.hypertables;"
```

Describe a market table:

```bash
docker compose exec timescaledb psql -U thewealth -d market -c "\d candles"
```

Apply the market schema to an existing volume:

```bash
docker compose exec timescaledb psql -U thewealth -d market -f /docker-entrypoint-initdb.d/001_market_schema.sql
```

## Container Analysis

Show processes in a container:

```bash
docker top thewealth-market-service
```

Open a shell in a service container:

```bash
docker compose exec market-service sh
```

Inspect container metadata:

```bash
docker inspect thewealth-market-service
```

Inspect the Compose network:

```bash
docker network inspect thewealth-core_core
```

Inspect local volumes:

```bash
docker volume ls | grep thewealth-core
docker volume inspect thewealth-core_pgdata
docker volume inspect thewealth-core_tsdata
```

## Common Debug Flows

When a service is unhealthy:

```bash
docker compose ps
docker compose logs --tail=100 market-service
docker compose exec market-service env
curl http://localhost:8001/health
```

When NATS auth or pub/sub is suspect:

```bash
docker compose ps nats
docker compose logs --tail=100 nats
docker compose exec market-service env | grep NATS_URL
docker compose exec market-service python /app/src/infrastructure/scripts/check_nats_pubsub.py
```

When database tables are missing:

```bash
docker compose exec postgres psql -U thewealth -d thewealth -c "\dt"
docker compose exec timescaledb psql -U thewealth -d market -c "\dt"
docker compose exec postgres psql -U thewealth -d thewealth -f /docker-entrypoint-initdb.d/001_app_schema.sql
docker compose exec timescaledb psql -U thewealth -d market -f /docker-entrypoint-initdb.d/001_market_schema.sql
```

When the stack needs a fully clean database:

```bash
docker compose down -v
docker compose up -d --build
```

When a service was rebuilt but old code appears to run:

```bash
docker compose build market-service
docker compose up -d --force-recreate market-service
docker compose logs --tail=100 market-service
```
