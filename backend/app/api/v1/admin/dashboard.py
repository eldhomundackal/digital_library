"""Admin dashboard router — GET /admin/dashboard/stats/ and /pending-actions/."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.common import SuccessResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

_STAFF_ROLES = ("staff", "admin", "superadmin")


@router.get("/dashboard/stats/")
async def get_dashboard_stats(
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Return platform overview stats for the admin dashboard."""
    service = AdminService(db)
    result = await service.get_dashboard()
    overview = result.platform_overview
    pending = result.pending_actions
    return SuccessResponse(
        data={
            "total_users": overview.total_readers + overview.total_publishers,
            "total_books": overview.total_books,
            "total_downloads": overview.total_downloads,
            "pending_kyc": pending.kyc_applications,
            "pending_books": pending.book_approvals,
            "active_publishers": overview.total_publishers,
        }
    )


@router.get("/dashboard/pending-actions/")
async def get_pending_actions(
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Return list of pending KYC and book approval actions."""
    service = AdminService(db)
    result = await service.get_dashboard()
    recent = result.recent_activity

    actions = []
    for book in recent.latest_books:
        actions.append(
            {
                "type": "book",
                "id": book["book_id"],
                "title": book["title"],
                "submitted_by": "",
                "submitted_at": book["submitted_at"],
            }
        )
    for publisher in recent.latest_publishers:
        actions.append(
            {
                "type": "kyc",
                "id": publisher["user_id"],
                "title": publisher["email"],
                "submitted_by": publisher["email"],
                "submitted_at": publisher["created_at"],
            }
        )
    return SuccessResponse(data=actions)
