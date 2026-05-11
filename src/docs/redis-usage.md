# Redis Cache Documentation

## Overview

Redis is deployed as a high-performance in-memory cache for the trading system. It handles:
- **Session Management**: User session data with automatic expiration
- **JWT Token Storage**: Token blacklist and validation
- **Temporary Cache**: Market data, calculation results, and transient state
- **Counters & Rate Limiting**: Request counting and rate limit enforcement

**Configuration:**
- Docker service: `thewealth-redis` (port 6379, volume: `redisdata`)
- Connection string: `redis://redis:6379`
- Available to all services via environment variable: `REDIS_URL`

---

## Quick Start

### 1. Access Redis from Services

All services automatically have Redis available through `app.state.redis`:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/example")
async def example(request: Request):
    redis = request.app.state.redis
    
    # Set a value
    await redis.set_key("my_key", "my_value", ttl=300)
    
    # Get a value
    value = await redis.get_key("my_key")
    return {"value": value}
```

### 2. Direct Client Usage

For scripts or standalone usage:

```python
from shared.redis_client import RedisClient

redis = RedisClient(url="redis://redis:6379")
await redis.connect()

# ... use redis ...

await redis.close()
```

---

## API Reference

### Session Management

**Store user session:**
```python
session_data = {
    "user_id": "user_123",
    "username": "alice",
    "permissions": ["read", "write"],
}
await redis.set_session("sess_abc123", session_data, ttl=3600)
```

**Retrieve session:**
```python
session = await redis.get_session("sess_abc123")
# Returns: {"user_id": "user_123", "username": "alice", ...}
```

**Delete session (logout):**
```python
await redis.delete_session("sess_abc123")
```

**TTL Options (default 3600s = 1 hour):**
- Short-lived: `ttl=300` (5 minutes) - for temporary sessions
- Standard: `ttl=3600` (1 hour) - typical web sessions
- Long-lived: `ttl=86400` (24 hours) - remember-me sessions

---

### JWT Token Management

**Store JWT token:**
```python
jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
user_id = "user_123"
await redis.set_jwt_token(jwt_token, user_id, ttl=86400)
```

**Validate JWT token:**
```python
user_id = await redis.get_jwt_token(jwt_token)
if user_id:
    # Token is valid (not blacklisted)
else:
    # Token is revoked or expired
```

**Revoke/blacklist JWT (logout):**
```python
await redis.delete_jwt_token(jwt_token)
```

**Use Case: Token Blacklist Strategy**
```python
# On token logout
await redis.delete_jwt_token(token)  # marks as revoked

# On token validation
user = await redis.get_jwt_token(token)
if not user:
    raise HTTPException(status_code=401, detail="Token revoked")
```

---

### Temporary Cache

**Store market data:**
```python
cache_key = "market_data:AAPL"
market_data = {
    "symbol": "AAPL",
    "price": 150.25,
    "volume": 1000000,
    "timestamp": time.time()
}
await redis.set_cache(cache_key, market_data, ttl=60)
```

**Retrieve cached data:**
```python
cached = await redis.get_cache("market_data:AAPL")
if cached:
    print(f"Using cached data: {cached}")
else:
    print("Cache miss - fetch from source")
```

**Clear cache:**
```python
await redis.delete_cache("market_data:AAPL")
```

**Typical TTL for Different Data:**
- Real-time prices: `ttl=30` (30 seconds) - frequently updated
- Market summaries: `ttl=300` (5 minutes) - slower change
- User preferences: `ttl=3600` (1 hour) - rarely changes
- Computed results: `ttl=600` (10 minutes) - medium-term cache

---

### Counter & Rate Limiting

**Increment counter:**
```python
count = await redis.increment("api_requests:user_123", 1)
print(f"Request count: {count}")
```

**Rate limiting example:**
```python
async def check_rate_limit(user_id: str, limit: int = 100, window: int = 60):
    """Allow 100 requests per minute per user"""
    key = f"rate_limit:{user_id}"
    current = await redis.increment(key, 1)
    
    if current == 1:
        # First request, set expiration
        await redis.expire(key, window)
    
    if current > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return current
```

---

### Generic Key Operations

**Set key with expiration:**
```python
await redis.set_key("key_name", {"data": "value"}, ttl=300)
```

**Get key (auto-parse JSON):**
```python
value = await redis.get_key("key_name")
```

**Check if key exists:**
```python
exists = await redis.exists("key_name")
```

**Delete key:**
```python
await redis.delete_key("key_name")
```

**Get remaining TTL (seconds):**
```python
ttl = await redis.ttl("key_name")
# Returns: seconds remaining, or -1 (no TTL), or -2 (doesn't exist)
```

**Set expiration on existing key:**
```python
success = await redis.expire("key_name", 600)
```

---

## Key Naming Conventions

Use hierarchical naming with colons for organization:

| Pattern | Purpose | Example |
|---------|---------|---------|
| `session:*` | User sessions | `session:sess_abc123` |
| `jwt:*` | JWT tokens | `jwt:eyJhbGc...` |
| `cache:*` | Temporary cache | `cache:market_data:AAPL` |
| `rate_limit:*` | Rate limits | `rate_limit:user_123` |
| `counter:*` | Counters | `counter:trades:daily` |

**Benefits:**
- Easy scoping with pattern matching
- Clear key organization
- Facilitates debugging and monitoring

---

## Common Patterns

### Pattern 1: Cached API Response

```python
@app.get("/market/price/{symbol}")
async def get_price(symbol: str, request: Request):
    redis = request.app.state.redis
    cache_key = f"cache:price:{symbol}"
    
    # Try cache first
    cached = await redis.get_cache(cache_key)
    if cached:
        return cached
    
    # Cache miss - fetch from source
    price_data = await fetch_price_from_broker(symbol)
    
    # Store in cache for 30 seconds
    await redis.set_cache(cache_key, price_data, ttl=30)
    
    return price_data
```

### Pattern 2: Session-Based Auth

```python
@app.post("/login")
async def login(credentials: Credentials, request: Request):
    redis = request.app.state.redis
    
    # Validate credentials
    user = validate_user(credentials)
    
    # Create session
    session_id = generate_session_id()
    session_data = {
        "user_id": user.id,
        "username": user.name,
        "permissions": user.permissions,
    }
    await redis.set_session(session_id, session_data, ttl=3600)
    
    return {"session_id": session_id}

@app.get("/protected")
async def protected_route(session_id: str, request: Request):
    redis = request.app.state.redis
    
    session = await redis.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return {"message": f"Hello {session['username']}"}
```

### Pattern 3: Distributed Rate Limiting

```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    redis = request.app.state.redis
    user_id = request.headers.get("X-User-ID", "anonymous")
    
    # Check rate limit: 1000 requests per 3600 seconds
    limit_key = f"rate_limit:{user_id}"
    count = await redis.increment(limit_key, 1)
    
    if count == 1:
        await redis.expire(limit_key, 3600)
    
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(1000 - count)
    
    if count > 1000:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
    
    return response
```

### Pattern 4: Order Processing with Caching

```python
@app.post("/orders")
async def place_order(order: Order, request: Request):
    redis = request.app.state.redis
    
    # Get cached market data
    cache_key = f"cache:market:{order.symbol}"
    market_data = await redis.get_cache(cache_key)
    
    if not market_data:
        market_data = await fetch_market_data(order.symbol)
        await redis.set_cache(cache_key, market_data, ttl=60)
    
    # Process order with current market data
    processed_order = process_order(order, market_data)
    
    # Cache order for quick retrieval
    order_cache_key = f"cache:order:{processed_order.id}"
    await redis.set_cache(order_cache_key, processed_order, ttl=300)
    
    return processed_order
```

---

## Testing

### Run Redis Connectivity Tests

From the project root:

```bash
docker-compose exec market-service python src/infrastructure/scripts/test_redis_connection.py
```

**Expected output:**
```
======================================================================
REDIS CONNECTIVITY TEST
======================================================================
[1/6] Testing basic connection...
✓ Successfully connected to Redis

[2/6] Testing basic set/get operations...
✓ Set/Get works: test_value

[3/6] Testing session storage...
✓ Session stored and retrieved: ...

[4/6] Testing JWT token storage...
✓ JWT token stored and retrieved: ...

[5/6] Testing temporary cache...
✓ Cache stored and retrieved: ...

[6/6] Testing counter operations...
✓ Counter operations working: ...

======================================================================
ALL TESTS PASSED ✓
======================================================================
```

### Manual Testing

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Ping Redis
> PING
PONG

# List all keys
> KEYS *

# Inspect a key
> GET session:sess_abc123

# Check memory usage
> INFO memory

# Monitor operations in real-time
> MONITOR
```

---

## Monitoring & Maintenance

### Health Check

Redis health is monitored via:
1. **Service health endpoint**: `/health` includes `redis_connected` status
2. **Docker health check**: Automatic ping every 10 seconds
3. **Application startup**: Services fail to start if Redis unavailable

### Storage Management

Redis uses in-memory storage with disk persistence (volume: `redisdata`).

**Monitor memory usage:**
```bash
docker-compose exec redis redis-cli INFO memory
```

**Common maintenance:**
```bash
# Clear all data (development only!)
docker-compose exec redis redis-cli FLUSHALL

# Clear specific database
docker-compose exec redis redis-cli FLUSHDB

# Persist data to disk
docker-compose exec redis redis-cli BGSAVE
```

### Backup & Recovery

```bash
# Backup Redis dump
docker cp thewealth-redis:/data/dump.rdb ./redis-backup.rdb

# Restore from backup
docker cp ./redis-backup.rdb thewealth-redis:/data/dump.rdb
docker-compose restart redis
```

---

## Performance Tips

1. **Batch Operations**: Group multiple operations into pipelines when possible
2. **Key Naming**: Use consistent hierarchical naming for easier scanning
3. **TTL Strategy**: Set appropriate TTLs to prevent memory bloat
4. **Connection Pooling**: RedisClient handles connection pooling automatically
5. **Error Handling**: Always wrap Redis operations in try/catch for resilience

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Redis connection refused" | Verify container running: `docker ps \| grep redis` |
| "NOAUTH Authentication required" | Check Redis password in config |
| "OOM command not allowed" | Redis out of memory - increase volume or clear old keys |
| "Connection timeout" | Check Redis service health: `docker logs thewealth-redis` |

---

## Integration Checklist

- [x] Redis container configured in docker-compose.yaml
- [x] Redis client library (redis-py) in requirements.txt
- [x] RedisClient module created with all operations
- [x] Service integration (app.state.redis available)
- [x] Health check endpoints updated
- [x] Connection test script created
- [x] Documentation complete (this file)

---

## References

- [Redis Documentation](https://redis.io/documentation)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [Redis Best Practices](https://redis.io/topics/client-side-caching)
