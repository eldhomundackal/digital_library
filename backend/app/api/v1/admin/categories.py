"""Admin categories router — /admin/categories endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_redis, require_roles
from app.schemas.common import SuccessResponse
from app.services.book_service import BookService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/admin/categories", tags=["Admin Categories"])

_ADMIN_ROLES = ("admin", "superadmin")


class CreateCategoryRequest(BaseModel):
    """Body for creating a category."""

    name: str
    slug: str


class UpdateCategoryRequest(BaseModel):
    """Body for updating a category."""

    name: str | None = None
    slug: str | None = None


@router.get("")
async def list_categories(
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> SuccessResponse:
    """List all categories."""
    storage = get_storage_provider()
    service = BookService(db, storage, redis)
    result = await service.list_categories()
    return SuccessResponse(data=result)


@router.post("")
async def create_category(
    payload: CreateCategoryRequest,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> SuccessResponse:
    """Create a new category."""
    storage = get_storage_provider()
    service = BookService(db, storage, redis)
    result = await service.manage_category(
        "create", current_user, name=payload.name, slug=payload.slug
    )
    return SuccessResponse(data=result)


@router.patch("/{category_id}")
async def update_category(
    category_id: str,
    payload: UpdateCategoryRequest,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> SuccessResponse:
    """Update a category's name or slug."""
    storage = get_storage_provider()
    service = BookService(db, storage, redis)
    result = await service.manage_category(
        "update",
        current_user,
        category_id=category_id,
        name=payload.name,
        slug=payload.slug,
    )
    return SuccessResponse(data=result)


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> SuccessResponse:
    """Soft-delete a category."""
    storage = get_storage_provider()
    service = BookService(db, storage, redis)
    await service.manage_category("delete", current_user, category_id=category_id)
    return SuccessResponse(data={"message": "Category deleted."})
