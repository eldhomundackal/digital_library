"""Redis cache helpers for book listings and detail pages."""

import json

from redis.asyncio import Redis

DEFAULT_TTL = 300  # 5 minutes


async def get_cached(redis: Redis, key: str) -> dict | None:
    """Get JSON value from Redis. Returns None if key missing."""
    value = await redis.get(key)
    if value is None:
        return None
    return json.loads(value)


async def set_cached(redis: Redis, key: str, value: dict, ttl: int = DEFAULT_TTL) -> None:
    """Store JSON value in Redis with TTL in seconds."""
    await redis.set(key, json.dumps(value), ex=ttl)


async def invalidate(redis: Redis, key: str) -> None:
    """Delete a single cache key."""
    await redis.delete(key)


async def invalidate_pattern(redis: Redis, pattern: str) -> None:
    """Delete all keys matching pattern (e.g. 'cache:books:*')."""
    cursor = 0
    while True:
        cursor, keys = await redis.scan(cursor, match=pattern, count=100)
        if keys:
            await redis.delete(*keys)
        if cursor == 0:
            break
