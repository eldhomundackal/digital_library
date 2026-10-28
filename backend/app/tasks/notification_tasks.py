"""Celery tasks for in-app notification creation and cleanup."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def create_in_app_notification(
    user_id: int,
    notification_type: str,
    group_key: str,
    title: str,
    message: str,
    data: dict,
) -> None:
    """Create or group an in-app notification for a single user."""
    import asyncio

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.db.session import AsyncSessionLocal

    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            from app.services.notification_service import NotificationService

            service = NotificationService(db)
            notification_data = data.copy()
            notification_data.setdefault("message", message)
            await service.create_or_group_notification(
                user_id=user_id,
                notification_type=notification_type,
                group_key=group_key,
                title=title,
                data=notification_data,
            )

    try:
        asyncio.run(_run())
    except Exception:
        logger.exception(
            "Failed to create notification for user %s type %s",
            user_id,
            notification_type,
        )


@celery_app.task
def create_notifications_for_role(
    role: str,
    notification_type: str,
    title: str,
    message: str,
    data: dict,
) -> None:
    """Bulk notify all active users of a given role."""
    import asyncio

    from sqlalchemy import select

    from app.db.models.user import User
    from app.db.session import AsyncSessionLocal

    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User.id).where(
                    User.role == role,
                    User.is_active.is_(True),
                )
            )
            user_ids = result.scalars().all()

        for uid in user_ids:
            create_in_app_notification.delay(
                user_id=uid,
                notification_type=notification_type,
                group_key=f"{notification_type}:{role}",
                title=title,
                message=message,
                data=data,
            )

    try:
        asyncio.run(_run())
    except Exception:
        logger.exception(
            "Failed bulk notification for role %s type %s",
            role,
            notification_type,
        )


@celery_app.task
def cleanup_expired_notifications() -> dict:
    """Delete all expired notifications. Scheduled daily by Celery Beat."""
    import asyncio

    from app.db.session import AsyncSessionLocal

    async def _run() -> int:
        async with AsyncSessionLocal() as db:
            from app.services.notification_service import NotificationService

            service = NotificationService(db)
            return await service.cleanup_expired()

    try:
        count = asyncio.run(_run())
        logger.info("Cleaned up %d expired notifications.", count)
        return {"deleted_count": count}
    except Exception:
        logger.exception("Failed to cleanup expired notifications.")
        return {"deleted_count": 0}
