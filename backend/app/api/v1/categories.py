"""Categories public router — /categories endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_redis
from app.schemas.common import SuccessResponse
from app.services.book_service import BookService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("")
async def list_categories(
    db: AsyncSession = Depends(get_db), redis=Depends(get_redis),
) -> SuccessResponse:
    """List active categories with total_books count."""
    storage = get_storage_provider()
    service = BookService(db, storage, redis)
    result = await service.list_categories()
    return SuccessResponse(data=result)
