from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

PREFIXES: dict[str, str] = {
    "user": "USR",
    "publisher": "PUB",
    "book": "BK",
    "kyc": "KYC",
    "download": "DL",
    "review": "REV",
}

_TABLE_MAP: dict[str, type] = {}


def _get_table_map() -> dict[str, type]:
    """Build the entity-type-to-model mapping lazily to avoid circular imports."""
    if not _TABLE_MAP:
        from app.db.models.book import Book
        from app.db.models.download import DownloadLog
        from app.db.models.kyc import KYCApplication
        from app.db.models.publisher import PublisherProfile
        from app.db.models.review import Review
        from app.db.models.user import User

        _TABLE_MAP.update(
            {
                "user": User,
                "publisher": PublisherProfile,
                "book": Book,
                "kyc": KYCApplication,
                "download": DownloadLog,
                "review": Review,
            }
        )
    return _TABLE_MAP


async def generate(entity_type: str, redis: Redis) -> str:
    """
    Atomically increment a Redis counter and return a formatted number.
    Counter is synced from DB row count on startup.
    """
    prefix = PREFIXES[entity_type]
    count = await redis.incr(f"counter:{entity_type}")
    return f"{prefix}-{str(count).zfill(6)}"  # USR-000001


async def sync_from_db(
    entity_type: str, db: AsyncSession, redis: Redis
) -> int:
    """Sync the Redis counter for entity_type with actual DB row count."""
    table_map = _get_table_map()
    model = table_map[entity_type]
    count = await db.scalar(select(func.count()).select_from(model))
    count = count or 0
    await redis.set(f"counter:{entity_type}", count)
    return count
