"""Analytics service — publisher and platform download analytics."""

from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.book import Book, BookVersion
from app.db.models.download import DownloadLog
from app.db.models.publisher import PublisherProfile
from app.db.models.user import User
from app.schemas.book import BookListItem
from app.schemas.download import (
    BookDownloadAnalytics,
    ChartDataPoint,
    DownloadAnalyticsSummary,
)


class AnalyticsService:
    """Aggregates download analytics for publishers and admins."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialise with DB session."""
        self.db = db

    async def get_publisher_analytics(self, user: User) -> dict:
        """Return all-time and per-book download analytics for the publisher."""
        books_result = await self.db.execute(
            select(Book).where(
                Book.publisher_id == user.id,
                Book.is_active.is_(True),
            )
        )
        books = books_result.scalars().all()
        book_ids = [b.id for b in books]

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        def _count_query(after: datetime | None = None) -> int:
            base = select(func.count(DownloadLog.id)).where(
                DownloadLog.book_id.in_(book_ids)
            )
            if after:
                base = base.where(DownloadLog.downloaded_at >= after)
            return base

        all_time = (await self.db.execute(_count_query())).scalar() or 0
        this_month = (await self.db.execute(_count_query(month_start))).scalar() or 0
        this_week = (await self.db.execute(_count_query(week_start))).scalar() or 0
        today_count = (await self.db.execute(_count_query(today_start))).scalar() or 0

        per_book = []
        for book in books:
            version_result = await self.db.execute(
                select(BookVersion).where(BookVersion.id == book.current_version_id)
            )
            version = version_result.scalar_one_or_none()
            title = version.title if version else book.title

            book_all_time = (
                await self.db.execute(
                    select(func.count(DownloadLog.id)).where(
                        DownloadLog.book_id == book.id
                    )
                )
            ).scalar() or 0

            per_book.append(
                {
                    "book_id": str(book.uuid),
                    "title": title,
                    "total_downloads": book_all_time,
                }
            )

        per_book.sort(key=lambda x: x["total_downloads"], reverse=True)
        most_downloaded = per_book[0] if per_book else None

        return {
            "summary": {
                "total_downloads_all_time": all_time,
                "total_downloads_this_month": this_month,
                "total_downloads_this_week": this_week,
                "total_downloads_today": today_count,
            },
            "most_downloaded_book": most_downloaded,
            "books": per_book,
        }

    async def get_book_analytics(
        self,
        book_uuid: str,
        period: str,
        from_date: str | None,
        to_date: str | None,
        user: User,
    ) -> BookDownloadAnalytics:
        """Return chart analytics for a specific book."""
        book_result = await self.db.execute(
            select(Book).where(Book.uuid == book_uuid, Book.is_active.is_(True))
        )
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        is_admin = user.role in ("admin", "superadmin", "staff")
        if not is_admin and book.publisher_id != user.id:
            raise HTTPException(
                status_code=403, detail="Access denied to this book's analytics."
            )

        version_result = await self.db.execute(
            select(BookVersion).where(BookVersion.id == book.current_version_id)
        )
        version = version_result.scalar_one_or_none()
        title = version.title if version else book.title

        now = datetime.now(timezone.utc)
        if from_date:
            start_dt = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc)
        else:
            start_dt = now - timedelta(days=30)

        if to_date:
            end_dt = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc)
        else:
            end_dt = now

        logs_result = await self.db.execute(
            select(DownloadLog.downloaded_at).where(
                DownloadLog.book_id == book.id,
                DownloadLog.downloaded_at >= start_dt,
                DownloadLog.downloaded_at <= end_dt,
            )
        )
        logs = logs_result.scalars().all()

        chart_map: dict[str, int] = {}
        for dl_at in logs:
            if dl_at is None:
                continue
            if period == "week":
                monday = dl_at.date() - timedelta(days=dl_at.weekday())
                key = monday.isoformat()
            elif period == "month":
                key = dl_at.strftime("%Y-%m")
            else:
                key = dl_at.strftime("%Y-%m-%d")
            chart_map[key] = chart_map.get(key, 0) + 1

        chart_data = [
            ChartDataPoint(date=k, downloads=v) for k, v in sorted(chart_map.items())
        ]

        total_in_range = sum(v for v in chart_map.values())
        now_d = date.today()
        today_start_dt = datetime.combine(now_d, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        week_start_dt = today_start_dt - timedelta(days=now_d.weekday())
        month_start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        all_time_count = (
            await self.db.execute(
                select(func.count(DownloadLog.id)).where(DownloadLog.book_id == book.id)
            )
        ).scalar() or 0
        month_count = (
            await self.db.execute(
                select(func.count(DownloadLog.id)).where(
                    DownloadLog.book_id == book.id,
                    DownloadLog.downloaded_at >= month_start_dt,
                )
            )
        ).scalar() or 0
        week_count = (
            await self.db.execute(
                select(func.count(DownloadLog.id)).where(
                    DownloadLog.book_id == book.id,
                    DownloadLog.downloaded_at >= week_start_dt,
                )
            )
        ).scalar() or 0
        today_count = (
            await self.db.execute(
                select(func.count(DownloadLog.id)).where(
                    DownloadLog.book_id == book.id,
                    DownloadLog.downloaded_at >= today_start_dt,
                )
            )
        ).scalar() or 0

        summary = DownloadAnalyticsSummary(
            total_downloads_all_time=all_time_count,
            total_downloads_this_month=month_count,
            total_downloads_this_week=week_count,
            total_downloads_today=today_count,
        )

        book_item = BookListItem(
            book_id=str(book.uuid),
            title=title,
            slug=book.slug,
            publisher_id=str(book.uuid),
            thumbnail_url=version.thumbnail_url if version else None,
            average_rating=float(book.average_rating or 0),
            total_reviews=book.total_reviews or 0,
            total_downloads=book.total_downloads or 0,
            language=None,
            categories=[],
            tags=[],
            published_at=book.published_at.isoformat() if book.published_at else None,
        )

        return BookDownloadAnalytics(
            book=book_item,
            summary=summary,
            chart_data=chart_data,
        )

    async def get_platform_analytics(self, admin: User) -> dict:
        """Return platform-wide download analytics."""
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_downloads = (
            await self.db.execute(select(func.count(DownloadLog.id)))
        ).scalar() or 0

        unique_this_month = (
            await self.db.execute(
                select(func.count(func.distinct(DownloadLog.user_id))).where(
                    DownloadLog.downloaded_at >= month_start
                )
            )
        ).scalar() or 0

        top_books_result = await self.db.execute(
            select(DownloadLog.book_id, func.count(DownloadLog.id).label("cnt"))
            .group_by(DownloadLog.book_id)
            .order_by(func.count(DownloadLog.id).desc())
            .limit(10)
        )
        top_books_rows = top_books_result.fetchall()
        top_books = []
        for row in top_books_rows:
            book_result = await self.db.execute(
                select(Book).where(Book.id == row.book_id)
            )
            book = book_result.scalar_one_or_none()
            if book:
                top_books.append(
                    {
                        "book_id": str(book.uuid),
                        "title": book.title,
                        "downloads": row.cnt,
                    }
                )

        monthly_chart = []
        for month_offset in range(11, -1, -1):
            base_date = (
                now.replace(day=1) - timedelta(days=month_offset * 28)
            ).replace(day=1)
            next_month = (base_date + timedelta(days=32)).replace(day=1)
            count = (
                await self.db.execute(
                    select(func.count(DownloadLog.id)).where(
                        DownloadLog.downloaded_at >= base_date,
                        DownloadLog.downloaded_at < next_month,
                    )
                )
            ).scalar() or 0
            monthly_chart.append(
                {
                    "month": base_date.strftime("%Y-%m"),
                    "downloads": count,
                }
            )

        return {
            "total_downloads": total_downloads,
            "unique_downloaders_this_month": unique_this_month,
            "top_books": top_books,
            "monthly_chart": monthly_chart,
        }

    async def get_user_download_analytics(self, user_id: str, admin: User) -> dict:
        """Return download history and stats for a specific user (admin only)."""
        from app.db.models.user import User as UserModel

        user_result = await self.db.execute(
            select(UserModel).where(UserModel.uuid == user_id)
        )
        target_user = user_result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found.")

        logs_result = await self.db.execute(
            select(DownloadLog)
            .where(DownloadLog.user_id == target_user.id)
            .order_by(DownloadLog.downloaded_at.desc())
            .limit(100)
        )
        logs = logs_result.scalars().all()

        items = []
        for log in logs:
            book_result = await self.db.execute(
                select(Book).where(Book.id == log.book_id)
            )
            book = book_result.scalar_one_or_none()
            items.append(
                {
                    "download_id": str(log.uuid),
                    "book_id": str(book.uuid) if book else None,
                    "title": book.title if book else None,
                    "downloaded_at": (
                        log.downloaded_at.isoformat() if log.downloaded_at else ""
                    ),
                }
            )

        total = (
            await self.db.execute(
                select(func.count(DownloadLog.id)).where(
                    DownloadLog.user_id == target_user.id
                )
            )
        ).scalar() or 0

        return {
            "user_id": str(target_user.uuid),
            "total_downloads": total,
            "history": items,
        }
