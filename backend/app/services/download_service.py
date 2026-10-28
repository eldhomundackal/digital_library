"""Download service — pre-signed URL generation, rate limiting, history."""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.book import Book, BookVersion
from app.db.models.download import DownloadLog
from app.db.models.user import User
from app.schemas.download import (
    BookFileSummary,
    DownloadLimits,
    DownloadResponse,
)
from app.schemas.common import PaginatedResponse
from app.storage.base import BaseStorageProvider
from app.utils.number_generator import generate
from app.utils.pagination import compute_pages


DOWNLOAD_URL_TTL = 600  # 10 minutes


class DownloadService:
    """Handles download URL generation with rate limiting and history."""

    def __init__(
        self,
        db: AsyncSession,
        storage: BaseStorageProvider | None,
        redis: Redis | None = None,
    ) -> None:
        """Initialise with DB session, storage provider, and Redis."""
        self.db = db
        self.storage = storage
        self.redis = redis

    async def generate_download_url(
        self, book_uuid: str, user: User
    ) -> DownloadResponse:
        """Generate a pre-signed download URL with rate limit enforcement."""
        from app.core.config import settings

        book_result = await self.db.execute(
            select(Book).where(Book.uuid == book_uuid, Book.is_active.is_(True))
        )
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        version_result = await self.db.execute(
            select(BookVersion).where(
                BookVersion.id == book.current_version_id,
                BookVersion.status == "APPROVED",
            )
        )
        version = version_result.scalar_one_or_none()
        if not version:
            raise HTTPException(
                status_code=404, detail="No approved version available."
            )

        if self.redis:
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            month_str = datetime.now(timezone.utc).strftime("%Y-%m")
            daily_key = f"download:daily:{user.id}:{book.id}:{today_str}"
            monthly_key = f"download:monthly:{user.id}:{book.id}:{month_str}"
            lock_key = f"download:active:{user.id}:{book.id}"

            lock = await self.redis.get(lock_key)
            if lock:
                raise HTTPException(
                    status_code=429,
                    detail="A download is already in progress for this book.",
                )

            max_daily = getattr(settings, "MAX_DOWNLOADS_PER_DAY", 5)
            max_monthly = getattr(settings, "MAX_DOWNLOADS_PER_MONTH", 15)

            daily_count = int(await self.redis.get(daily_key) or 0)
            monthly_count = int(await self.redis.get(monthly_key) or 0)

            if daily_count >= max_daily:
                raise HTTPException(
                    status_code=429, detail="Daily download limit reached."
                )
            if monthly_count >= max_monthly:
                raise HTTPException(
                    status_code=429, detail="Monthly download limit reached."
                )

            await self.redis.set(lock_key, "1", ex=DOWNLOAD_URL_TTL)
            await self.redis.incr(daily_key)
            await self.redis.expire(daily_key, 86400)
            await self.redis.incr(monthly_key)
            await self.redis.expire(monthly_key, 86400 * 31)

            daily_remaining = max_daily - daily_count - 1
            monthly_remaining = max_monthly - monthly_count - 1
        else:
            daily_remaining = 5
            monthly_remaining = 15

        if self.storage:
            download_url = await self.storage.generate_presigned_url(
                version.pdf_file, DOWNLOAD_URL_TTL
            )
        else:
            download_url = version.pdf_file

        import redis.asyncio as aioredis
        from app.core.config import settings as _settings

        redis_for_gen = self.redis
        if not redis_for_gen:
            redis_for_gen = await aioredis.from_url(
                _settings.REDIS_URL, decode_responses=True
            )
            close_redis = True
        else:
            close_redis = False

        dl_number = await generate("download", redis_for_gen)
        if close_redis:
            await redis_for_gen.aclose()

        log = DownloadLog(
            number=dl_number,
            book_id=book.id,
            book_version_id=version.id,
            user_id=user.id,
        )
        self.db.add(log)

        book.total_downloads += 1
        version.total_downloads += 1
        await self.db.commit()

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=DOWNLOAD_URL_TTL)

        return DownloadResponse(
            download_url=download_url,
            expires_in=DOWNLOAD_URL_TTL,
            expires_at=expires_at.isoformat(),
            book=BookFileSummary(
                book_id=str(book.uuid),
                title=version.title,
                file_name=version.pdf_file_name,
                file_size_mb=float(version.pdf_file_size_mb),
            ),
            download_limits=DownloadLimits(
                daily_limit=getattr(settings, "MAX_DOWNLOADS_PER_DAY", 5),
                monthly_limit=getattr(settings, "MAX_DOWNLOADS_PER_MONTH", 15),
                daily_remaining=daily_remaining,
                monthly_remaining=monthly_remaining,
                daily_resets_at=(now + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                ).isoformat(),
                monthly_resets_at=(
                    (now.replace(day=1) + timedelta(days=32)).replace(
                        day=1, hour=0, minute=0, second=0
                    )
                ).isoformat(),
            ),
        )

    async def get_my_history(
        self, user: User, pagination
    ) -> PaginatedResponse:
        """Return paginated download history for the current user."""
        page = getattr(pagination, "page", 1)
        limit = getattr(pagination, "limit", 20)

        query = select(DownloadLog).where(
            DownloadLog.user_id == user.id,
            DownloadLog.is_deleted.is_(False),
        ).order_by(DownloadLog.downloaded_at.desc())

        total = (
            await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
        ).scalar() or 0

        offset = (page - 1) * limit
        result = await self.db.execute(query.offset(offset).limit(limit))
        logs = result.scalars().all()

        items = []
        for log in logs:
            book_result = await self.db.execute(
                select(Book).where(Book.id == log.book_id)
            )
            book = book_result.scalar_one_or_none()
            if not book:
                continue
            version_result = await self.db.execute(
                select(BookVersion).where(BookVersion.id == log.book_version_id)
            )
            version = version_result.scalar_one_or_none()
            items.append(
                {
                    "download_id": str(log.uuid),
                    "book_id": str(book.uuid),
                    "title": version.title if version else book.title,
                    "downloaded_at": log.downloaded_at.isoformat()
                    if log.downloaded_at
                    else "",
                    "is_deleted": log.is_deleted,
                }
            )

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=compute_pages(total, limit),
        )

    async def soft_delete_history(self, book_uuid: str, user: User) -> None:
        """Soft-hide a download history entry."""
        book_result = await self.db.execute(
            select(Book).where(Book.uuid == book_uuid)
        )
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        log_result = await self.db.execute(
            select(DownloadLog).where(
                DownloadLog.book_id == book.id,
                DownloadLog.user_id == user.id,
                DownloadLog.is_deleted.is_(False),
            )
        )
        log = log_result.scalars().first()
        if not log:
            raise HTTPException(
                status_code=404, detail="Download history entry not found."
            )

        log.is_deleted = True
        log.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()
