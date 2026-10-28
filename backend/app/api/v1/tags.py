"""Tags public router — /tags endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.common import SuccessResponse
from app.services.book_service import BookService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("")
async def list_tags(
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """List APPROVED active tags with total_books count."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    result = await service.list_approved_tags()
    return SuccessResponse(data=result)
