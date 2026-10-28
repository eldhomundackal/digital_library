"""Admin reviews router — moderation endpoints."""

from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.common import SuccessResponse
from app.services.review_service import ReviewService

router = APIRouter(prefix="/admin/reviews", tags=["Admin Reviews"])

_STAFF_ROLES = ("staff", "admin", "superadmin")


class DismissReportRequest(BaseModel):
    """Body for dismissing a review report."""

    note: str


@router.get("")
async def list_all_reviews(
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """List all reviews across the platform."""
    service = ReviewService(db)
    result = await service.list_all_reviews()
    return SuccessResponse(data=result)


@router.get("/reported")
async def list_reported_reviews(
    status: str | None = None,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """List reported reviews, optionally filtered by status."""
    service = ReviewService(db)
    result = await service.list_reported_reviews(status=status)
    return SuccessResponse(data=result)


@router.delete("/{review_id}")
async def remove_review(
    review_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Remove a review and all its replies."""
    service = ReviewService(db)
    await service.remove_review(review_id, current_user)
    return SuccessResponse(data={"message": "Review removed."})


@router.delete("/{review_id}/replies/{reply_id}")
async def remove_reply(
    review_id: str,
    reply_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Remove a specific reply."""
    service = ReviewService(db)
    await service.delete_reply(review_id, reply_id, current_user)
    return SuccessResponse(data={"message": "Reply removed."})


@router.post("/{review_id}/dismiss-report")
async def dismiss_report(
    review_id: str,
    payload: DismissReportRequest,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Dismiss all pending reports on a review."""
    service = ReviewService(db)
    await service.dismiss_report(review_id, payload.note, current_user)
    return SuccessResponse(data={"message": "Reports dismissed."})
