## Provision and Secure NATS Event Bus

Description

Deploy NATS in Docker with versioned topics and authentication enabled. Document pub/sub usage model. Acceptance: NATS is reachable, supports pub/sub, and enforces auth.

Checklist

[x] Deploy NATS container with config

[x] Enable NATS authentication

[x] Test pub/sub from Python client

[x] documentation

## Set Up PostgreSQL and TimescaleDB

Description

Deploy PostgreSQL and TimescaleDB in Docker. Create initial schemas for users, strategies, orders, positions, events, ticks, candles, features, indicators. Acceptance: DBs are reachable, schemas are created, and tables can be queried.

Checklist

[x] Deploy PostgreSQL and TimescaleDB containers

[x] Write and apply schema migrations

[x] Verify table creation and connectivity

[x] documentation

## Implement Base Event Contracts

Description

Define Pydantic schemas for all core events (market.tick, signal.generated, order.submitted, order.filled, position.opened, etc.) in a shared package. Version schemas and ensure importable by all services. Acceptance: Schemas are validated, versioned, and imported in tests.

Checklist

[x] Write Pydantic models for all event types

[x] Publish shared package for import

[x] Test event serialization/deserialization

[x] documentation
