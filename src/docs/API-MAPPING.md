# Deriv API Endpoint Mapping

> Scanned from `src/docs/deriv-server-api.md` — all 28 endpoints classified, with consumption mapping for our FastAPI + WebSocket server.

---

## Legend

| Column | Meaning |
|--------|---------|
| **Endpoint** | WS action key or REST path |
| **Method** | WS message key / REST verb |
| **Auth** | Required / Not required (+ note) |
| **Type** | WebSocket or REST |
| **Payload** | Request → Response schema |
| **Consumption** | How our backend uses it |

---

## 1. WebSocket — Account Management (5 endpoints)

| Endpoint | Method | Auth | Type | Payload | Consumption |
|----------|--------|------|------|---------|-------------|
| `balance` | `balance: 1` | Required | WebSocket | Req: `{"balance":1, "subscribe":1}` → Res: `{"balance":{"balance":10092.59,"currency":"USD","loginid":"VRTC965733"}}` | `deriv_connector.py` subscribes on startup, publishes `v1.account.balance` to NATS for `execution-service` to consume |
| `portfolio` | `portfolio: 1` | Required | WebSocket | Req: `{"portfolio":1}` → Res: `{"portfolio":{"contracts":[{"contract_id":...,"contract_type":"CALL"}]}}` | Exposed via FastAPI route → calls WS → returns JSON. Cached in Redis with 30s TTL. |
| `profit_table` | `profit_table: 1` | Required | WebSocket | Req: `{"profit_table":1,"limit":25,"offset":0}` → Res: `{"profit_table":{...}}` | FastAPI route → WS request → JSON response. Used by analytics service for P&L reporting. |
| `statement` | `statement: 1` | Required | WebSocket | Req: `{"statement":1,"description":1,"limit":100}` → Res: `{"statement":{...}}` | FastAPI route → WS request → paginated JSON. Published to NATS `v1.account.statement` for audit logging. |
| `transaction` | `transaction: 1` | Required | WebSocket | Req: `{"transaction":1,"subscribe":1}` → Res: stream of `{"transaction":{...}}` | Subscription handler in `deriv_connector.py` → publishes `v1.account.transaction` to NATS. `execution-service` consumes to update order/position state. |

---

## 2. WebSocket — Market Data (5 endpoints)

| Endpoint | Method | Auth | Type | Payload | Consumption |
|----------|--------|------|------|---------|-------------|
| `active_symbols` | `active_symbols: "brief"` | Not required | WebSocket | Req: `{"active_symbols":"brief"}` → Res: `{"active_symbols":[{"underlying_symbol":"1HZ100V",...}]}` | Called once at `market-service` startup. Cached in Redis (key: `market:active_symbols`, TTL: 1h). Returned by `GET /market/symbols`. |
| `contracts_for` | `contracts_for: "1HZ100V"` | Not required | WebSocket | Req: `{"contracts_for":"1HZ100V"}` → Res: `{"contracts_for":{...}}` | FastAPI route `GET /market/contracts/{symbol}` → WS request → JSON. Cached in Redis per symbol (TTL: 30min). |
| `contracts_list` | `contracts_list: 1` | Not required | WebSocket | Req: `{"contracts_list":1}` → Res: `{"contracts_list":[{"contract_category":"callput","contract_types":["CALL","PUT"]}]}` | Called once at startup. Cached in Redis (TTL: 1h). Used by gateway to populate contract type dropdowns. |
| `ticks` | `ticks: "1HZ100V"` | Not required | WebSocket | Req: `{"ticks":"1HZ100V","subscribe":1}` → Res: stream of `{"tick":{"ask":...,"bid":...,"epoch":...,"symbol":"1HZ100V"}}` | **Already implemented** in `deriv_connector.py`. Subscribes per symbol, normalizes in `normalization.py`, publishes `v1.market.tick` to NATS, persists to TimescaleDB `ticks` hypertable. |
| `ticks_history` | `ticks_history: "1HZ100V"` | Not required | WebSocket | Req: `{"ticks_history":"1HZ100V","end":"latest","count":100,"style":"ticks"}` → Res: `{"history":{"prices":[...],"times":[...]}}` | FastAPI route `GET /market/history/{symbol}` → WS request → JSON. Falls back to TimescaleDB query if Deriv unavailable. Supports `style: "candles"` with `granularity` param. |

---

## 3. WebSocket — Trading Operations (7 endpoints)

| Endpoint | Method | Auth | Type | Payload | Consumption |
|----------|--------|------|------|---------|-------------|
| `proposal` | `proposal: 1` | Not required* | WebSocket | Req: `{"proposal":1,"contract_type":"CALL","amount":100,"duration":5,"underlying_symbol":"1HZ100V"}` → Res: `{"proposal":{"id":"abc123","ask_price":10.50,"payout":19.90}}` | FastAPI route `POST /trade/proposal` → WS request → JSON. *Auth needed for personalized pricing — pass token if available. Published to NATS `v1.trade.proposal` for strategy evaluation. |
| `buy` | `buy: "proposal_id"` | Required | WebSocket | Req: `{"buy":"abc123xyz","price":10.50}` → Res: `{"buy":{"contract_id":12345678,"balance_after":10082.09,"buy_price":10.50}}` | FastAPI route `POST /trade/buy` (auth-gated) → WS request → JSON. Only `execution-service` can issue via NATS `v1.order.submitted`. |
| `sell` | `sell: 12345678` | Required | WebSocket | Req: `{"sell":12345678,"price":0}` → Res: `{"sell":{"contract_id":12345678,"sold_for":15.00,"balance_after":10097.09}}` | FastAPI route `POST /trade/sell/{contract_id}` (auth-gated) → WS request → JSON. Published to NATS `v1.order.filled`. |
| `proposal_open_contract` | `proposal_open_contract: 1` | Required | WebSocket | Req: `{"proposal_open_contract":1,"contract_id":12345678,"subscribe":1}` → Res: stream of `{"proposal_open_contract":{"profit":...,"status":"open"}}` | Subscription in `execution-service` → publishes `v1.position.updated` to NATS. Used by `strategy-service` for exit decisions. |
| `contract_update` | `contract_update: 1` | Required | WebSocket | Req: `{"contract_update":1,"contract_id":12345678,"limit_order":{"stop_loss":5,"take_profit":15}}` → Res: `{"contract_update":{"contract_id":12345678,...}}` | FastAPI route `PATCH /trade/contract/{contract_id}` (auth-gated) → WS request → JSON. |
| `contract_update_history` | `contract_update_history: 1` | Required | WebSocket | Req: `{"contract_update_history":1,"contract_id":12345678}` → Res: `{"contract_update_history":{...}}` | FastAPI route `GET /trade/contract/{contract_id}/updates` → WS request → JSON. |
| `cancel` | `cancel: 12345678` | Required | WebSocket | Req: `{"cancel":12345678}` → Res: `{"cancel":{"contract_id":12345678,...}}` | FastAPI route `POST /trade/contract/{contract_id}/cancel` (auth-gated) → WS request → JSON. |

> *`proposal`: No Auth for public pricing, but Auth required for personalized pricing (your balance, existing positions).

---

## 4. WebSocket — Subscription Management (2 endpoints)

| Endpoint | Method | Auth | Type | Payload | Consumption |
|----------|--------|------|------|---------|-------------|
| `forget` | `forget: "sub_id"` | Not required | WebSocket | Req: `{"forget":"abc123subscription"}` → Res: `{"forget":"abc123subscription","msg_type":"forget"}` | Called internally by `deriv_connector.py` on unsubscribe. Exposed as FastAPI route `DELETE /market/subscription/{sub_id}` for manual management. |
| `forget_all` | `forget_all: ["ticks"]` | Not required | WebSocket | Req: `{"forget_all":["ticks","proposal"]}` → Res: `{"forget_all":["ticks","proposal"],"msg_type":"forget_all"}` | Called on graceful shutdown of `market-service` to clean up all subscriptions. |

---

## 5. WebSocket — System (3 endpoints)

| Endpoint | Method | Auth | Type | Payload | Consumption |
|----------|--------|------|------|---------|-------------|
| `ping` | `ping: 1` | Not required | WebSocket | Req: `{"ping":1}` → Res: `{"ping":"pong","msg_type":"ping"}` | `deriv_connector.py` sends ping every 30s. If no pong within 10s, triggers reconnect. |
| `time` | `time: 1` | Not required | WebSocket | Req: `{"time":1}` → Res: `{"time":1234567890,"msg_type":"time"}` | Called on connection open to sync server time offset. Used for timestamp normalization in `normalization.py`. |
| `trading_times` | `trading_times: "today"` | Not required | WebSocket | Req: `{"trading_times":"today"}` → Res: `{"trading_times":{"markets":[...]}}` | Called daily at startup. Cached in Redis (TTL: 6h). Returned by `GET /market/trading-times`. |

---

## 6. REST — Options Account Management (5 endpoints)

| Endpoint | Method | Auth | Type | Payload | Consumption |
|----------|--------|------|------|---------|-------------|
| `GET /trading/v1/options/accounts` | GET | Required (OAuth2) | REST | Header: `Deriv-App-ID`, `Authorization: Bearer` → Res: `{"data":[{"account_id":"DOT90004580","balance":10000,"account_type":"demo"}]}` | FastAPI route `GET /deriv/accounts` → `httpx.AsyncClient` GET → JSON. Cached in Redis (TTL: 5min). Only `gateway` service calls this. |
| `POST /trading/v1/options/accounts` | POST | Required (OAuth2) | REST | Body: `{"currency":"USD","group":"row","account_type":"demo"}` → Res: `{"data":[{"account_id":"DOT90004580",...}]}` | FastAPI route `POST /deriv/accounts` → `httpx.AsyncClient` POST → JSON. Used by onboarding flow in `gateway`. |
| `POST /trading/v1/options/accounts/{id}/reset-demo-balance` | POST | Required | REST | Path: `account_id` → Res: `{"data":{"balance":10000,"account_type":"demo"}}` | FastAPI route `POST /deriv/accounts/{id}/reset` → httpx POST. Only for demo accounts. |
| `POST /trading/v1/options/accounts/{id}/otp` | POST | Required | REST | Path: `accountId` → Res: `{"data":{"url":"wss://...?otp=..."}}` | Called by `execution-service` before establishing an authenticated WS connection. Returns the OTP URL for the trading WS. |
| `GET /trading/v1/options/ws/public` | GET | Not required | REST (WS upgrade) | No body → 101 Switching Protocols → WebSocket | **Currently used** by `deriv_connector.py` as the primary connection for public market data. |

---

## 7. REST — System Health (1 endpoint)

| Endpoint | Method | Auth | Type | Payload | Consumption |
|----------|--------|------|------|---------|-------------|
| `GET /v1/health` | GET | Not required | REST | No params → Res: `{"status":"ok","timestamp":"2025-01-15T10:30:00Z"}` | Called by our connectivity checker `src/infrastructure/scripts/check_connectivity.sh` to verify Deriv API is reachable. |

---

## 8. OAuth Endpoints (2 endpoints, auth infrastructure)

| Endpoint | Method | Auth | Type | Payload | Consumption |
|----------|--------|------|------|---------|-------------|
| `GET https://auth.deriv.com/oauth2/auth` | GET (redirect) | User interaction | OAuth | Query: `response_type=code&client_id=...&scope=trade&code_challenge=...` → redirects to `redirect_uri?code=...` | `gateway` service redirects users here for login/signup. PKCE flow managed server-side. |
| `POST https://auth.deriv.com/oauth2/token` | POST | `client_id` + `code_verifier` | OAuth | Body: `grant_type=authorization_code&code=...&code_verifier=...` → Res: `{"access_token":"ory_at_...","expires_in":3600}` | FastAPI route `POST /auth/deriv/callback` exchanges auth code for token. Token stored in Redis (hashed) and used for all authenticated Deriv calls. |

---

## Summary Tallies

| Category | Count | Details |
|----------|-------|---------|
| **Total endpoints** | **28** | 22 WS + 6 REST (excluding 2 OAuth infra endpoints) |
| **WebSocket** | **22** | 5 Account + 5 Market Data + 7 Trading + 2 Subscription + 3 System |
| **REST** | **6** | 5 Account Management + 1 Health |
| **OAuth** | **2** | Authorization + Token exchange (infrastructure) |
| **Auth required** | **15** | 5 Account WS + 7 Trading WS + 3 REST accounts (list, create, reset) |
| **No auth** | **13** | 5 Market Data WS + 1 Trading WS (`proposal`*) + 2 Subscription WS + 3 System WS + 1 REST public WS + 1 REST health |
| **Subscription (streaming)** | **5** | balance, ticks, transaction, proposal, proposal_open_contract |

## Implementation Status

| Status | Count | Endpoints |
|--------|-------|-----------|
| **Already implemented** | 2 | `ticks` (via `deriv_connector.py`), `ticks_history` (falls back to TimescaleDB) |
| **Needs connector work** | 10 | `balance`, `portfolio`, `profit_table`, `statement`, `transaction`, `active_symbols`, `contracts_for`, `contracts_list`, `trading_times`, `time` (partial — used on connect) |
| **Needs auth + execution** | 9 | `proposal`, `buy`, `sell`, `proposal_open_contract`, `contract_update`, `contract_update_history`, `cancel`, all 2 OAuth endpoints |
| **Infrastructure** | 7 | All REST account management, `ping`, `forget`, `forget_all`, `health` |
