# Deriv API Integration Documentation

## Overview

The market-service connects to Deriv's WebSocket API to stream real-time market data (ticks and candles) for forex and synthetic index markets.

## WebSocket Connection

The current service supports both public and authenticated Deriv WebSocket endpoints.

**Public endpoint (no auth required):**
`wss://api.derivws.com/trading/v1/options/ws/public`

**Authenticated endpoint (optional):**
`wss://ws.derivws.com/websockets/v3?app_id={app_id}`

Where `{app_id}` is your Deriv application ID.

## Authentication

If `DERIV_API_TOKEN` is provided, the service authenticates using:

```json
{
  "authorize": "your_api_token_here"
}
```

## API Endpoints/Requests Used

### 1. Get Active Symbols
**Request:**
```json
{
  "active_symbols": "brief",
  "product_type": "basic"
}
```

**Response:** List of available trading symbols with market categories.

### 2. Subscribe to Tick Data
**Request:**
```json
{
  "ticks": "symbol_name",
  "subscribe": 1
}
```

**Response:** Real-time tick updates for the specified symbol.

### 3. Subscribe to Candle Data
**Request:**
```json
{
  "ticks_history": "symbol_name",
  "style": "candles",
  "granularity": 60,
  "end": "latest",
  "count": 1,
  "subscribe": 1
}
```

**Response:** Real-time candle updates for the specified symbol and granularity.

## Rate Limits

Deriv imposes rate limits on API calls. The demo app ID (1089) is heavily rate-limited and may not work reliably for production use.

## Configuration

Set the following environment variables:

```bash
# Use the public no-auth endpoint for market data
DERIV_WS_URL=wss://api.derivws.com/trading/v1/options/ws/public
DERIV_API_TOKEN=

# Optional authenticated endpoint if you have an app ID and token
# DERIV_APP_ID=your_app_id
# DERIV_WS_URL=wss://ws.derivws.com/websockets/v3?app_id=your_app_id
# DERIV_API_TOKEN=your_api_token

# Markets to filter (default: forex,synthetic_index)
DERIV_MARKETS=forex,synthetic_index

# Specific symbols to monitor (optional allowlist)
MARKET_SYMBOLS=frxEURUSD,R_100
```

### Avoid active_symbols rate limiting

If `MARKET_SYMBOLS` is set, the market-service will bypass the Deriv `active_symbols` discovery request and subscribe directly to the listed symbols. This is useful when the default discovery call is rate-limited.

## Getting Your Own App ID and API Token

1. **Create a Deriv Account:** Go to [deriv.com](https://deriv.com) and create an account.

2. **Get App ID:**
   - Visit the [Deriv API Dashboard](https://app.deriv.com/account/api-token)
   - Create a new app registration
   - Note the App ID provided

3. **Get API Token:**
   - In the API token section, create a new token
   - Select scopes: `read` (for market data)
   - Copy the generated token

4. **Update Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your DERIV_APP_ID and DERIV_API_TOKEN
   ```

## Testing Connection

After setting up credentials:

```bash
docker compose up -d --build
curl http://localhost:8001/market/status
```

Expected response should show `"provider_mode": "primary"` instead of `"fallback"`.

## Error Handling

The service includes automatic reconnection and fallback to synthetic data when Deriv is unavailable or rate-limited.</content>
<parameter name="filePath">/home/urangani/codeSpace/current/TheTradingSystem/the-wealth-core/src/docs/deriv-api.md