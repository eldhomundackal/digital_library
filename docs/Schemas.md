# Pydantic Schemas

All request and response schemas. Every router imports from here — never define schemas inline in routers.

---

## `app/schemas/common.py` — Shared base schemas

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Any

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str | None = None
    data: T | None = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: dict[str, list[str]] | None = None

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int
    pages: int
```

---

## `app/schemas/auth.py`

```python
from pydantic import BaseModel, EmailStr, field_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str          # min 8 chars, validated
    confirm_password: str
    first_name: str
    last_name: str
    role: str              # "reader" | "publisher" only; staff/admin never via API

    @field_validator("role")
    def role_must_be_public(cls, v): ...
    # raises ValueError if role not in ["reader", "publisher"]

    @field_validator("confirm_password")
    def passwords_match(cls, v, values): ...

class RegisterResponse(BaseModel):
    user_id: str           # uuid
    email: str
    role: str
    is_email_verified: bool

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int        # seconds

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserSummary"    # see user schemas
    # refresh_token set as HttpOnly cookie by router, not in body

class RefreshResponse(BaseModel):
    access_token: str
    expires_in: int

class SendOTPRequest(BaseModel):
    email: EmailStr

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str               # 6-digit string

class VerifyEmailResponse(BaseModel):
    user_id: str
    role: str
    next_step: str         # "kyc_required" | "login"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyResetOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class VerifyResetOTPResponse(BaseModel):
    reset_session_token: str
    expires_in: int

class ResetPasswordRequest(BaseModel):
    reset_session_token: str
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    def passwords_match(cls, v, values): ...

class OIDCCallbackRequest(BaseModel):
    code: str
    state: str
```

---

## `app/schemas/user.py`

```python
from pydantic import BaseModel
from datetime import date

class UserSummary(BaseModel):
    """Minimal user info embedded in login response and notifications."""
    user_id: str
    email: str
    role: str
    is_first_login: bool
    profile_completion: int | None   # readers only
    kyc_status: str | None          # publishers only

class ReaderProfileResponse(BaseModel):
    user_id: str
    email: str
    role: str = "reader"
    is_email_verified: bool
    is_active: bool
    profile_completion: int
    created_at: str
    profile: "ReaderProfileDetail"

class ReaderProfileDetail(BaseModel):
    first_name: str
    last_name: str
    avatar: str | None
    bio: str | None
    date_of_birth: str | None
    gender: str | None
    country: "CountrySummary | None"
    city: "CitySummary | None"
    preferred_language: "LanguageSummary | None"
    preferred_categories: list["CategorySummary"]
    preferred_tags: list["TagSummary"]
    occupation: str | None

class UpdateReaderProfileRequest(BaseModel):
    """All fields optional — PATCH semantics."""
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    date_of_birth: str | None = None   # YYYY-MM-DD
    gender: str | None = None
    country_id: int | None = None
    city_id: int | None = None
    language_id: int | None = None
    preferred_category_ids: list[int] | None = None
    preferred_tag_ids: list[int] | None = None
    occupation: str | None = None

class PublisherProfileResponse(BaseModel):
    user_id: str
    email: str
    role: str = "publisher"
    is_email_verified: bool
    is_active: bool
    kyc_status: str
    created_at: str
    profile: "PublisherProfileDetail"

class PublisherProfileDetail(BaseModel):
    display_name: str
    bio: str | None
    logo: str | None
    website: str | None
    social_links: "SocialLinks"
    total_books: int
    joined_date: str
    is_verified: bool

class SocialLinks(BaseModel):
    twitter: str | None = None
    linkedin: str | None = None
    facebook: str | None = None
    instagram: str | None = None

class UpdatePublisherProfileRequest(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    website: str | None = None
    social_links: SocialLinks | None = None

class StaffProfileResponse(BaseModel):
    user_id: str
    email: str
    role: str
    is_active: bool
    created_at: str
    profile: "StaffProfileDetail"

class StaffProfileDetail(BaseModel):
    first_name: str
    last_name: str
    permissions: list[str]

class CreateStaffRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    permissions: list[str]     # list of permission enum values

class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class NotificationPreferencesRequest(BaseModel):
    reply_notifications: bool

class AvatarResponse(BaseModel):
    avatar_url: str
```

---

## `app/schemas/kyc.py`

```python
from pydantic import BaseModel

class KYCDocumentDetail(BaseModel):
    document_id: str | None
    type: str
    label: str
    status: str
    file_url: str | None
    file_name: str | None
    uploaded_at: str | None
    rejection_reason: str | None

class KYCDashboardResponse(BaseModel):
    kyc_id: str
    overall_status: str
    submitted_at: str | None
    reviewed_at: str | None
    terms_accepted: bool
    terms_accepted_at: str | None
    documents: dict[str, KYCDocumentDetail]   # keyed by document_type
    can_submit: bool
    resubmission_required: list[str]          # document types needing reupload

class KYCSubmitRequest(BaseModel):
    terms_accepted: bool

class KYCRejectDocumentRequest(BaseModel):
    reason: str

class KYCRequestResubmissionRequest(BaseModel):
    documents: list["DocumentRejection"]
    note: str | None = None

class DocumentRejection(BaseModel):
    type: str
    reason: str

class KYCListItem(BaseModel):
    kyc_id: str
    publisher: "PublisherSummary"
    overall_status: str
    submitted_at: str
    documents_summary: "DocumentsSummary"

class DocumentsSummary(BaseModel):
    total: int
    approved: int
    pending: int
    rejected: int
```

---

## `app/schemas/book.py`

```python
from pydantic import BaseModel

class AuthorInput(BaseModel):
    """Used when submitting a book — either existing author or new."""
    author_id: int | None = None     # if existing
    first_name: str | None = None    # if new
    last_name: str | None = None
    bio: str | None = None

class CreateBookRequest(BaseModel):
    """multipart/form-data — files handled separately by FastAPI UploadFile."""
    title: str
    description: str
    category_id: int
    language_id: int
    page_count: int | None = None
    publication_year: int | None = None
    isbn: str | None = None
    version_label: str             # e.g. "1.0"
    tag_ids: list[int] = []        # existing approved tags
    new_tags: list[str] = []       # new tag names to suggest
    authors: list[AuthorInput]
    # thumbnail: UploadFile  — declared in router
    # pdf_file: UploadFile   — declared in router

class BookListItem(BaseModel):
    book_id: str
    title: str
    thumbnail: str
    description: str
    category: "CategorySummary"
    authors: list["AuthorSummary"]
    publisher: "PublisherSummary"
    language: "LanguageSummary"
    average_rating: float
    total_ratings: int
    total_downloads: int
    publication_year: int | None
    created_at: str

class BookDetailResponse(BaseModel):
    book_id: str
    title: str
    thumbnail: str
    description: str
    category: "CategorySummary"
    tags: list["TagSummary"]
    authors: list["AuthorDetail"]
    publisher: "PublisherSummary"
    language: "LanguageSummary"
    page_count: int | None
    publication_year: int | None
    isbn: str | None
    average_rating: float
    total_ratings: int
    total_downloads: int
    versions: list["BookVersionSummary"]  # dropdown data for old versions
    current_version: "BookVersionSummary"
    pdf_file: "PDFFileSummary"      # size only, never URL for non-auth users
    is_downloadable: bool
    status: str
    archive_notice: "ArchiveNotice | None"
    created_at: str

class BookVersionSummary(BaseModel):
    version_id: str
    version_number: int
    version_label: str
    is_current: bool
    status: str
    total_downloads: int
    approved_at: str | None

class PDFFileSummary(BaseModel):
    file_name: str
    file_size_mb: float

class ArchiveNotice(BaseModel):
    is_archived: bool
    message: str
    archived_at: str

class PublisherBookListItem(BaseModel):
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

class PublisherBookListResponse(BaseModel):
    items: list[PublisherBookListItem]
    total: int
    page: int
    limit: int
    pages: int
    summary: "BookStatusSummary"

class BookStatusSummary(BaseModel):
    total: int
    draft: int
    pending: int
    approved: int
    rejected: int
    archived: int

class RejectBookRequest(BaseModel):
    reason: str

class CategorySummary(BaseModel):
    category_id: str
    name: str
    slug: str

class TagSummary(BaseModel):
    tag_id: str
    name: str
    slug: str
    status: str | None = None   # only shown to publisher/admin

class AuthorSummary(BaseModel):
    author_id: str
    first_name: str
    last_name: str
    avatar: str | None

class AuthorDetail(BaseModel):
    author_id: str
    first_name: str
    last_name: str
    bio: str | None
    avatar: str | None
    total_books: int

class CreateAuthorRequest(BaseModel):
    first_name: str
    last_name: str
    bio: str | None = None
    # avatar: UploadFile — declared in router

class MergeAuthorsRequest(BaseModel):
    primary_author_id: str
    duplicate_author_ids: list[str]
    reason: str
```

---

## `app/schemas/review.py`

```python
from pydantic import BaseModel, Field

class SubmitReviewRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)   # always mandatory
    comment: str | None = None             # optional

class ReviewResponse(BaseModel):
    review_id: str
    book_id: str
    user: "UserSummary"
    rating: int
    comment: str
    is_edited: bool
    is_publisher_response: bool
    reply_count: int
    replies: list["ReplyResponse"]
    created_at: str
    updated_at: str

class ReplyResponse(BaseModel):
    reply_id: str
    user: "UserSummary"
    comment: str
    is_publisher_response: bool
    is_edited: bool
    created_at: str

class BookReviewsResponse(BaseModel):
    summary: "RatingSummary"
    items: list[ReviewResponse]
    total: int
    page: int
    limit: int
    pages: int

class RatingSummary(BaseModel):
    average_rating: float
    total_ratings: int
    total_reviews: int
    rating_breakdown: dict[str, int]   # {"5": 600, "4": 350, ...}

class SubmitReplyRequest(BaseModel):
    comment: str

class ReportRequest(BaseModel):
    reason: str    # SPAM | OFFENSIVE | MISLEADING | OTHER
    note: str | None = None
```

---

## `app/schemas/download.py`

```python
from pydantic import BaseModel

class DownloadResponse(BaseModel):
    download_url: str          # pre-signed S3 URL
    expires_in: int            # seconds (600)
    expires_at: str
    book: "BookFileSummary"
    download_limits: "DownloadLimits"

class BookFileSummary(BaseModel):
    book_id: str
    title: str
    file_name: str
    file_size_mb: float

class DownloadLimits(BaseModel):
    daily_limit: int
    monthly_limit: int
    daily_remaining: int
    monthly_remaining: int
    daily_resets_at: str
    monthly_resets_at: str

class DownloadHistoryItem(BaseModel):
    download_id: str
    book: "BookListItem"       # includes archive_notice if archived
    downloaded_at: str
    is_deleted: bool

class DownloadAnalyticsSummary(BaseModel):
    total_downloads_all_time: int
    total_downloads_this_month: int
    total_downloads_this_week: int
    total_downloads_today: int

class BookDownloadAnalytics(BaseModel):
    book: "BookListItem"
    summary: "DownloadAnalyticsSummary"
    chart_data: list["ChartDataPoint"]

class ChartDataPoint(BaseModel):
    date: str
    downloads: int
```

---

## `app/schemas/notification.py`

```python
from pydantic import BaseModel

class NotificationResponse(BaseModel):
    notification_id: str
    type: str
    title: str
    message: str
    is_read: bool
    is_grouped: bool
    group_count: int
    data: dict | None              # flexible payload per notification type
    created_at: str
    updated_at: str

class NotificationListResponse(BaseModel):
    unread_count: int
    items: list[NotificationResponse]
    total: int
    page: int
    limit: int
    pages: int

class NotificationPreferencesResponse(BaseModel):
    reply_notifications: bool
```

---

## `app/schemas/admin.py`

```python
from pydantic import BaseModel

class DashboardResponse(BaseModel):
    platform_overview: "PlatformOverview"
    pending_actions: "PendingActions"
    recent_activity: "RecentActivity"

class PlatformOverview(BaseModel):
    total_readers: int
    total_publishers: int
    total_books: int
    total_downloads: int
    new_registrations_today: int
    new_books_today: int

class PendingActions(BaseModel):
    kyc_applications: int
    book_approvals: int
    tag_approvals: int
    reported_reviews: int

class RecentActivity(BaseModel):
    latest_books: list[dict]
    latest_publishers: list[dict]
    latest_reported_reviews: list[dict]

class AuditLogResponse(BaseModel):
    audit_id: str
    action: str
    performed_by: "UserSummary"
    target: "AuditTarget"
    metadata: dict | None
    note: str | None
    ip_address: str | None
    performed_at: str

class AuditTarget(BaseModel):
    type: str
    id: str
    label: str

class ActivityFeedResponse(BaseModel):
    activity_id: str
    type: str
    category: str              # actionable | informational
    title: str
    message: str
    action_url: str | None
    actor: "ActivityActor"
    is_read: bool
    created_at: str

class ActivityActor(BaseModel):
    type: str
    id: str
    name: str

class AdminUserListItem(BaseModel):
    user_id: str
    email: str
    role: str
    is_active: bool
    created_at: str
    profile_summary: dict     # name/display_name depending on role
```

---

## `app/schemas/utils.py`

```python
from pydantic import BaseModel

class CountrySummary(BaseModel):
    country_id: str
    name: str
    iso_code: str

class CountryResponse(BaseModel):
    country_id: str
    name: str
    iso_code: str
    phone_code: str | None
    flag: str | None
    is_seeded: bool

class CitySummary(BaseModel):
    city_id: str
    name: str
    state: str | None

class CityResponse(BaseModel):
    city_id: str
    name: str
    state: str | None
    country: CountrySummary
    is_seeded: bool

class LanguageSummary(BaseModel):
    language_id: str
    name: str
    iso_code: str

class CreateCountryRequest(BaseModel):
    name: str
    iso_code: str
    phone_code: str | None = None
    flag: str | None = None

class CreateCityRequest(BaseModel):
    name: str
    state: str | None = None

class CreateLanguageRequest(BaseModel):
    name: str
    iso_code: str

class PublisherSummary(BaseModel):
    publisher_id: str
    display_name: str
    logo: str | None
    is_verified: bool
```
