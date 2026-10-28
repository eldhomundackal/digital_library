"""Public publisher profile router — /publishers endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_db
from app.schemas.common import SuccessResponse
from app.services.publisher_service import PublisherService

router = APIRouter(prefix="/publishers", tags=["Publishers"])


@router.get("/{publisher_id}")
async def get_publisher(
    publisher_id: str,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Return a verified publisher's public profile."""
    service = PublisherService(db)
    profile = await service.get_public_profile(publisher_id)
    return SuccessResponse(data=profile)


@router.get("/{publisher_id}/books")
async def get_publisher_books(
    publisher_id: str,
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Return paginated approved books for a verified publisher."""
    service = PublisherService(db)
    result = await service.get_public_books(publisher_id, params.page, params.limit)
    return SuccessResponse(data=result)
