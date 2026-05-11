#!/usr/bin/env bash
set -euo pipefail

docker compose exec postgres pg_isready -U thewealth -d thewealth
docker compose exec timescaledb pg_isready -U thewealth -d market
docker compose exec redis redis-cli ping
docker compose exec market-service python -c "import socket; socket.create_connection(('nats', 4222), timeout=2).close()"
docker compose exec execution-service python -c "import socket; socket.create_connection(('postgres', 5432), timeout=2).close()"
docker compose exec strategy-service python -c "import socket; socket.create_connection(('timescaledb', 5432), timeout=2).close()"
docker compose exec analytics-service python -c "import socket; socket.create_connection(('redis', 6379), timeout=2).close()"
docker compose exec gateway-service python -c "import urllib.request; urllib.request.urlopen('http://market-service:8000/health', timeout=2)"

echo "Core infrastructure connectivity checks passed."
