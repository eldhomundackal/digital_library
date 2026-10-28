"""Schemas for downloads, history, and analytics."""

from pydantic import BaseModel

from app.schemas.book import BookListItem


class BookFileSummary(BaseModel):
    """Book metadata shown in download response."""

    book_id: str
    title: str
    file_name: str
    file_size_mb: float


class DownloadLimits(BaseModel):
    """Remaining download limits for a user."""

    daily_limit: int
    monthly_limit: int
    daily_remaining: int
    monthly_remaining: int
    daily_resets_at: str
    monthly_resets_at: str


class DownloadResponse(BaseModel):
    """Response for GET /books/{id}/download."""

    download_url: str
    expires_in: int
    expires_at: str
    book: BookFileSummary
    download_limits: DownloadLimits


class DownloadHistoryItem(BaseModel):
    """Row in download history list."""

    download_id: str
    book: BookListItem
    downloaded_at: str
    is_deleted: bool


class DownloadAnalyticsSummary(BaseModel):
    """Aggregate download counts across time periods."""

    total_downloads_all_time: int
    total_downloads_this_month: int
    total_downloads_this_week: int
    total_downloads_today: int


class ChartDataPoint(BaseModel):
    """Single data point for download chart."""

    date: str
    downloads: int


class BookDownloadAnalytics(BaseModel):
    """Analytics for a single book."""

    book: BookListItem
    summary: DownloadAnalyticsSummary
    chart_data: list[ChartDataPoint]
