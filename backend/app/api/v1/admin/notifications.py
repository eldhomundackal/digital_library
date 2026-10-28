"""Admin notifications router — /admin/notifications endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.common import SuccessResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/admin/notifications", tags=["Admin Notifications"])

_STAFF_ROLES = ("staff", "admin", "superadmin")


@router.get("")
async def get_admin_notifications(
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get notifications for the current admin/staff user."""
    service = NotificationService(db)
    result = await service.get_my_notifications(current_user, {})
    return SuccessResponse(data=result)


@router.post("/read-all")
async def mark_all_read(
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Mark all admin notifications as read."""
    service = NotificationService(db)
    await service.mark_all_read(current_user)
    return SuccessResponse(data={"message": "All notifications marked as read."})


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Mark a single notification as read."""
    service = NotificationService(db)
    await service.mark_read(notification_id, current_user)
    return SuccessResponse(data={"message": "Notification marked as read."})
