## Implement Deriv WebSocket Market Connector

Description

Build an async Python service that connects to Deriv's WebSocket API, subscribes to tick/candle streams for all supported symbols, and handles reconnects. Acceptance: service streams live ticks/candles for SYNTH and FX symbols.

Checklist

- [x] Connect to Deriv WS and authenticate
- [x] Subscribe to all required symbols
- [x] Handle reconnect and error cases
- [x] Document implementation

## Normalize and Publish Market Events via NATS

Description

Transform raw Deriv messages into internal event format (using event contracts), publish `market.tick` and `market.candle` events to NATS (versioned topics). Acceptance: events are published, versioned, and validated by contract.

Checklist

- [x] Map Deriv data to internal event schema
- [x] Publish events to NATS topics
- [x] Validate event structure and versioning
- [x] Document implementation

## Persist Market Data to TimescaleDB

Description

Write async handlers to store all ticks and candles in TimescaleDB, ensuring time-series indexing and retention policies. Acceptance: all received market data is persisted and queryable.

Checklist

- [x] Implement async DB writes for ticks/candles
- [x] Create indexes and retention policies
- [x] Verify data persistence with sample queries
- [x] Document implementation

## Setup Deriv API Credentials

Description

Configure proper Deriv App ID and API Token for reliable market data access. The demo credentials are rate-limited.

Checklist

- [x] Document Deriv API endpoints and WebSocket usage
- [x] Create setup script for credential configuration
- [x] Update environment configuration
- [ ] Obtain and configure personal Deriv App ID and API Token
- [x] Document implementation

## Notes

- Implementation details: `src/docs/market-service.md`
- Runtime and debugging commands: `src/docs/testing-and-debugging.md`
