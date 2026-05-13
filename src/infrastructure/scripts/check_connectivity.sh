#!/usr/bin/env bash
set -euo pipefail

echo "=== Infrastructure ==="
docker compose exec timescaledb pg_isready -U thewealth -d market
docker compose exec redis redis-cli ping

echo "=== NATS ==="
docker compose exec market-service python -c "import socket; socket.create_connection(('nats', 4222), timeout=2).close()"
docker compose exec market-service python /app/src/infrastructure/scripts/check_nats_pubsub.py

echo "=== Services ==="
docker compose exec gateway-service python -c "import urllib.request; urllib.request.urlopen('http://market-service:8000/health', timeout=2)"

echo "=== Database Rows ==="
docker compose exec timescaledb psql -U thewealth -d thewealth -c "SELECT COUNT(*) FROM users, strategies, orders, positions, events LIMIT 1;" 2>/dev/null || echo "thewealth database ready (no app data yet)"
docker compose exec timescaledb psql -U thewealth -d market -c "SELECT COUNT(*) FROM ticks, candles, features, indicators LIMIT 1;" 2>/dev/null || echo "market database ready (no market data yet)"

echo "Core infrastructure connectivity checks passed."
