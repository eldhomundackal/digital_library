"""Admin authors router — /admin/authors endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.book import CreateAuthorRequest, MergeAuthorsRequest
from app.schemas.common import SuccessResponse
from app.services.author_service import AuthorService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/admin/authors", tags=["Admin Authors"])

_ADMIN_ROLES = ("admin", "superadmin")
_STAFF_ROLES = ("staff", "admin", "superadmin")


@router.patch("/{author_id}")
async def update_author(
    author_id: str,
    payload: CreateAuthorRequest,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Update an author's details."""
    storage = get_storage_provider()
    service = AuthorService(db, storage)
    result = await service.update_author(author_id, payload, current_user)
    return SuccessResponse(data=result)


@router.delete("/{author_id}")
async def deactivate_author(
    author_id: str,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Soft-deactivate an author."""
    storage = get_storage_provider()
    service = AuthorService(db, storage)
    await service.deactivate_author(author_id, current_user)
    return SuccessResponse(data={"message": "Author deactivated."})


@router.post("/merge")
async def merge_authors(
    payload: MergeAuthorsRequest,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Merge duplicate authors into a primary author."""
    storage = get_storage_provider()
    service = AuthorService(db, storage)
    result = await service.merge_authors(payload, current_user)
    return SuccessResponse(data=result)
