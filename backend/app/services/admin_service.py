"""Admin service — dashboard, audit log, and activity feed."""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import ActivityFeed, AuditLog
from app.db.models.book import Book, BookVersion
from app.db.models.download import DownloadLog
from app.db.models.kyc import KYCApplication
from app.db.models.review import ReviewReport
from app.db.models.category import Tag
from app.db.models.publisher import PublisherProfile
from app.db.models.user import User
from app.schemas.admin import (
    ActivityFeedResponse,
    AuditLogResponse,
    AuditTarget,
    DashboardResponse,
    PendingActions,
    PlatformOverview,
    RecentActivity,
)
from app.schemas.auth import UserSummary
from app.schemas.common import PaginatedResponse
from app.utils.pagination import compute_pages


class AdminService:
    """Aggregates admin dashboard data, audit trail, and activity feed."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialise with DB session."""
        self.db = db

    async def get_dashboard(self) -> DashboardResponse:
        """Return platform overview, pending action counts, and recent activity."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_readers = (
            await self.db.execute(
                select(func.count(User.id)).where(User.role == "reader")
            )
        ).scalar() or 0

        total_publishers = (
            await self.db.execute(
                select(func.count(User.id)).where(User.role == "publisher")
            )
        ).scalar() or 0

        total_books = (
            await self.db.execute(
                select(func.count(BookVersion.id)).where(
                    BookVersion.status == "APPROVED"
                )
            )
        ).scalar() or 0

        total_downloads = (
            await self.db.execute(select(func.count(DownloadLog.id)))
        ).scalar() or 0

        new_registrations_today = (
            await self.db.execute(
                select(func.count(User.id)).where(
                    User.created_at >= today_start
                )
            )
        ).scalar() or 0

        new_books_today = (
            await self.db.execute(
                select(func.count(BookVersion.id)).where(
                    BookVersion.status == "APPROVED",
                    BookVersion.updated_at >= today_start,
                )
            )
        ).scalar() or 0

        kyc_pending = (
            await self.db.execute(
                select(func.count(KYC.id)).where(KYC.overall_status == "PENDING")
            )
        ).scalar() or 0

        book_approvals = (
            await self.db.execute(
                select(func.count(BookVersion.id)).where(
                    BookVersion.status == "PENDING"
                )
            )
        ).scalar() or 0

        tag_approvals = (
            await self.db.execute(
                select(func.count(Tag.id)).where(Tag.status == "PENDING")
            )
        ).scalar() or 0

        reported_reviews = (
            await self.db.execute(
                select(func.count(ReviewReport.id)).where(
                    ReviewReport.status == "PENDING"
                )
            )
        ).scalar() or 0

        latest_books_result = await self.db.execute(
            select(BookVersion)
            .where(BookVersion.status == "PENDING")
            .order_by(BookVersion.submitted_at.desc())
            .limit(5)
        )
        latest_books = [
            {
                "book_id": str(bv.uuid),
                "title": bv.title,
                "submitted_at": bv.submitted_at.isoformat()
                if bv.submitted_at
                else "",
            }
            for bv in latest_books_result.scalars().all()
        ]

        latest_publishers_result = await self.db.execute(
            select(User)
            .where(User.role == "publisher", User.is_active.is_(True))
            .order_by(User.created_at.desc())
            .limit(5)
        )
        latest_publishers = [
            {
                "user_id": str(u.uuid),
                "email": u.email,
                "created_at": u.created_at.isoformat() if u.created_at else "",
            }
            for u in latest_publishers_result.scalars().all()
        ]

        latest_reports_result = await self.db.execute(
            select(ReviewReport)
            .where(ReviewReport.status == "PENDING")
            .order_by(ReviewReport.created_at.desc())
            .limit(5)
        )
        latest_reported_reviews = [
            {
                "report_id": str(rp.uuid),
                "reason": rp.reason,
                "created_at": rp.created_at.isoformat() if rp.created_at else "",
            }
            for rp in latest_reports_result.scalars().all()
        ]

        return DashboardResponse(
            platform_overview=PlatformOverview(
                total_readers=total_readers,
                total_publishers=total_publishers,
                total_books=total_books,
                total_downloads=total_downloads,
                new_registrations_today=new_registrations_today,
                new_books_today=new_books_today,
            ),
            pending_actions=PendingActions(
                kyc_applications=kyc_pending,
                book_approvals=book_approvals,
                tag_approvals=tag_approvals,
                reported_reviews=reported_reviews,
            ),
            recent_activity=RecentActivity(
                latest_books=latest_books,
                latest_publishers=latest_publishers,
                latest_reported_reviews=latest_reported_reviews,
            ),
        )

    async def get_audit_log(self, filters, pagination) -> PaginatedResponse:
        """Return paginated audit log, optionally filtered by action or date."""
        page = getattr(pagination, "page", 1)
        limit = getattr(pagination, "limit", 20)

        query = select(AuditLog).order_by(AuditLog.performed_at.desc())

        action_filter = getattr(filters, "action", None)
        performed_by_filter = getattr(filters, "performed_by", None)
        from_filter = getattr(filters, "from_date", None)
        to_filter = getattr(filters, "to_date", None)

        if action_filter:
            query = query.where(AuditLog.action == action_filter)
        if performed_by_filter:
            user_result = await self.db.execute(
                select(User.id).where(User.uuid == performed_by_filter)
            )
            uid = user_result.scalar_one_or_none()
            if uid:
                query = query.where(AuditLog.performed_by_id == uid)
        if from_filter:
            from_dt = datetime.fromisoformat(from_filter).replace(
                tzinfo=timezone.utc
            )
            query = query.where(AuditLog.performed_at >= from_dt)
        if to_filter:
            to_dt = datetime.fromisoformat(to_filter).replace(tzinfo=timezone.utc)
            query = query.where(AuditLog.performed_at <= to_dt)

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
            performed_by_result = await self.db.execute(
                select(User).where(User.id == log.performed_by_id)
            )
            performed_by = performed_by_result.scalar_one_or_none()
            items.append(
                AuditLogResponse(
                    audit_id=str(log.uuid),
                    action=log.action,
                    performed_by=UserSummary(
                        user_id=str(performed_by.uuid) if performed_by else "",
                        email=performed_by.email if performed_by else "",
                        role=performed_by.role if performed_by else "",
                    ),
                    target=AuditTarget(
                        type=log.target_type,
                        id=str(log.target_id),
                        label=log.target_label,
                    ),
                    metadata=log.metadata_,
                    note=log.note,
                    ip_address=log.ip_address,
                    performed_at=log.performed_at.isoformat()
                    if log.performed_at
                    else "",
                )
            )

        return PaginatedResponse(
            items=[i.model_dump() for i in items],
            total=total,
            page=page,
            limit=limit,
            pages=compute_pages(total, limit),
        )

    async def get_activity_feed(
        self, user: User, filters, pagination
    ) -> PaginatedResponse:
        """Return paginated activity feed for all staff/admin."""
        page = getattr(pagination, "page", 1)
        limit = getattr(pagination, "limit", 20)

        query = select(ActivityFeed).order_by(ActivityFeed.created_at.desc())

        category_filter = getattr(filters, "category", None)
        is_read_filter = getattr(filters, "is_read", None)

        if category_filter:
            query = query.where(ActivityFeed.category == category_filter)
        if is_read_filter is not None:
            query = query.where(ActivityFeed.is_read.is_(is_read_filter))

        total = (
            await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
        ).scalar() or 0

        offset = (page - 1) * limit
        result = await self.db.execute(query.offset(offset).limit(limit))
        entries = result.scalars().all()

        items = [
            ActivityFeedResponse(
                activity_id=str(e.uuid),
                type=e.type,
                category=e.category,
                title=e.title,
                message=e.message,
                action_url=e.action_url,
                actor={
                    "type": e.actor_type,
                    "id": str(e.actor_id),
                    "name": e.actor_name,
                },
                is_read=e.is_read,
                created_at=e.created_at.isoformat() if e.created_at else "",
            )
            for e in entries
        ]

        return PaginatedResponse(
            items=[i.model_dump() for i in items],
            total=total,
            page=page,
            limit=limit,
            pages=compute_pages(total, limit),
        )

    async def mark_activity_read(
        self, activity_id: str, user: User
    ) -> None:
        """Mark an activity feed entry as read."""
        result = await self.db.execute(
            select(ActivityFeed).where(ActivityFeed.uuid == activity_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            raise HTTPException(status_code=404, detail="Activity entry not found.")

        entry.is_read = True
        entry.read_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def mark_all_activity_read(self, user: User) -> None:
        """Mark all unread activity entries as read."""
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(ActivityFeed)
            .where(ActivityFeed.is_read.is_(False))
            .values(is_read=True, read_at=now)
        )
        await self.db.commit()
