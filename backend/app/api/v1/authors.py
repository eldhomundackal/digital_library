"""Authors public router — /authors endpoints."""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_db, require_approved_publisher
from app.schemas.book import CreateAuthorRequest
from app.schemas.common import SuccessResponse
from app.services.author_service import AuthorService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/authors", tags=["Authors"])


@router.get("")
async def list_authors(
    search: str | None = None,
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """List authors with optional search."""
    storage = get_storage_provider()
    service = AuthorService(db, storage)
    result = await service.list_authors(search, params)
    return SuccessResponse(data=result)


@router.get("/{author_id}")
async def get_author(
    author_id: str,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get author detail including their books."""
    storage = get_storage_provider()
    service = AuthorService(db, storage)
    result = await service.get_author_detail(author_id)
    return SuccessResponse(data=result)


@router.post("")
async def create_author(
    payload: CreateAuthorRequest = Depends(),
    avatar: UploadFile | None = File(None),
    current_user=Depends(require_approved_publisher),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Create a new author (publisher only)."""
    storage = get_storage_provider()
    service = AuthorService(db, storage)
    result = await service.create_author(payload, avatar, current_user)
    return SuccessResponse(data=result)


@router.patch("/{author_id}")
async def update_author(
    author_id: str,
    payload: CreateAuthorRequest,
    current_user=Depends(require_approved_publisher),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Update an author (creator publisher only)."""
    storage = get_storage_provider()
    service = AuthorService(db, storage)
    result = await service.update_author(author_id, payload, current_user)
    return SuccessResponse(data=result)
