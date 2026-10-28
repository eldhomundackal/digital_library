# Routers

All 118 endpoints wired to service calls. Routers are thin — no business logic, only HTTP concerns.

## Conventions

- Routers are **thin** — one line per endpoint: validate input, call service, return response
- All business logic lives in services
- Auth guards applied via `Depends(require_roles(...))` or `Depends(require_permission(...))`
- File uploads declared as `UploadFile` FastAPI parameters, not in Pydantic schemas
- Pagination params reused via `Depends(pagination_params)`

---

## `app/api/v1/auth.py`

```python
router = APIRouter(prefix="/auth", tags=["Auth"])

# POST /auth/register
# Body: RegisterRequest
# Auth: none
# Returns: SuccessResponse[RegisterResponse]
# Calls: auth_service.register(payload)
# Notes: role must be reader|publisher only
async def register(payload: RegisterRequest, auth_service=Depends()): ...

# POST /auth/verify-email/send
# Body: SendOTPRequest
# Auth: none
# Returns: SuccessResponse
# Calls: auth_service.send_email_otp(email, otp_type="email_verify")
async def send_verify_email_otp(payload: SendOTPRequest): ...

# POST /auth/verify-email/confirm
# Body: VerifyEmailRequest
# Auth: none
# Returns: SuccessResponse[VerifyEmailResponse]
# Calls: auth_service.verify_email(email, otp)
async def confirm_email(payload: VerifyEmailRequest): ...

# POST /auth/login
# Body: LoginRequest
# Auth: none
# Returns: SuccessResponse[LoginResponse]
# Side effect: sets HttpOnly cookie refresh_token
# Calls: auth_service.login(email, password, response)
async def login(payload: LoginRequest, response: Response): ...

# POST /auth/logout
# Auth: Bearer token
# Returns: SuccessResponse
# Side effect: clears refresh_token cookie, blacklists token in Redis
# Calls: auth_service.logout(refresh_token_from_cookie)
async def logout(request: Request, response: Response): ...

# POST /auth/refresh
# Auth: HttpOnly cookie refresh_token
# Returns: SuccessResponse[RefreshResponse]
# Calls: auth_service.refresh_access_token(refresh_token)
async def refresh(request: Request): ...

# POST /auth/forgot-password
# Body: ForgotPasswordRequest
# Auth: none
# Returns: SuccessResponse (always same message, email enumeration safe)
# Calls: auth_service.send_email_otp(email, otp_type="password_reset")
async def forgot_password(payload: ForgotPasswordRequest): ...

# POST /auth/forgot-password/verify
# Body: VerifyResetOTPRequest
# Auth: none
# Returns: SuccessResponse[VerifyResetOTPResponse]
# Calls: auth_service.verify_reset_otp(email, otp)
async def verify_reset_otp(payload: VerifyResetOTPRequest): ...

# POST /auth/reset-password
# Body: ResetPasswordRequest
# Auth: none
# Returns: SuccessResponse
# Calls: auth_service.reset_password(reset_session_token, password)
async def reset_password(payload: ResetPasswordRequest): ...

# GET /auth/external/login
# Auth: none
# Returns: RedirectResponse to IDP authorization URL
# Calls: auth_service.get_authorization_url()
# Notes: 404 when AUTH_PROVIDER=local
async def external_login(): ...

# GET /auth/external/callback
# Query: code, state
# Auth: none
# Returns: SuccessResponse[LoginResponse]
# Side effect: sets HttpOnly cookie refresh_token
# Calls: auth_service.handle_external_callback(code, state)
async def external_callback(code: str, state: str, response: Response): ...

# POST /auth/external/logout
# Auth: Bearer token
# Returns: SuccessResponse
# Calls: auth_service.external_logout()
async def external_logout(): ...
```

---

## `app/api/v1/users.py`

```python
router = APIRouter(prefix="/users", tags=["Users"])

# GET /users/me
# Auth: any logged-in user
# Returns: SuccessResponse[ReaderProfileResponse | PublisherProfileResponse | StaffProfileResponse]
# Calls: user_service.get_my_profile(current_user)
async def get_my_profile(current_user=Depends(get_current_user)): ...

# PATCH /users/me
# Body: UpdateReaderProfileRequest | UpdatePublisherProfileRequest
# Auth: any logged-in user
# Returns: SuccessResponse[updated profile]
# Calls: user_service.update_my_profile(current_user, payload)
async def update_my_profile(payload: dict, current_user=Depends(get_current_user)): ...

# DELETE /users/me
# Auth: any logged-in user
# Returns: SuccessResponse
# Calls: user_service.deactivate_my_account(current_user)
async def deactivate_my_account(current_user=Depends(get_current_user)): ...

# PATCH /users/me/avatar
# Body: multipart/form-data file
# Auth: any logged-in user
# Returns: SuccessResponse[AvatarResponse]
# Calls: user_service.update_avatar(current_user, file)
async def update_avatar(file: UploadFile, current_user=Depends(get_current_user)): ...

# PATCH /users/me/password
# Body: UpdatePasswordRequest
# Auth: any logged-in user
# Returns: SuccessResponse
# Notes: 400 if AUTH_PROVIDER != local
# Calls: user_service.change_password(current_user, payload)
async def change_password(payload: UpdatePasswordRequest, current_user=Depends(get_current_user)): ...

# GET /users/me/notifications
# Auth: any logged-in user
# Query: is_read, page, limit
# Returns: SuccessResponse[NotificationListResponse]
# Calls: notification_service.get_my_notifications(current_user, filters)
async def get_notifications(current_user=Depends(get_current_user), params=Depends(pagination_params)): ...

# PATCH /users/me/notifications/preferences
# Body: NotificationPreferencesRequest
# Auth: any logged-in user
# Returns: SuccessResponse[NotificationPreferencesResponse]
# Calls: notification_service.update_preferences(current_user, payload)
async def update_notification_prefs(payload: NotificationPreferencesRequest, current_user=Depends(get_current_user)): ...

# POST /users/me/notifications/read-all
# Auth: any logged-in user
# Returns: SuccessResponse
# Calls: notification_service.mark_all_read(current_user)
async def mark_all_notifications_read(current_user=Depends(get_current_user)): ...

# PATCH /users/me/notifications/{id}/read
# Auth: any logged-in user
# Returns: SuccessResponse
# Calls: notification_service.mark_read(notification_id, current_user)
async def mark_notification_read(id: str, current_user=Depends(get_current_user)): ...

# DELETE /users/me/notifications/{id}
# Auth: any logged-in user
# Returns: SuccessResponse
# Calls: notification_service.delete_notification(id, current_user)
async def delete_notification(id: str, current_user=Depends(get_current_user)): ...

# GET /users/me/downloads
# Auth: reader | publisher
# Query: page, limit
# Returns: SuccessResponse[PaginatedResponse[DownloadHistoryItem]]
# Calls: download_service.get_my_history(current_user, params)
async def get_download_history(current_user=Depends(get_current_user), params=Depends(pagination_params)): ...

# DELETE /users/me/downloads/{book_id}
# Auth: reader | publisher
# Returns: SuccessResponse
# Calls: download_service.soft_delete_history(book_id, current_user)
async def delete_download_history(book_id: str, current_user=Depends(get_current_user)): ...
```

---

## `app/api/v1/books.py` — Public book endpoints

```python
router = APIRouter(prefix="/books", tags=["Books"])

# GET /books
# Auth: none
# Query: search, category_id, tag_id, language_id, publication_year,
#        sort_by (latest|popular|rating), page, limit
# Returns: SuccessResponse[PaginatedResponse[BookListItem]]
# Calls: book_service.list_approved_books(filters, pagination)
async def list_books(filters=Depends(book_filters), params=Depends(pagination_params)): ...

# GET /books/{id}
# Auth: none (anonymous sees metadata only; logged-in sees download button)
# Returns: SuccessResponse[BookDetailResponse]
# Calls: book_service.get_book_detail(book_uuid, current_user)
async def get_book(id: str, current_user=Depends(get_optional_user)): ...

# GET /books/{id}/download
# Auth: reader | publisher (not staff/admin)
# Returns: SuccessResponse[DownloadResponse]
# Calls: download_service.generate_download_url(book_uuid, current_user)
async def download_book(id: str, current_user=Depends(require_roles("reader", "publisher"))): ...

# GET /books/{id}/reviews
# Auth: none
# Query: sort_by, page, limit
# Returns: SuccessResponse[BookReviewsResponse]
# Calls: review_service.get_book_reviews(book_uuid, sort, pagination)
async def get_book_reviews(id: str, sort_by: str = "latest", params=Depends(pagination_params)): ...

# POST /books/{id}/reviews
# Auth: reader | publisher
# Body: SubmitReviewRequest
# Returns: SuccessResponse[ReviewResponse]
# Calls: review_service.submit_review(book_uuid, payload, current_user)
async def submit_review(id: str, payload: SubmitReviewRequest, current_user=Depends(require_roles("reader", "publisher"))): ...

# PATCH /books/{id}/reviews
# Auth: reader | publisher (own review only)
# Body: SubmitReviewRequest
# Returns: SuccessResponse[ReviewResponse]
# Calls: review_service.update_review(book_uuid, payload, current_user)
async def update_review(id: str, payload: SubmitReviewRequest, current_user=Depends(require_roles("reader", "publisher"))): ...

# DELETE /books/{id}/reviews
# Auth: reader | publisher (own review only)
# Returns: SuccessResponse
# Calls: review_service.delete_review(book_uuid, current_user)
async def delete_review(id: str, current_user=Depends(require_roles("reader", "publisher"))): ...

# GET /books/{id}/reviews/me
# Auth: reader | publisher
# Returns: SuccessResponse[ReviewResponse | None]
# Calls: review_service.get_my_review(book_uuid, current_user)
async def get_my_review(id: str, current_user=Depends(require_roles("reader", "publisher"))): ...
```

---

## `app/api/v1/publisher_books.py` — Publisher book management

```python
router = APIRouter(prefix="/publisher", tags=["Publisher Books"])
# All endpoints: Depends(require_roles("publisher")) + KYC approved check

# GET /publisher/books
# Query: status, page, limit
# Returns: SuccessResponse[PublisherBookListResponse]
# Calls: book_service.get_publisher_books(current_user, filters)
async def list_my_books(status: str | None, params=Depends(pagination_params), current_user=Depends(require_approved_publisher)): ...

# POST /publisher/books
# Body: multipart/form-data (CreateBookRequest fields + thumbnail + pdf_file)
# Returns: SuccessResponse[BookDetailResponse] with status=DRAFT
# Calls: book_service.create_book(payload, files, current_user)
async def create_book(payload: CreateBookRequest = Depends(), thumbnail: UploadFile = File(...), pdf_file: UploadFile = File(...), current_user=Depends(require_approved_publisher)): ...

# GET /publisher/books/{id}
# Returns: SuccessResponse[BookDetailResponse] (all statuses visible)
# Calls: book_service.get_publisher_book_detail(book_uuid, current_user)
async def get_my_book(id: str, current_user=Depends(require_approved_publisher)): ...

# PATCH /publisher/books/{id}
# Body: multipart/form-data (partial update)
# Notes: only allowed when status=DRAFT or REJECTED
# Returns: SuccessResponse[BookDetailResponse]
# Calls: book_service.update_book(book_uuid, payload, files, current_user)
async def update_book(id: str, current_user=Depends(require_approved_publisher)): ...

# DELETE /publisher/books/{id}
# Notes: soft-archives the book (status -> ARCHIVED)
# Returns: SuccessResponse
# Calls: book_service.archive_book(book_uuid, current_user)
async def archive_book(id: str, current_user=Depends(require_approved_publisher)): ...

# POST /publisher/books/{id}/submit
# Notes: DRAFT or REJECTED -> PENDING; validates all required fields present
# Returns: SuccessResponse
# Calls: book_service.submit_book(book_uuid, current_user)
async def submit_book(id: str, current_user=Depends(require_approved_publisher)): ...

# POST /publisher/books/{id}/unarchive
# Notes: ARCHIVED -> DRAFT
# Returns: SuccessResponse
# Calls: book_service.unarchive_book(book_uuid, current_user)
async def unarchive_book(id: str, current_user=Depends(require_approved_publisher)): ...

# GET /publisher/analytics/downloads
# Returns: SuccessResponse[DownloadAnalyticsSummary + per-book breakdown]
# Calls: analytics_service.get_publisher_analytics(current_user)
async def get_publisher_analytics(current_user=Depends(require_approved_publisher)): ...

# GET /publisher/analytics/downloads/{book_id}
# Query: period (daily|weekly|monthly), from, to
# Returns: SuccessResponse[BookDownloadAnalytics]
# Calls: analytics_service.get_book_analytics(book_uuid, period, from, to, current_user)
async def get_book_analytics(book_id: str, period: str = "daily", current_user=Depends(require_approved_publisher)): ...
```

---

## `app/api/v1/reviews.py` — Replies and reports

```python
router = APIRouter(prefix="/reviews", tags=["Reviews"])

# POST /reviews/{review_id}/replies
# Auth: reader | publisher
# Body: SubmitReplyRequest
# Returns: SuccessResponse[ReplyResponse]
# Notes: is_publisher_response auto-set if user is book's publisher
# Calls: review_service.submit_reply(review_id, payload, current_user)
async def submit_reply(review_id: str, payload: SubmitReplyRequest, current_user=Depends(require_roles("reader", "publisher"))): ...

# PATCH /reviews/{review_id}/replies/{id}
# Auth: owner of reply only
# Returns: SuccessResponse[ReplyResponse]
# Calls: review_service.update_reply(review_id, reply_id, payload, current_user)
async def update_reply(review_id: str, id: str, payload: SubmitReplyRequest, current_user=Depends(get_current_user)): ...

# DELETE /reviews/{review_id}/replies/{id}
# Auth: owner of reply only
# Returns: SuccessResponse
# Calls: review_service.delete_reply(review_id, reply_id, current_user)
async def delete_reply(review_id: str, id: str, current_user=Depends(get_current_user)): ...

# POST /reviews/{review_id}/report
# Auth: reader | publisher
# Body: ReportRequest
# Returns: SuccessResponse
# Notes: one report per user per review; 400 if already reported
# Calls: review_service.report_review(review_id, payload, current_user)
async def report_review(review_id: str, payload: ReportRequest, current_user=Depends(require_roles("reader", "publisher"))): ...

# POST /reviews/{review_id}/replies/{id}/report
# Auth: reader | publisher
# Body: ReportRequest
# Returns: SuccessResponse
# Calls: review_service.report_reply(review_id, reply_id, payload, current_user)
async def report_reply(review_id: str, id: str, payload: ReportRequest, current_user=Depends(require_roles("reader", "publisher"))): ...
```

---

## `app/api/v1/publishers.py` — Public publisher pages

```python
router = APIRouter(prefix="/publishers", tags=["Publishers"])

# GET /publishers/{id}
# Auth: none
# Returns: SuccessResponse[PublisherProfileDetail]
# Calls: publisher_service.get_public_profile(publisher_uuid)
async def get_publisher(id: str): ...

# GET /publishers/{id}/books
# Auth: none
# Query: page, limit
# Returns: SuccessResponse[PaginatedResponse[BookListItem]]
# Calls: book_service.get_books_by_publisher(publisher_uuid, pagination)
async def get_publisher_books(id: str, params=Depends(pagination_params)): ...
```

---

## `app/api/v1/authors.py`

```python
router = APIRouter(prefix="/authors", tags=["Authors"])

# GET /authors
# Auth: none
# Query: search, page, limit
# Returns: SuccessResponse[PaginatedResponse[AuthorSummary]]
# Calls: author_service.list_authors(search, pagination)
async def list_authors(search: str | None = None, params=Depends(pagination_params)): ...

# GET /authors/{id}
# Auth: none
# Returns: SuccessResponse[AuthorDetail + books list]
# Calls: author_service.get_author_detail(author_uuid)
async def get_author(id: str): ...

# POST /authors
# Auth: publisher (approved KYC)
# Body: multipart/form-data CreateAuthorRequest + optional avatar
# Returns: SuccessResponse[AuthorDetail]
# Notes: slug-match check for duplicates before creating
# Calls: author_service.create_author(payload, avatar_file, current_user)
async def create_author(payload: CreateAuthorRequest = Depends(), avatar: UploadFile | None = None, current_user=Depends(require_approved_publisher)): ...

# PATCH /authors/{id}
# Auth: publisher who created the author
# Returns: SuccessResponse[AuthorDetail]
# Calls: author_service.update_author(author_uuid, payload, current_user)
async def update_author(id: str, payload: CreateAuthorRequest, current_user=Depends(require_approved_publisher)): ...
```

---

## `app/api/v1/kyc.py`

```python
router = APIRouter(prefix="/kyc", tags=["KYC"])
# All: Depends(require_roles("publisher"))

# GET /kyc
# Returns: SuccessResponse[KYCDashboardResponse]
# Calls: kyc_service.get_my_kyc(current_user)
async def get_kyc_dashboard(current_user=Depends(require_roles("publisher"))): ...

# POST /kyc/documents/{type}
# Body: multipart/form-data file (PDF only, max 10MB)
# Path: type in [government_id, publishing_license, business_registration]
# Returns: SuccessResponse[KYCDocumentDetail]
# Calls: kyc_service.upload_document(document_type, file, current_user)
async def upload_document(type: str, file: UploadFile, current_user=Depends(require_roles("publisher"))): ...

# DELETE /kyc/documents/{type}
# Notes: only allowed when overall_status=INCOMPLETE
# Returns: SuccessResponse
# Calls: kyc_service.remove_document(document_type, current_user)
async def remove_document(type: str, current_user=Depends(require_roles("publisher"))): ...

# POST /kyc/submit
# Body: KYCSubmitRequest (terms_accepted must be True)
# Notes: all 3 docs must be UPLOADED; validates before submitting
# Returns: SuccessResponse
# Calls: kyc_service.submit_kyc(payload, current_user)
async def submit_kyc(payload: KYCSubmitRequest, current_user=Depends(require_roles("publisher"))): ...

# POST /kyc/resubmit
# Body: multipart/form-data (only flagged document types accepted)
# Returns: SuccessResponse
# Calls: kyc_service.resubmit_documents(files, current_user)
async def resubmit_documents(current_user=Depends(require_roles("publisher"))): ...
```

---

## `app/api/v1/admin/` — All admin routers

```python
# All admin routers share: Depends(require_roles("staff", "admin", "superadmin"))
# Staff also needs: Depends(require_permission("manage_X")) per endpoint group

# admin/kyc.py
# GET  /admin/kyc                              list, query ?status
# GET  /admin/kyc/{id}                         detail with full document URLs
# POST /admin/kyc/{id}/approve                 approve entire application
# POST /admin/kyc/{id}/reject                  Body: reason
# PATCH /admin/kyc/{id}/documents/{type}/approve
# PATCH /admin/kyc/{id}/documents/{type}/reject  Body: reason
# POST /admin/kyc/{id}/request-resubmission    Body: KYCRequestResubmissionRequest
# All call: kyc_service.*

# admin/books.py
# GET  /admin/books                            list all statuses
# GET  /admin/books/{id}                       full detail
# POST /admin/books/{id}/approve               -> triggers notification to publisher
# POST /admin/books/{id}/reject                Body: reason -> triggers notification
# All call: book_service.*

# admin/reviews.py
# GET    /admin/reviews                        all reviews
# GET    /admin/reviews/reported               ?status=PENDING|REVIEWED|DISMISSED
# DELETE /admin/reviews/{review_id}            removes review + all replies + closes reports
# DELETE /admin/reviews/{review_id}/replies/{id}
# POST   /admin/reviews/{review_id}/dismiss-report  Body: note
# All call: review_service.*

# admin/tags.py
# GET  /admin/tags                             all tags including PENDING
# POST /admin/tags/{id}/approve
# POST /admin/tags/{id}/reject
# PATCH /admin/tags/{id}                       edit name/slug
# DELETE /admin/tags/{id}                      soft deactivate
# All call: book_service.manage_tag(*)

# admin/categories.py
# POST   /admin/categories                     Body: name, slug
# PATCH  /admin/categories/{id}
# DELETE /admin/categories/{id}                soft deactivate
# All call: book_service.manage_category(*)

# admin/authors.py
# PATCH /admin/authors/{id}
# DELETE /admin/authors/{id}                   soft deactivate
# POST  /admin/authors/merge                   Body: MergeAuthorsRequest
# All call: author_service.*

# admin/users.py
# GET  /admin/users                            ?role, ?is_active, page, limit
# GET  /admin/users/{id}
# PATCH /admin/users/{id}
# POST /admin/users/{id}/activate
# POST /admin/users/{id}/deactivate
# POST /admin/users/create-staff               admin|superadmin only
# POST /admin/users/create-admin               superadmin only
# All call: user_service.*

# admin/utils.py
# POST/PATCH/DELETE /admin/utils/countries
# POST/PATCH/DELETE /admin/utils/countries/{id}/cities
# POST/PATCH/DELETE /admin/utils/cities/{id}
# POST/PATCH/DELETE /admin/utils/languages
# All call: utils_service.*

# admin/dashboard.py
# GET /admin/dashboard                         calls admin_service.get_dashboard()

# admin/audit.py
# GET /admin/audit-log                         ?action, ?performed_by, ?from, ?to, page, limit
#                                              admin|superadmin only
#                                              calls admin_service.get_audit_log(filters)

# admin/activity.py
# GET   /admin/activity-feed                   ?type, ?is_read, page, limit
# PATCH /admin/activity-feed/{id}/read
# POST  /admin/activity-feed/read-all
# All call: admin_service.*

# admin/notifications.py
# GET  /admin/notifications
# POST /admin/notifications/read-all
# PATCH /admin/notifications/{id}/read
# All call: notification_service.*

# admin/analytics.py
# GET /admin/analytics/downloads                platform-wide
# GET /admin/analytics/downloads/{book_id}      any book
# GET /admin/analytics/users/{user_id}/downloads  any user
# All call: analytics_service.*
```

---

## `app/api/v1/categories.py` and `app/api/v1/tags.py`

```python
# categories.py
# GET /categories
# Auth: none
# Returns: list of active categories with total_books count
# Calls: book_service.list_categories()

# tags.py
# GET /tags
# Auth: none
# Returns: list of APPROVED active tags with total_books count
# Calls: book_service.list_approved_tags()
```

---

## `app/api/v1/utils.py` — Public utility endpoints

```python
# GET /utils/countries        no auth, returns active countries
# GET /utils/countries/{id}/cities   no auth, returns active cities for country
# GET /utils/languages        no auth, returns active languages
# All call: utils_service.*
```

---

## Shared dependency helpers (`app/core/dependencies.py`)

```python
# get_current_user(token) -> User
#   Decodes JWT, loads User from DB, raises 401 if invalid/expired

# get_optional_user(token) -> User | None
#   Same as above but returns None instead of raising (for public endpoints)

# require_roles(*roles) -> User
#   Calls get_current_user, raises 403 if user.role not in roles

# require_permission(permission) -> User
#   Calls get_current_user; admin/superadmin pass; staff checked against StaffPermission

# require_approved_publisher -> User
#   require_roles("publisher") + check publisher_profile.kyc_status == APPROVED

# pagination_params(page: int = 1, limit: int = 20) -> PaginationParams
#   Clamps limit to max 100

# book_filters(search, category_id, tag_id, language_id, publication_year, sort_by) -> BookFilters
#   Packages query params into a typed dataclass
```
