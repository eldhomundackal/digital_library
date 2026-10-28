"""Admin user management router — /admin/users endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.db.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.user import CreateStaffRequest
from app.services.user_service import UserService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/admin/users", tags=["Admin — Users"])

_ADMIN_ROLES = ("admin", "superadmin")
_STAFF_ROLES = ("staff", "admin", "superadmin")


@router.get("")
async def list_users(
    role: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """List users with optional role/active filters."""
    from sqlalchemy import func

    query = select(User)
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    count_q = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_q)
    total = count_result.scalar() or 0

    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    users = result.scalars().all()

    items = [
        {
            "user_id": str(u.uuid),
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]
    return SuccessResponse(
        data={"items": items, "total": total, "page": page, "limit": limit}
    )


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get a specific user by UUID."""
    result = await db.execute(select(User).where(User.uuid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    storage = get_storage_provider()
    service = UserService(db, storage)
    profile = await service.get_my_profile(user)
    return SuccessResponse(data=profile)


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    payload: dict,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Partial update a user (admin only)."""
    result = await db.execute(select(User).where(User.uuid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    allowed_fields = {"email", "role"}
    for field, value in payload.items():
        if field in allowed_fields:
            setattr(user, field, value)
    await db.commit()
    return SuccessResponse(data={"message": "User updated."})


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Reactivate a soft-deleted user."""
    result = await db.execute(select(User).where(User.uuid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = True
    user.deleted_at = None
    await db.commit()
    return SuccessResponse(data={"message": "User activated."})


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Soft-delete a user account."""
    result = await db.execute(select(User).where(User.uuid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = False
    user.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return SuccessResponse(data={"message": "User deactivated."})


@router.post("/create-staff")
async def create_staff(
    payload: CreateStaffRequest,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Create a new staff user."""
    storage = get_storage_provider()
    service = UserService(db, storage)
    result = await service.create_staff(payload, current_user)
    return SuccessResponse(data=result)


@router.post("/create-admin")
async def create_admin(
    payload: CreateStaffRequest,
    current_user=Depends(require_roles("superadmin")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Create a new admin user (superadmin only)."""
    storage = get_storage_provider()
    service = UserService(db, storage)
    result = await service.create_admin(payload, current_user)
    return SuccessResponse(data=result)
