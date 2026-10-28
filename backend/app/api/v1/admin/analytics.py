"""Admin analytics router — platform-wide download analytics."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.common import SuccessResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])

_ADMIN_ROLES = ("admin", "superadmin")


@router.get("/downloads")
async def get_platform_analytics(
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Platform-wide download analytics."""
    service = AnalyticsService(db)
    result = await service.get_platform_analytics(current_user)
    return SuccessResponse(data=result)


@router.get("/downloads/{book_id}")
async def get_book_analytics(
    book_id: str,
    period: str = "day",
    from_date: str | None = None,
    to_date: str | None = None,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Download analytics for a specific book."""
    service = AnalyticsService(db)
    result = await service.get_book_analytics(
        book_id, period, from_date, to_date, current_user
    )
    return SuccessResponse(data=result)


@router.get("/users/{user_id}/downloads")
async def get_user_download_analytics(
    user_id: str,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Download history and stats for a specific user."""
    service = AnalyticsService(db)
    result = await service.get_user_download_analytics(user_id, current_user)
    return SuccessResponse(data=result)
