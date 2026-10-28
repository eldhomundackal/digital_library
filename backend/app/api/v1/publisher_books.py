"""Publisher book management router — /publisher/books endpoints."""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_db, require_approved_publisher
from app.schemas.common import SuccessResponse
from app.services.book_service import BookService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/publisher", tags=["Publisher Books"])


@router.get("/books")
async def list_my_books(
    status: str | None = None,
    params: PaginationParams = Depends(),
    current_user=Depends(require_approved_publisher),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """List publisher's own books filtered by status."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    result = await service.get_publisher_books(current_user, status, params)
    return SuccessResponse(data=result)


@router.post("/books")
async def create_book(
    title: str = Form(...),
    description: str = Form(...),
    category_id: int = Form(...),
    language_id: int = Form(...),
    version_label: str = Form(...),
    page_count: int | None = Form(None),
    publication_year: int | None = Form(None),
    isbn: str | None = Form(None),
    thumbnail: UploadFile = File(...),
    pdf_file: UploadFile = File(...),
    current_user=Depends(require_approved_publisher),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Create a new book in DRAFT status."""
    from app.schemas.book import CreateBookRequest

    payload = CreateBookRequest(
        title=title,
        description=description,
        category_id=category_id,
        language_id=language_id,
        version_label=version_label,
        page_count=page_count,
        publication_year=publication_year,
        isbn=isbn,
        authors=[],
    )
    storage = get_storage_provider()
    service = BookService(db, storage)
    result = await service.create_book(payload, thumbnail, pdf_file, current_user)
    return SuccessResponse(data=result)


@router.get("/books/{book_id}")
async def get_my_book(
    book_id: str,
    current_user=Depends(require_approved_publisher),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get full detail of publisher's book (all statuses)."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    result = await service.get_publisher_book_detail(book_id, current_user)
    return SuccessResponse(data=result)


@router.patch("/books/{book_id}")
async def update_book(
    book_id: str,
    title: str | None = Form(None),
    description: str | None = Form(None),
    category_id: int | None = Form(None),
    language_id: int | None = Form(None),
    version_label: str | None = Form(None),
    page_count: int | None = Form(None),
    publication_year: int | None = Form(None),
    isbn: str | None = Form(None),
    thumbnail: UploadFile | None = File(None),
    pdf_file: UploadFile | None = File(None),
    current_user=Depends(require_approved_publisher),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Update a DRAFT or REJECTED book."""
    payload = {
        k: v
        for k, v in {
            "title": title,
            "description": description,
            "category_id": category_id,
            "language_id": language_id,
            "version_label": version_label,
            "page_count": page_count,
            "publication_year": publication_year,
            "isbn": isbn,
        }.items()
        if v is not None
    }
    storage = get_storage_provider()
    service = BookService(db, storage)
    result = await service.update_book(
        book_id, payload, thumbnail, pdf_file, current_user
    )
    return SuccessResponse(data=result)


@router.delete("/books/{book_id}")
async def archive_book(
    book_id: str,
    current_user=Depends(require_approved_publisher),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Soft-archive a book (status -> ARCHIVED)."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    await service.archive_book(book_id, current_user)
    return SuccessResponse(data={"message": "Book archived."})


@router.post("/books/{book_id}/submit")
async def submit_book(
    book_id: str,
    current_user=Depends(require_approved_publisher),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Submit book for admin review (DRAFT/REJECTED -> PENDING)."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    await service.submit_book(book_id, current_user)
    return SuccessResponse(data={"message": "Book submitted for review."})


@router.post("/books/{book_id}/unarchive")
async def unarchive_book(
    book_id: str,
    current_user=Depends(require_approved_publisher),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Unarchive a book (ARCHIVED -> DRAFT)."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    await service.unarchive_book(book_id, current_user)
    return SuccessResponse(data={"message": "Book unarchived."})


@router.get("/analytics/downloads")
async def get_publisher_analytics(
    current_user=Depends(require_approved_publisher),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get publisher's download analytics summary."""
    from app.services.analytics_service import AnalyticsService

    service = AnalyticsService(db)
    result = await service.get_publisher_analytics(current_user)
    return SuccessResponse(data=result)


@router.get("/analytics/downloads/{book_id}")
async def get_book_analytics(
    book_id: str,
    period: str = "daily",
    from_date: str | None = None,
    to_date: str | None = None,
    current_user=Depends(require_approved_publisher),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get per-book download analytics."""
    from app.services.analytics_service import AnalyticsService

    service = AnalyticsService(db)
    result = await service.get_book_analytics(
        book_id, period, from_date, to_date, current_user
    )
    return SuccessResponse(data=result)
