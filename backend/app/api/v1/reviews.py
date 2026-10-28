"""Reviews router — replies and reports on reviews."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_roles
from app.schemas.common import SuccessResponse
from app.schemas.review import ReportRequest, SubmitReplyRequest
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/{review_id}/replies")
async def submit_reply(
    review_id: str,
    payload: SubmitReplyRequest,
    current_user=Depends(require_roles("reader", "publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Submit a reply to a review."""
    service = ReviewService(db)
    result = await service.submit_reply(review_id, payload, current_user)
    return SuccessResponse(data=result)


@router.patch("/{review_id}/replies/{reply_id}")
async def update_reply(
    review_id: str,
    reply_id: str,
    payload: SubmitReplyRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Update a reply (owner only)."""
    service = ReviewService(db)
    result = await service.update_reply(review_id, reply_id, payload, current_user)
    return SuccessResponse(data=result)


@router.delete("/{review_id}/replies/{reply_id}")
async def delete_reply(
    review_id: str,
    reply_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Delete a reply (owner only)."""
    service = ReviewService(db)
    await service.delete_reply(review_id, reply_id, current_user)
    return SuccessResponse(data={"message": "Reply deleted."})


@router.post("/{review_id}/report")
async def report_review(
    review_id: str,
    payload: ReportRequest,
    current_user=Depends(require_roles("reader", "publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Report a review for moderation."""
    service = ReviewService(db)
    await service.report_review(review_id, payload, current_user)
    return SuccessResponse(data={"message": "Review reported."})


@router.post("/{review_id}/replies/{reply_id}/report")
async def report_reply(
    review_id: str,
    reply_id: str,
    payload: ReportRequest,
    current_user=Depends(require_roles("reader", "publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Report a reply for moderation."""
    service = ReviewService(db)
    await service.report_reply(review_id, reply_id, payload, current_user)
    return SuccessResponse(data={"message": "Reply reported."})
