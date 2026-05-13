#!/usr/bin/env python3
"""
Redis connectivity test script.
Tests basic Redis operations: set/get, sessions, JWT tokens, and cache.
"""

import asyncio
import sys
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, "/app/src")

from shared.redis_client import RedisClient


async def main():
    print("=" * 70)
    print("REDIS CONNECTIVITY TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    redis = RedisClient(url="redis://redis:6379")

    try:
        # Test connection
        print("[1/6] Testing basic connection...")
        await redis.connect()
        print("✓ Successfully connected to Redis\n")

        # Test basic set/get
        print("[2/6] Testing basic set/get operations...")
        await redis.set_key("test_key", "test_value", ttl=60)
        value = await redis.get_key("test_key")
        assert value == "test_value", f"Expected 'test_value', got {value}"
        print(f"✓ Set/Get works: {value}\n")

        # Test session operations
        print("[3/6] Testing session storage...")
        session_data = {
            "user_id": "user_123",
            "username": "test_user",
            "permissions": ["read", "write"],
            "created_at": datetime.now().isoformat(),
        }
        session_id = "sess_abc123"
        await redis.set_session(session_id, session_data, ttl=3600)
        retrieved_session = await redis.get_session(session_id)
        assert retrieved_session == session_data, "Session data mismatch"
        print(f"✓ Session stored and retrieved:\n  Session ID: {session_id}")
        print(f"  User: {retrieved_session['username']}\n")

        # Test JWT token operations
        print("[4/6] Testing JWT token storage...")
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyJ9.test"
        user_id = "user_123"
        await redis.set_jwt_token(jwt_token, user_id, ttl=86400)
        retrieved_user = await redis.get_jwt_token(jwt_token)
        assert retrieved_user == user_id, "JWT token data mismatch"
        print("✓ JWT token stored and retrieved:")
        print(f"  Token: {jwt_token[:50]}...")
        print(f"  User ID: {retrieved_user}\n")

        # Test cache operations
        print("[5/6] Testing temporary cache...")
        cache_key = "market_data"
        cache_data = {"symbol": "AAPL", "price": 150.25, "timestamp": time.time()}
        await redis.set_cache(cache_key, cache_data, ttl=300)
        retrieved_cache = await redis.get_cache(cache_key)
        assert retrieved_cache["symbol"] == cache_data["symbol"], "Cache data mismatch"
        print("✓ Cache stored and retrieved:")
        print(f"  Key: {cache_key}")
        print(f"  Data: {retrieved_cache}\n")

        # Test counter operations
        print("[6/6] Testing counter operations...")
        counter_key = "request_count"
        initial_count = await redis.increment(counter_key, 1)
        assert initial_count == 1, f"Expected count 1, got {initial_count}"
        incremented_count = await redis.increment(counter_key, 5)
        assert incremented_count == 6, f"Expected count 6, got {incremented_count}"
        print("✓ Counter operations working:")
        print(f"  Initial: 1, After +5: {incremented_count}\n")

        # Test key expiration
        print("[BONUS] Testing key expiration...")
        temp_key = "temporary_data"
        await redis.set_key(temp_key, "will_expire", ttl=2)
        await redis.expire(temp_key, 1)  # Reduce TTL to 1 second
        ttl = await redis.ttl(temp_key)
        print(f"✓ TTL set successfully: {ttl} second(s) remaining\n")

        print("=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
        print("\nRedis is ready for:")
        print("  • Session management")
        print("  • JWT token storage")
        print("  • Temporary cache storage")
        print("  • Counter/rate limiting")
        print("  • Any key-value operations")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify Redis container is running: docker ps | grep redis")
        print("  2. Check Redis is accessible: redis-cli -h redis ping")
        print("  3. Review Redis logs: docker logs thewealth-redis")
        sys.exit(1)
    finally:
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
