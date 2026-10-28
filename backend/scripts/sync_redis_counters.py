"""
Syncs Redis number generator counters with actual DB row counts.
Run after:
- First deployment (before seed_superadmin)
- Redis flush or restart
- Data migration that inserted rows bypassing the app
Also called automatically at app startup via lifespan.
"""

import asyncio

import redis.asyncio as aioredis

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.utils.number_generator import sync_from_db

ENTITY_TYPES = ["user", "publisher", "book", "kyc", "download", "review"]


async def sync_all() -> None:
    """Sync all entity type counters from DB into Redis."""
    redis_client = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    async with AsyncSessionLocal() as db:
        for entity_type in ENTITY_TYPES:
            count = await sync_from_db(entity_type, db, redis_client)
            print(f"  {entity_type}: counter set to {count}")
    await redis_client.aclose()
    print("Redis counters synced.")


asyncio.run(sync_all())
