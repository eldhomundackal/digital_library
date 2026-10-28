"""Notification service — in-app notification lifecycle."""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification
from app.db.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferencesResponse,
    NotificationResponse,
)
from app.utils.pagination import compute_pages

NOTIFICATION_TTL_DAYS = 7


class NotificationService:
    """Handles in-app notification creation, listing, and cleanup."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialise with DB session."""
        self.db = db

    async def create_or_group_notification(
        self,
        user_id: int,
        notification_type: str,
        group_key: str,
        title: str,
        data: dict,
    ) -> None:
        """Create a new notification or increment an existing grouped one."""
        message = data.get("message", title)

        existing_result = await self.db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.group_key == group_key,
                Notification.is_read.is_(False),
            )
        )
        existing = existing_result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if existing:
            existing.group_count += 1
            existing.is_grouped = True
            existing.title = title
            existing.message = message
            existing.data = data
            existing.updated_at = now
        else:
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                group_key=group_key,
                expires_at=now + timedelta(days=NOTIFICATION_TTL_DAYS),
                data=data,
            )
            self.db.add(notification)

        await self.db.commit()

    async def get_my_notifications(
        self, user: User, filters, pagination
    ) -> NotificationListResponse:
        """Return paginated notifications for the current user."""
        page = getattr(pagination, "page", 1)
        limit = getattr(pagination, "limit", 20)
        is_read_filter = getattr(filters, "is_read", None)

        query = select(Notification).where(
            Notification.user_id == user.id
        )

        if is_read_filter is not None:
            query = query.where(Notification.is_read.is_(is_read_filter))

        query = query.order_by(Notification.created_at.desc())

        total = (
            await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
        ).scalar() or 0

        unread_count = (
            await self.db.execute(
                select(func.count()).where(
                    Notification.user_id == user.id,
                    Notification.is_read.is_(False),
                )
            )
        ).scalar() or 0

        offset = (page - 1) * limit
        result = await self.db.execute(query.offset(offset).limit(limit))
        notifications = result.scalars().all()

        items = [
            NotificationResponse(
                notification_id=str(n.uuid),
                type=n.type,
                title=n.title,
                message=n.message,
                is_read=n.is_read,
                is_grouped=n.is_grouped,
                group_count=n.group_count,
                data=n.data,
                created_at=n.created_at.isoformat() if n.created_at else "",
                updated_at=(n.updated_at or n.created_at).isoformat()
                if (n.updated_at or n.created_at)
                else "",
            )
            for n in notifications
        ]

        return NotificationListResponse(
            unread_count=unread_count,
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=compute_pages(total, limit),
        )

    async def mark_read(self, notification_id: str, user: User) -> None:
        """Mark a single notification as read and reset its grouping."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.uuid == notification_id,
                Notification.user_id == user.id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found.")

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        notification.group_count = 1
        notification.is_grouped = False
        await self.db.commit()

    async def mark_all_read(self, user: User) -> dict:
        """Mark all unread notifications as read for the current user."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user.id,
                Notification.is_read.is_(False),
            )
            .values(
                is_read=True,
                read_at=now,
                group_count=1,
                is_grouped=False,
            )
            .returning(Notification.id)
        )
        count = len(result.fetchall())
        await self.db.commit()
        return {"marked": count}

    async def delete_notification(
        self, notification_id: str, user: User
    ) -> None:
        """Hard-delete a notification (notifications are disposable)."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.uuid == notification_id,
                Notification.user_id == user.id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found.")

        await self.db.delete(notification)
        await self.db.commit()

    async def update_preferences(
        self, user: User, payload
    ) -> NotificationPreferencesResponse:
        """Update notification preferences on the user's profile."""
        from app.db.models.user import PublisherProfile, ReaderProfile

        profile_result = await self.db.execute(
            select(ReaderProfile).where(ReaderProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            pub_result = await self.db.execute(
                select(PublisherProfile).where(PublisherProfile.user_id == user.id)
            )
            profile = pub_result.scalar_one_or_none()

        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found.")

        profile.reply_notifications = payload.reply_notifications
        await self.db.commit()

        return NotificationPreferencesResponse(
            reply_notifications=profile.reply_notifications
        )

    async def cleanup_expired(self) -> int:
        """Delete all expired notifications. Called by Celery Beat daily."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            delete(Notification).where(Notification.expires_at < now).returning(
                Notification.id
            )
        )
        count = len(result.fetchall())
        await self.db.commit()
        return count
