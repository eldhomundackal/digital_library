"""Schemas for ratings, reviews, replies, and reports."""

from pydantic import BaseModel, Field

from app.schemas.auth import UserSummary


class ReplyResponse(BaseModel):
    """Single reply in a review response."""

    reply_id: str
    user: UserSummary
    comment: str
    is_publisher_response: bool
    is_edited: bool
    created_at: str


class ReviewResponse(BaseModel):
    """Full review with nested replies."""

    review_id: str
    book_id: str
    user: UserSummary
    rating: int
    comment: str
    is_edited: bool
    is_publisher_response: bool
    reply_count: int
    replies: list[ReplyResponse]
    created_at: str
    updated_at: str


class RatingSummary(BaseModel):
    """Rating statistics for a book."""

    average_rating: float
    total_ratings: int
    total_reviews: int
    rating_breakdown: dict[str, int]


class BookReviewsResponse(BaseModel):
    """Paginated reviews with rating summary."""

    summary: RatingSummary
    items: list[ReviewResponse]
    total: int
    page: int
    limit: int
    pages: int


class SubmitReviewRequest(BaseModel):
    """Body for POST /books/{id}/reviews."""

    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class SubmitReplyRequest(BaseModel):
    """Body for POST /reviews/{review_id}/replies."""

    comment: str


class ReportRequest(BaseModel):
    """Body for POST /reviews/{review_id}/report."""

    reason: str
    note: str | None = None
