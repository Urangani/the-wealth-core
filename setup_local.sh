#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_ROOT}"

# ── Colors ──────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# ── 1. Python virtual environment ───────────────────────────────
if [ ! -d .venv ]; then
    info "Creating Python virtual environment..."
    python3 -m venv .venv
    ok "Virtual environment created at .venv/"
else
    ok ".venv/ already exists"
fi

source .venv/bin/activate

info "Installing/updating dependencies..."
pip install -q --upgrade pip
pip install -r requirements.txt
ok "Dependencies installed"

# ── 2. .env file ────────────────────────────────────────────────
if [ ! -f .env ]; then
    info "Creating .env from .env.example with localhost URLs..."
    cat > .env << 'ENVEOF'
NATS_URL=nats://thewealth:thewealth_nats@localhost:4222
POSTGRES_URL=postgresql://thewealth:thewealth@localhost:15432/thewealth
TIMESCALE_URL=postgresql://thewealth:thewealth@localhost:5433/market
REDIS_URL=redis://localhost:6379

DERIV_APP_ID=1089
DERIV_WS_URL=wss://ws.derivws.com/websockets/v3?app_id=1089
DERIV_API_TOKEN=
DERIV_MARKETS=forex,synthetic_index
MARKET_SYMBOLS=
MARKET_CANDLE_GRANULARITIES=60
MARKET_RECONNECT_DELAY_SECONDS=3

MARKET_FALLBACK_ENABLED=true
MARKET_FALLBACK_INTERVAL_SECONDS=1
FALLBACK_MARKET_SYMBOLS=frxEURUSD,R_100

MARKET_BATCH_FLUSH_SIZE=200
MARKET_BATCH_FLUSH_INTERVAL_SECONDS=1
MARKET_TICK_RETENTION_DAYS=30
MARKET_CANDLE_RETENTION_DAYS=180
ENVEOF
    ok ".env created with localhost URLs"
else
    ok ".env already exists"
fi

# ── 3. Infrastructure health ────────────────────────────────────
info "Checking infrastructure reachability..."

nats_ok=false
if command -v nats-server &>/dev/null; then
    nats_ok=true
elif docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'thewealth-infra.*nats'; then
    nats_ok=true
fi
$nats_ok && ok "NATS reachable" || warn "NATS not detected — start it with:  docker compose -f docker-compose.infra.yaml up -d nats"

pg_ok=false
if pg_isready -h localhost -p 15432 -U thewealth &>/dev/null; then
    pg_ok=true
fi
$pg_ok && ok "PostgreSQL reachable at localhost:15432" || warn "PostgreSQL not detected — start with:  docker compose -f docker-compose.infra.yaml up -d postgres"

ts_ok=false
if pg_isready -h localhost -p 5433 -U thewealth &>/dev/null; then
    ts_ok=true
fi
$ts_ok && ok "TimescaleDB reachable at localhost:5433" || warn "TimescaleDB not detected — start with:  docker compose -f docker-compose.infra.yaml up -d timescaledb"

redis_ok=false
if command -v redis-cli &>/dev/null && redis-cli -h localhost -p 6379 ping 2>/dev/null; then
    redis_ok=true
elif docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'thewealth-infra.*redis'; then
    redis_ok=true
fi
$redis_ok && ok "Redis reachable" || warn "Redis not detected — start it with:  docker compose -f docker-compose.infra.yaml up -d redis"

# ── 4. PYTHONPATH helper ────────────────────────────────────────
info "Setting up PYTHONPATH persistence..."
ACTIVATE_FILE=".venv/bin/activate"
if ! grep -q 'PYTHONPATH' "$ACTIVATE_FILE" 2>/dev/null; then
    cat >> "$ACTIVATE_FILE" << 'PYEOF'

# The Wealth Core: set PYTHONPATH=src for imports
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}${VIRTUAL_ENV}/../src"
PYEOF
    ok "PYTHONPATH=src appended to .venv/bin/activate"
else
    ok "PYTHONPATH already set in .venv/bin/activate"
fi

# ── 5. Summary ──────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "  ${GREEN}Local dev environment ready!${NC}"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Next steps:"
echo "    1. source .venv/bin/activate"
echo "    2. docker compose -f docker-compose.infra.yaml up -d"
echo "    3. pytest src/tests -v"
echo "    4. uvicorn main:app --reload --port 8001 --app-dir src/services/market-service"
echo ""
echo "  Full docs: src/docs/local-development.md"
echo "═══════════════════════════════════════════════════════════"
