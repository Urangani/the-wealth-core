from typing import Any
from urllib.parse import urlparse

import redis


class RedisClient:
    """Client for Redis cache operations supporting session, JWT, and temp cache."""

    def __init__(self, url: str = "redis://localhost:6379"):
        self.url = url
        self.client: redis.Redis | None = None
        self._parse_url()

    def _parse_url(self) -> None:
        """Parse Redis URL and initialize connection parameters."""
        parsed = urlparse(self.url)
        self.host = parsed.hostname or "localhost"
        self.port = parsed.port or 6379
        self.db = int(parsed.path.lstrip("/")) if parsed.path else 0
        self.password = parsed.password

    async def connect(self) -> None:
        """Connect to Redis server."""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            # Test connection
            self.client.ping()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis at {self.url}: {e}") from e

    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            self.client.close()

    @property
    def is_connected(self) -> bool:
        """Check if Redis client is connected."""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    # Session operations
    async def set_session(self, session_id: str, data: dict[str, Any], ttl: int = 3600) -> None:
        """Store session data with TTL (default 1 hour)."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        import json

        self.client.setex(f"session:{session_id}", ttl, json.dumps(data))

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve session data."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        import json

        data = self.client.get(f"session:{session_id}")
        return json.loads(data) if data else None

    async def delete_session(self, session_id: str) -> None:
        """Delete session data."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        self.client.delete(f"session:{session_id}")

    # JWT operations
    async def set_jwt_token(self, token: str, user_id: str, ttl: int = 86400) -> None:
        """Store JWT token blacklist/validation data with TTL (default 24 hours)."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        self.client.setex(f"jwt:{token}", ttl, user_id)

    async def get_jwt_token(self, token: str) -> str | None:
        """Retrieve JWT token validation data."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return self.client.get(f"jwt:{token}")

    async def delete_jwt_token(self, token: str) -> None:
        """Delete JWT token (revoke)."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        self.client.delete(f"jwt:{token}")

    # Temporary cache operations
    async def set_cache(self, key: str, value: Any, ttl: int = 300) -> None:
        """Store temporary cache data with TTL (default 5 minutes)."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        import json

        if not isinstance(value, str):
            value = json.dumps(value)
        self.client.setex(f"cache:{key}", ttl, value)

    async def get_cache(self, key: str) -> Any | None:
        """Retrieve temporary cache data."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        import json

        data = self.client.get(f"cache:{key}")
        if not data:
            return None
        try:
            return json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return data

    async def delete_cache(self, key: str) -> None:
        """Delete cache entry."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        self.client.delete(f"cache:{key}")

    # Generic operations
    async def set_key(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a key with optional TTL."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        import json

        if not isinstance(value, str):
            value = json.dumps(value)
        if ttl:
            self.client.setex(key, ttl, value)
        else:
            self.client.set(key, value)

    async def get_key(self, key: str) -> Any | None:
        """Get a key value."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        import json

        data = self.client.get(key)
        if not data:
            return None
        try:
            return json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return data

    async def delete_key(self, key: str) -> None:
        """Delete a key."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return bool(self.client.exists(key))

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return self.client.incrby(key, amount)

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on a key."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return bool(self.client.expire(key, ttl))

    async def ttl(self, key: str) -> int:
        """Get TTL of a key in seconds. Returns -1 if key exists but has no TTL, -2 if key doesn't exist."""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return self.client.ttl(key)
