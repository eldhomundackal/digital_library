"""Admin book management router — /admin/books endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_db, require_roles
from app.schemas.book import RejectBookRequest
from app.schemas.common import SuccessResponse
from app.services.book_service import BookService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/admin/books", tags=["Admin Books"])

_STAFF_ROLES = ("staff", "admin", "superadmin")


@router.get("")
async def list_books(
    status: str | None = None,
    params: PaginationParams = Depends(),
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """List all books across all statuses."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    result = await service.list_approved_books(status, None, None, None, params)
    return SuccessResponse(data=result)


@router.get("/{book_id}")
async def get_book(
    book_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get full book detail."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    result = await service.get_book_detail(book_id, current_user)
    return SuccessResponse(data=result)


@router.post("/{book_id}/approve")
async def approve_book(
    book_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Approve a PENDING book."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    await service.approve_book(book_id, current_user)
    return SuccessResponse(data={"message": "Book approved."})


@router.post("/{book_id}/reject")
async def reject_book(
    book_id: str,
    payload: RejectBookRequest,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Reject a PENDING book with a reason."""
    storage = get_storage_provider()
    service = BookService(db, storage)
    await service.reject_book(book_id, payload.reason, current_user)
    return SuccessResponse(data={"message": "Book rejected."})
