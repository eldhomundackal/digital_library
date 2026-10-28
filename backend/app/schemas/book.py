"""Schemas for books, versions, authors, categories, and tags."""

from pydantic import BaseModel

from app.schemas.utils import LanguageSummary, PublisherSummary


class CategorySummary(BaseModel):
    """Minimal category info used in book responses."""

    category_id: str
    name: str
    slug: str


class TagSummary(BaseModel):
    """Minimal tag info used in book responses."""

    tag_id: str
    name: str
    slug: str
    status: str | None = None


class AuthorSummary(BaseModel):
    """Minimal author info used in book list items."""

    author_id: str
    first_name: str
    last_name: str
    avatar: str | None


class AuthorDetail(BaseModel):
    """Full author info including total books."""

    author_id: str
    first_name: str
    last_name: str
    bio: str | None
    avatar: str | None
    total_books: int


class AuthorInput(BaseModel):
    """Used when submitting a book — either existing author or new."""

    author_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None


class CreateBookRequest(BaseModel):
    """multipart/form-data body for POST /publisher/books."""

    title: str
    description: str
    category_id: int
    language_id: int
    page_count: int | None = None
    publication_year: int | None = None
    isbn: str | None = None
    version_label: str
    tag_ids: list[int] = []
    new_tags: list[str] = []
    authors: list[AuthorInput]


class BookVersionSummary(BaseModel):
    """Version summary used in book detail responses."""

    version_id: str
    version_number: int
    version_label: str
    is_current: bool
    status: str
    total_downloads: int
    approved_at: str | None


class PDFFileSummary(BaseModel):
    """PDF file metadata shown to all users (never includes URL)."""

    file_name: str
    file_size_mb: float


class ArchiveNotice(BaseModel):
    """Archive notice shown for inactive books."""

    is_archived: bool
    message: str
    archived_at: str


class BookListItem(BaseModel):
    """Row in the public book listing."""

    book_id: str
    title: str
    thumbnail: str
    description: str
    category: CategorySummary
    authors: list[AuthorSummary]
    publisher: PublisherSummary
    language: LanguageSummary
    average_rating: float
    total_ratings: int
    total_downloads: int
    publication_year: int | None
    created_at: str


class BookDetailResponse(BaseModel):
    """Full book detail response."""

    book_id: str
    title: str
    thumbnail: str
    description: str
    category: CategorySummary
    tags: list[TagSummary]
    authors: list[AuthorDetail]
    publisher: PublisherSummary
    language: LanguageSummary
    page_count: int | None
    publication_year: int | None
    isbn: str | None
    average_rating: float
    total_ratings: int
    total_downloads: int
    versions: list[BookVersionSummary]
    current_version: BookVersionSummary
    pdf_file: PDFFileSummary
    is_downloadable: bool
    status: str
    archive_notice: ArchiveNotice | None
    created_at: str


class PublisherBookListItem(BaseModel):
    """Row in the publisher's own book list."""

    book_id: str
    title: str
    thumbnail: str
    status: str
    total_downloads: int
    average_rating: float
    submitted_at: str | None
    approved_at: str | None
    rejection_reason: str | None
    is_resubmission: bool
    resubmission_count: int


class BookStatusSummary(BaseModel):
    """Status counts for the publisher book dashboard."""

    total: int
    draft: int
    pending: int
    approved: int
    rejected: int
    archived: int


class PublisherBookListResponse(BaseModel):
    """Paginated publisher book list with summary."""

    items: list[PublisherBookListItem]
    total: int
    page: int
    limit: int
    pages: int
    summary: BookStatusSummary


class RejectBookRequest(BaseModel):
    """Body for POST /admin/books/{id}/reject."""

    reason: str


class CreateAuthorRequest(BaseModel):
    """Body for POST /authors — multipart includes optional avatar UploadFile."""

    first_name: str
    last_name: str
    bio: str | None = None


class MergeAuthorsRequest(BaseModel):
    """Body for POST /admin/authors/merge."""

    primary_author_id: str
    duplicate_author_ids: list[str]
    reason: str
