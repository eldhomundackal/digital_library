from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success envelope for all API responses."""

    success: bool = True
    message: str | None = None
    data: T | None = None


class ErrorResponse(BaseModel):
    """Standard error envelope for all API error responses."""

    success: bool = False
    message: str
    errors: dict[str, list[str]] | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response with metadata."""

    items: list[T]
    total: int
    page: int
    limit: int
    pages: int
