"""Admin activity feed router — /admin/activity-feed endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_db, require_roles
from app.schemas.common import SuccessResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin/activity-feed", tags=["Admin Activity"])

_STAFF_ROLES = ("staff", "admin", "superadmin")


@router.get("")
async def get_activity_feed(
    category: str | None = None,
    is_read: bool | None = None,
    params: PaginationParams = Depends(),
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get the admin activity feed with optional filters."""
    filters = {"category": category, "is_read": is_read}
    service = AdminService(db)
    result = await service.get_activity_feed(current_user, filters, params)
    return SuccessResponse(data=result)


@router.patch("/{activity_id}/read")
async def mark_activity_read(
    activity_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Mark a single activity feed entry as read."""
    service = AdminService(db)
    await service.mark_activity_read(activity_id, current_user)
    return SuccessResponse(data={"message": "Activity marked as read."})


@router.post("/read-all")
async def mark_all_activity_read(
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Mark all activity feed entries as read."""
    service = AdminService(db)
    await service.mark_all_activity_read(current_user)
    return SuccessResponse(data={"message": "All activity marked as read."})
