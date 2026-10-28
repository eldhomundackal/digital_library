"""Admin dashboard router — GET /admin/dashboard."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.common import SuccessResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

_STAFF_ROLES = ("staff", "admin", "superadmin")


@router.get("/dashboard")
async def get_dashboard(
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Return admin dashboard with platform overview and pending actions."""
    service = AdminService(db)
    result = await service.get_dashboard()
    return SuccessResponse(data=result)
