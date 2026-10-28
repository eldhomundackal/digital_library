"""Admin tags router — /admin/tags endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.common import SuccessResponse
from app.services.book_service import BookService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/admin/tags", tags=["Admin Tags"])

_STAFF_ROLES = ("staff", "admin", "superadmin")


class UpdateTagRequest(BaseModel):
    """Body for updating a tag's name or slug."""

    name: str | None = None
    slug: str | None = None


@router.get("")
async def list_all_tags(
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """List all tags including PENDING ones."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    result = await service.list_approved_tags()
    return SuccessResponse(data=result)


@router.post("/{tag_id}/approve")
async def approve_tag(
    tag_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Approve a pending tag."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    await service.manage_tag(tag_id, "approve", current_user)
    return SuccessResponse(data={"message": "Tag approved."})


@router.post("/{tag_id}/reject")
async def reject_tag(
    tag_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Reject a pending tag."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    await service.manage_tag(tag_id, "reject", current_user)
    return SuccessResponse(data={"message": "Tag rejected."})


@router.patch("/{tag_id}")
async def update_tag(
    tag_id: str,
    payload: UpdateTagRequest,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Edit a tag's name or slug."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    await service.manage_tag(
        tag_id,
        "update",
        current_user,
        name=payload.name,
        slug=payload.slug,
    )
    return SuccessResponse(data={"message": "Tag updated."})


@router.delete("/{tag_id}")
async def deactivate_tag(
    tag_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Soft-deactivate a tag."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    await service.manage_tag(tag_id, "deactivate", current_user)
    return SuccessResponse(data={"message": "Tag deactivated."})
