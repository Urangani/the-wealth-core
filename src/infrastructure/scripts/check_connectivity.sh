#!/usr/bin/env bash
set -euo pipefail

docker compose exec postgres pg_isready -U thewealth -d thewealth
docker compose exec timescaledb pg_isready -U thewealth -d market
docker compose exec redis redis-cli ping
docker compose exec market-service python -c "import socket; socket.create_connection(('nats', 4222), timeout=2).close()"
docker compose exec market-service python /app/src/infrastructure/scripts/check_nats_pubsub.py
docker compose exec execution-service python -c "import socket; socket.create_connection(('postgres', 5432), timeout=2).close()"
docker compose exec strategy-service python -c "import socket; socket.create_connection(('timescaledb', 5432), timeout=2).close()"
docker compose exec analytics-service python -c "import socket; socket.create_connection(('redis', 6379), timeout=2).close()"
docker compose exec gateway-service python -c "import urllib.request; urllib.request.urlopen('http://market-service:8000/health', timeout=2)"
docker compose exec postgres psql -U thewealth -d thewealth -c "SELECT COUNT(*) FROM users, strategies, orders, positions, events LIMIT 1;"
docker compose exec timescaledb psql -U thewealth -d market -c "SELECT COUNT(*) FROM ticks, candles, features, indicators LIMIT 1;"

echo "Core infrastructure connectivity checks passed."
