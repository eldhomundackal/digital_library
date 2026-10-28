"""Admin audit log router — GET /admin/audit-log."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.common import SuccessResponse
from app.services.admin_service import AdminService
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/admin", tags=["Admin Audit"])

_ADMIN_ROLES = ("admin", "superadmin")


class AuditFilters:
    """Query parameters for filtering the audit log."""

    def __init__(
        self,
        action: str | None = None,
        performed_by: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> None:
        """Initialise audit log filter parameters."""
        self.action = action
        self.performed_by = performed_by
        self.from_date = from_date
        self.to_date = to_date


@router.get("/audit-log")
async def get_audit_log(
    filters: AuditFilters = Depends(),
    pagination: PaginationParams = Depends(),
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Return paginated admin audit log."""
    service = AdminService(db)
    result = await service.get_audit_log(filters, pagination)
    return SuccessResponse(data=result)
