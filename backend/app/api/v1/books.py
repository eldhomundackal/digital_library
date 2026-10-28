"""Public book listing and detail router — /books endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    PaginationParams,
    get_current_user,
    get_db,
    get_optional_user,
    get_redis,
    require_roles,
)
from app.schemas.review import SubmitReviewRequest
from app.schemas.common import SuccessResponse
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("")
async def list_books(
    search: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    tag_id: int | None = Query(default=None),
    language_id: int | None = Query(default=None),
    publication_year: int | None = Query(default=None),
    sort_by: str = Query(default="latest"),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> SuccessResponse:
    """List all approved books with optional filters."""
    from app.services.book_service import BookService

    storage = get_storage_provider()
    service = BookService(db, storage, redis)
    filters = {
        "search": search,
        "category_id": category_id,
        "tag_id": tag_id,
        "language_id": language_id,
        "publication_year": publication_year,
        "sort_by": sort_by,
    }
    result = await service.list_approved_books(filters, params.page, params.limit)
    return SuccessResponse(data=result)


@router.get("/{book_id}")
async def get_book(
    book_id: str,
    current_user=Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> SuccessResponse:
    """Get book detail. Anonymous sees metadata only; logged-in sees download button."""
    from app.services.book_service import BookService

    storage = get_storage_provider()
    service = BookService(db, storage, redis)
    result = await service.get_book_detail(book_id, current_user)
    return SuccessResponse(data=result)


@router.get("/{book_id}/download")
async def download_book(
    book_id: str,
    current_user=Depends(require_roles("reader", "publisher")),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> SuccessResponse:
    """Generate a pre-signed download URL for a book."""
    from app.services.download_service import DownloadService

    storage = get_storage_provider()
    service = DownloadService(db, storage, redis)
    result = await service.generate_download_url(book_id, current_user)
    return SuccessResponse(data=result)


@router.get("/{book_id}/reviews")
async def get_book_reviews(
    book_id: str,
    sort_by: str = Query(default="latest"),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get paginated reviews for a book."""
    from app.services.review_service import ReviewService

    service = ReviewService(db)
    result = await service.get_book_reviews(book_id, sort_by, params)
    return SuccessResponse(data=result)


@router.post("/{book_id}/reviews")
async def submit_review(
    book_id: str,
    payload: SubmitReviewRequest,
    current_user=Depends(require_roles("reader", "publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Submit a review for a book."""
    from app.services.review_service import ReviewService

    service = ReviewService(db)
    result = await service.submit_review(book_id, payload, current_user)
    return SuccessResponse(data=result)


@router.patch("/{book_id}/reviews")
async def update_review(
    book_id: str,
    payload: SubmitReviewRequest,
    current_user=Depends(require_roles("reader", "publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Update the current user's review for a book."""
    from app.services.review_service import ReviewService

    service = ReviewService(db)
    result = await service.update_review(book_id, payload, current_user)
    return SuccessResponse(data=result)


@router.delete("/{book_id}/reviews")
async def delete_review(
    book_id: str,
    current_user=Depends(require_roles("reader", "publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Delete the current user's review for a book."""
    from app.services.review_service import ReviewService

    service = ReviewService(db)
    await service.delete_review(book_id, current_user)
    return SuccessResponse(data={"message": "Review deleted."})


@router.get("/{book_id}/reviews/me")
async def get_my_review(
    book_id: str,
    current_user=Depends(require_roles("reader", "publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get the current user's review for a book."""
    from app.services.review_service import ReviewService

    service = ReviewService(db)
    result = await service.get_my_review(book_id, current_user)
    return SuccessResponse(data=result)
