# Services

All 11 service files with method signatures, pseudocode logic, error conditions and Redis/DB interactions.

## Conventions

- Every service method is `async`
- All DB access via injected `AsyncSession`
- Redis client injected for cache/limits/OTP
- Raise `HTTPException` for all user-facing errors
- Fire Celery tasks with `.delay()` — never await them in service methods
- Call `audit_action()` at the end of every admin mutating method
- Call `create_activity_feed_entry()` for any event that shows in the admin feed

---

## `app/services/auth_service.py`

```python
class AuthService:
    def __init__(self, db: AsyncSession, redis: Redis, auth_provider: BaseAuthProvider): ...

    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        # 1. Check email not already taken -> 400 if exists
        # 2. Hash password (local only)
        # 3. Generate user number via number_generator.generate("user")
        # 4. Create User row (role=payload.role, is_email_verified=False)
        # 5. Create ReaderProfile or PublisherProfile row
        # 6. For publisher: create KYCApplication row (status=INCOMPLETE)
        # 7. send_otp_email.delay(email, otp_type="email_verify")
        # 8. Return RegisterResponse

    async def send_email_otp(self, email: str, otp_type: str) -> None:
        # 1. Check user exists -> 404 if not
        # 2. Generate 6-digit OTP
        # 3. Store in Redis: otp:{otp_type}:{email} -> {otp, attempts:0} TTL 10min
        # 4. send_otp_email.delay(email, otp, otp_type)

    async def verify_email(self, email: str, otp: str) -> VerifyEmailResponse:
        # 1. Load OTP from Redis -> 400 if not found (expired)
        # 2. Check attempts < 5 -> 429 if exceeded, force resend
        # 3. Compare OTP -> increment attempts in Redis if wrong -> 400
        # 4. Delete OTP from Redis
        # 5. Set user.is_email_verified = True
        # 6. Determine next_step: "kyc_required" if publisher else "login"
        # 7. send_welcome_email.delay(user)
        # 8. Return VerifyEmailResponse

    async def login(self, email: str, password: str, response: Response) -> LoginResponse:
        # 1. Load user by email -> 401 if not found
        # 2. Check user.is_active -> 403 if deactivated
        # 3. Check is_email_verified -> 403 with message
        # 4. Verify password hash -> 401 if wrong
        # 5. Update last_login_at, set is_first_login=False after first
        # 6. Create JWT access token (15min)
        # 7. Create refresh token (7 days) -> set as HttpOnly cookie on response
        # 8. Store refresh token in Redis for blacklist checking
        # 9. Return LoginResponse (access token in body only)

    async def logout(self, refresh_token: str, response: Response) -> None:
        # 1. Blacklist refresh token in Redis
        # 2. Clear HttpOnly cookie on response

    async def refresh_access_token(self, refresh_token: str) -> RefreshResponse:
        # 1. Check token not blacklisted in Redis -> 401
        # 2. Decode refresh token -> 401 if expired/invalid
        # 3. Load user -> 401 if not found or inactive
        # 4. Issue new access token
        # 5. Return RefreshResponse

    async def verify_reset_otp(self, email: str, otp: str) -> VerifyResetOTPResponse:
        # Same OTP check flow as verify_email
        # On success: generate short-lived reset_session_token (10min)
        # Store in Redis: reset_session:{token} -> email
        # Return token

    async def reset_password(self, reset_session_token: str, password: str) -> None:
        # 1. Load email from Redis by reset_session_token -> 400 if expired
        # 2. Delete reset session from Redis
        # 3. Hash new password
        # 4. Update user.hashed_password
        # 5. Blacklist all existing refresh tokens for this user (force re-login)

    async def get_authorization_url(self) -> str:
        # Delegates to auth_provider.get_authorization_url()
        # Raises 404 if AUTH_PROVIDER=local

    async def handle_external_callback(self, code: str, state: str, response: Response) -> LoginResponse:
        # 1. auth_provider.handle_callback(code, state) -> token
        # 2. auth_provider.get_user_info(token) -> UserInfoSchema
        # 3. Find or create local User (match by idp_sub + auth_provider)
        # 4. If new user: create profile, send welcome email
        # 5. Issue app JWT tokens (same as local login)
        # 6. Set HttpOnly cookie
        # 7. Return LoginResponse
```

---

## `app/services/user_service.py`

```python
class UserService:
    def __init__(self, db: AsyncSession, storage: BaseStorageProvider): ...

    async def get_my_profile(self, user: User) -> ReaderProfileResponse | PublisherProfileResponse | StaffProfileResponse:
        # Load profile based on user.role and return typed response
        # Include profile_completion for readers
        # Include kyc_status for publishers

    async def update_my_profile(self, user: User, payload: dict) -> profile response:
        # Load correct profile model based on role
        # Apply only non-None fields (PATCH semantics)
        # For reader: recalculate profile_completion after update
        # For publisher: update social links as JSON-like fields
        # Save and return updated profile

    async def update_avatar(self, user: User, file: UploadFile) -> AvatarResponse:
        # 1. validate_file(file, "avatar")
        # 2. Delete old avatar from S3 if exists
        # 3. storage.upload(file, path=f"avatars/{user.uuid}.{ext}")
        # 4. Update profile.avatar with new URL
        # 5. Return AvatarResponse

    async def change_password(self, user: User, payload: UpdatePasswordRequest) -> None:
        # 1. Raise 400 if auth_provider != "local"
        # 2. Verify current_password against hash -> 400 if wrong
        # 3. Hash new_password
        # 4. Update user.hashed_password

    async def deactivate_my_account(self, user: User) -> None:
        # Soft delete: user.is_active=False, user.deleted_at=now()

    async def create_staff(self, payload: CreateStaffRequest, created_by: User) -> StaffProfileResponse:
        # 1. Require created_by.role in [admin, superadmin]
        # 2. Check email not taken
        # 3. Generate temp password
        # 4. Create User(role="staff") + StaffProfile + StaffPermission rows
        # 5. send_staff_welcome_email.delay(email, temp_password)
        # 6. audit_action("STAFF_CREATED", target=new_user, by=created_by)
        # 7. Return StaffProfileResponse

    async def create_admin(self, payload: CreateStaffRequest, created_by: User) -> StaffProfileResponse:
        # Same as create_staff but role="admin"
        # Require created_by.role == "superadmin"
        # audit_action("ADMIN_CREATED")

    async def calculate_profile_completion(self, profile: ReaderProfile) -> int:
        # Tier 1 done (always): 40%
        # Tier 2 all filled: 75%
        # Tier 3 all filled: 100%
        # Return appropriate percentage
```

---

## `app/services/kyc_service.py`

```python
class KYCService:
    def __init__(self, db: AsyncSession, storage: BaseStorageProvider): ...

    async def get_my_kyc(self, user: User) -> KYCDashboardResponse:
        # Load KYCApplication + KYCDocuments for this publisher
        # Compute can_submit: all 3 docs UPLOADED and terms not yet accepted
        # Compute resubmission_required: docs with status=REJECTED
        # Return dashboard response

    async def upload_document(self, doc_type: str, file: UploadFile, user: User) -> KYCDocumentDetail:
        # 1. Validate doc_type in allowed list
        # 2. validate_file(file, "kyc_doc") -> PDF only, max 10MB
        # 3. Check KYC status not PENDING or APPROVED -> 400
        # 4. Delete old file from S3 if exists
        # 5. storage.upload(file, path=f"kyc/{publisher.uuid}/{doc_type}.pdf")
        # 6. Upsert KYCDocument row (status=UPLOADED, uploaded_at=now())
        # 7. Return KYCDocumentDetail

    async def remove_document(self, doc_type: str, user: User) -> None:
        # 1. Check KYC overall_status == INCOMPLETE -> 400 otherwise
        # 2. Delete file from S3
        # 3. Reset KYCDocument to NOT_UPLOADED

    async def submit_kyc(self, terms_accepted: bool, user: User) -> None:
        # 1. Check terms_accepted=True -> 400 if not
        # 2. Check all 3 docs status=UPLOADED -> 400 if any missing
        # 3. Check overall_status not already PENDING/APPROVED -> 400
        # 4. Set all doc statuses to PENDING
        # 5. Set KYCApplication.overall_status=PENDING, submitted_at=now()
        # 6. Set terms_accepted=True, terms_accepted_at=now()
        # 7. Log KYCActionLog(action=SUBMITTED)
        # 8. send_kyc_status_email.delay(publisher, status="submitted")
        # 9. create_activity_feed_entry(type=KYC_NEW_APPLICATION)
        # 10. create_in_app_notification.delay(admin_users, KYC_NEW_APPLICATION)

    async def resubmit_documents(self, files: dict[str, UploadFile], user: User) -> None:
        # 1. Load resubmission_required list from KYC
        # 2. Validate: only accept doc types that are in resubmission_required -> 400 otherwise
        # 3. Upload each file to S3 (same path, overwrites)
        # 4. Set each doc status back to PENDING
        # 5. Set overall_status=RESUBMITTED
        # 6. Log KYCActionLog(action=RESUBMITTED)
        # 7. Notify admin/staff

    async def approve_kyc(self, kyc_id: str, admin: User) -> None:
        # 1. Load KYC -> 404 if not found
        # 2. Set all docs APPROVED, overall_status=APPROVED
        # 3. Set publisher_profile.is_verified=True, kyc_status=APPROVED
        # 4. Log KYCActionLog(action=APPROVED, performed_by=admin)
        # 5. send_kyc_status_email.delay(publisher, status="approved")
        # 6. create_in_app_notification.delay(publisher, KYC_APPROVED)
        # 7. audit_action("KYC_APPROVED", by=admin)

    async def reject_kyc(self, kyc_id: str, reason: str, admin: User) -> None:
        # 1. Set overall_status=REJECTED, rejection_reason=reason
        # 2. Log KYCActionLog(action=REJECTED)
        # 3. Notify publisher with reason
        # 4. audit_action("KYC_REJECTED", metadata={reason})

    async def approve_document(self, kyc_id: str, doc_type: str, admin: User) -> None:
        # Set doc.status=APPROVED, doc.reviewed_by=admin, doc.reviewed_at=now()
        # audit_action("KYC_DOCUMENT_APPROVED")

    async def reject_document(self, kyc_id: str, doc_type: str, reason: str, admin: User) -> None:
        # Set doc.status=REJECTED, doc.rejection_reason=reason
        # audit_action("KYC_DOCUMENT_REJECTED")

    async def request_resubmission(self, kyc_id: str, payload: KYCRequestResubmissionRequest, admin: User) -> None:
        # Set flagged docs to REJECTED with reasons
        # Set overall_status=REJECTED
        # Log KYCActionLog(action=RESUBMISSION_REQUESTED)
        # Notify publisher with list of flagged docs + reasons
        # audit_action("KYC_RESUBMISSION_REQUESTED")
```

---

## `app/services/book_service.py`

```python
class BookService:
    def __init__(self, db: AsyncSession, storage: BaseStorageProvider, redis: Redis): ...

    async def create_book(self, payload: CreateBookRequest, thumbnail: UploadFile, pdf_file: UploadFile, user: User) -> BookDetailResponse:
        # 1. validate_file(thumbnail, "thumbnail"); validate_file(pdf_file, "book_pdf")
        # 2. Generate book number: number_generator.generate("book")
        # 3. Create Book row
        # 4. version_number = 1; upload files to S3 under books/{uuid}/v1/
        # 5. Create BookVersion(version_number=1, version_label=payload.version_label, status=DRAFT)
        # 6. Set book.current_version_id = new version
        # 7. Handle authors: for each AuthorInput, find existing or create new
        # 8. Create BookAuthor junction rows
        # 9. Attach existing tags (by tag_id)
        # 10. Create new tag suggestions (status=PENDING) -> notify admin
        # 11. Log BookVersionActionLog(action=CREATED)
        # 12. Return BookDetailResponse

    async def submit_book(self, book_uuid: str, user: User) -> None:
        # 1. Load book + current version, verify owner
        # 2. Check status in [DRAFT, REJECTED] -> 400 otherwise
        # 3. Validate all required fields present on version
        # 4. Set version.status=PENDING, submitted_at=now()
        # 5. If resubmission: increment resubmission_count, set is_resubmission=True, clear rejection_reason
        # 6. Log BookVersionActionLog(action=SUBMITTED or RESUBMITTED)
        # 7. create_activity_feed_entry(BOOK_SUBMITTED or BOOK_RESUBMITTED)
        # 8. Notify admin/staff

    async def approve_book(self, book_uuid: str, admin: User) -> None:
        # 1. Load book + current version -> 404 if not found
        # 2. Set version.status=APPROVED, approved_at=now(), reviewed_by=admin
        # 3. Set version.is_current=True
        # 4. Increment category.total_books and tag.total_books
        # 5. Log action, notify publisher
        # 6. audit_action("BOOK_APPROVED", by=admin)
        # 7. Invalidate book cache in Redis

    async def reject_book(self, book_uuid: str, reason: str, admin: User) -> None:
        # 1. Set version.status=REJECTED, rejection_reason=reason
        # 2. Log action, notify publisher with reason
        # 3. audit_action("BOOK_REJECTED")

    async def archive_book(self, book_uuid: str, user: User) -> None:
        # 1. Verify user is book's publisher
        # 2. Set version.status=ARCHIVED, archived_at=now()
        # 3. Set book.is_active=False
        # 4. Log BookVersionActionLog(action=ARCHIVED)
        # 5. Decrement category.total_books
        # 6. Invalidate cache

    async def list_approved_books(self, filters: BookFilters, pagination: PaginationParams) -> PaginatedResponse:
        # Build query on BookVersion where status=APPROVED and book.is_active=True
        # Apply filters: category_id, tag_id, language_id, publication_year
        # Apply search: use search_vector @@ plainto_tsquery(search) if search provided
        # Apply sort: latest=created_at desc, popular=total_downloads desc, rating=average_rating desc
        # Paginate and return

    async def get_book_detail(self, book_uuid: str, user: User | None) -> BookDetailResponse:
        # Load Book + current BookVersion + authors + tags + publisher
        # If book.is_active=False:
        #   anonymous -> 404
        #   logged-in reader -> check if they downloaded it; if yes show with archive_notice; else 404
        # Build response; pdf_file shows only size (not URL) for all users
        # is_downloadable = user is not None and user.role in [reader, publisher]

    async def get_publisher_books(self, user: User, status: str | None, pagination) -> PublisherBookListResponse:
        # Load all BookVersions for publisher, optionally filtered by status
        # Include summary counts per status

    async def list_categories(self) -> list[CategorySummary]:
        # Return active categories with total_books count, cached in Redis

    async def list_approved_tags(self) -> list[TagSummary]:
        # Return APPROVED active tags with total_books count

    async def manage_tag(self, tag_id: str, action: str, admin: User, **kwargs) -> None:
        # action in [approve, reject, update, deactivate]
        # approve: set status=APPROVED; update tag.total_books
        # reject: set status=REJECTED
        # deactivate: soft delete
        # audit_action per action

    async def manage_category(self, action: str, admin: User, **kwargs) -> None:
        # CRUD for categories; soft delete on DELETE
        # audit_action per action
        # Invalidate category cache
```

---

## `app/services/author_service.py`

```python
class AuthorService:
    def __init__(self, db: AsyncSession, storage: BaseStorageProvider): ...

    async def create_author(self, payload: CreateAuthorRequest, avatar: UploadFile | None, user: User) -> AuthorDetail:
        # 1. Slug-match check: search existing authors by name -> warn if similar found
        # 2. If avatar: validate_file + storage.upload
        # 3. Create Author row (created_by_id=publisher_profile.id)
        # 4. Return AuthorDetail

    async def update_author(self, author_uuid: str, payload, user: User) -> AuthorDetail:
        # 1. Load author -> 404 if not found
        # 2. Check author.created_by_id == user.publisher_profile.id OR user.role in [admin, superadmin] -> 403
        # 3. Apply updates
        # 4. Return AuthorDetail

    async def merge_authors(self, primary_id: str, duplicate_ids: list[str], admin: User) -> dict:
        # 1. Load primary + duplicates -> 404 if any not found
        # 2. Reassign all BookAuthor rows from duplicates to primary
        # 3. Soft delete duplicate Author rows
        # 4. Recalculate primary.total_books
        # 5. audit_action("AUTHORS_MERGED")
        # 6. Return merge summary

    async def list_authors(self, search: str | None, pagination) -> PaginatedResponse:
        # Full text search on first_name + last_name if search provided
        # Return active authors with total_books count

    async def get_author_detail(self, author_uuid: str) -> AuthorDetail:
        # Load Author + their approved books
        # 404 if not found or inactive
```

---

## `app/services/review_service.py`

```python
class ReviewService:
    def __init__(self, db: AsyncSession): ...

    async def submit_review(self, book_uuid: str, payload: SubmitReviewRequest, user: User) -> ReviewResponse:
        # 1. Load book -> 404 if not found or not APPROVED
        # 2. Block publisher from rating own book -> 403
        # 3. Check no existing rating for this user+book -> 400 if exists (use update instead)
        # 4. Create Rating row
        # 5. Recompute book.average_rating and book.total_ratings
        # 6. If payload.comment: create Review row linked to Rating
        # 7. Return ReviewResponse (or silent SuccessResponse if rating-only)

    async def update_review(self, book_uuid: str, payload: SubmitReviewRequest, user: User) -> ReviewResponse:
        # 1. Load existing Rating for user+book -> 404 if not found
        # 2. Update Rating.score
        # 3. Recompute book average
        # 4. If Review exists: update comment, set is_edited=True
        # 5. If no Review and payload.comment given: create new Review
        # 6. Return updated ReviewResponse

    async def delete_review(self, book_uuid: str, user: User) -> None:
        # 1. Load Rating for user+book -> 404 if not found
        # 2. Soft delete Review if exists (is_active=False, deleted_at=now())
        # 3. Hard delete Rating (removes from average)
        # 4. Recompute book average_rating (score no longer counted)

    async def submit_reply(self, review_id: str, payload: SubmitReplyRequest, user: User) -> ReplyResponse:
        # 1. Load Review -> 404 if not found or not active
        # 2. Determine is_publisher_response:
        #    Load book -> check if user is publisher AND book.publisher_id == user.publisher_profile.id
        # 3. Create ReviewReply row
        # 4. Increment review.reply_count
        # 5. If reply_notifications enabled for review author: create_in_app_notification + email
        # 6. Return ReplyResponse

    async def report_review(self, review_id: str, payload: ReportRequest, user: User) -> None:
        # 1. Load Review -> 404 if not found
        # 2. Check no existing report from this user -> 400 if already reported
        # 3. Create ReviewReport row
        # 4. Increment review.report_count
        # 5. Notify admin/staff via activity feed

    async def get_book_reviews(self, book_uuid: str, sort: str, pagination) -> BookReviewsResponse:
        # Load reviews where is_active=True for book
        # Include replies (one level deep, active only)
        # Include rating summary (average, breakdown)
        # Sort: latest=created_at desc, highest/lowest rating, most_replies

    async def remove_review(self, review_id: str, admin: User) -> None:
        # 1. Soft delete Review + all its replies
        # 2. Delete Rating (remove from average)
        # 3. Recompute book average
        # 4. Close any open reports against this review
        # 5. audit_action("REVIEW_REMOVED")

    async def dismiss_report(self, review_id: str, note: str, admin: User) -> None:
        # Set ReviewReport.status=DISMISSED
        # audit_action("REPORT_DISMISSED")
```

---

## `app/services/download_service.py`

```python
class DownloadService:
    def __init__(self, db: AsyncSession, storage: BaseStorageProvider, redis: Redis): ...

    async def generate_download_url(self, book_uuid: str, version_uuid: str | None, user: User) -> DownloadResponse:
        # 1. Load Book + version (current if version_uuid=None) -> 404 if not found
        # 2. Check book.is_active and version.status=APPROVED -> 404
        # 3. Check Redis concurrent lock: download:active:{user_id}:{book_id} -> 429 if exists
        # 4. Check Redis daily limit: download:daily:{user_id}:{book_id}:{date} -> 429 if >= MAX_DOWNLOADS_PER_DAY
        # 5. Check Redis monthly limit -> 429 if >= MAX_DOWNLOADS_PER_MONTH
        # 6. Check 80% daily threshold -> trigger warning notification if hit
        # 7. Check 80% monthly threshold -> trigger warning notification if hit
        # 8. Generate pre-signed S3 URL: storage.generate_presigned_url(path, expires=600)
        # 9. Set concurrent lock: Redis SET download:active:{user_id}:{book_id} 1 EX 600
        # 10. Increment daily + monthly Redis counters
        # 11. Create DownloadLog row
        # 12. Increment book.total_downloads and version.total_downloads
        # 13. Return DownloadResponse with URL, limits remaining

    async def get_my_history(self, user: User, pagination) -> PaginatedResponse:
        # Load DownloadLogs where user_id=user.id and is_deleted=False
        # Include book details; for archived books include archive_notice
        # Paginate and return

    async def soft_delete_history(self, book_uuid: str, user: User) -> None:
        # Find DownloadLog for user+book -> 404 if not found
        # Set is_deleted=True, deleted_at=now()
        # Note: record kept for archived book logic
```

---

## `app/services/notification_service.py`

```python
class NotificationService:
    def __init__(self, db: AsyncSession): ...

    async def create_or_group_notification(
        self, user_id: int, notification_type: str,
        group_key: str, title: str, data: dict
    ) -> None:
        # 1. Find existing UNREAD notification with same group_key for user
        # 2. If found: increment group_count, update message, set is_grouped=True, updated_at=now()
        # 3. If not found: create new Notification row
        #    Set expires_at = now() + 7 days

    async def get_my_notifications(self, user: User, filters, pagination) -> NotificationListResponse:
        # Load notifications for user ordered by created_at desc
        # Filter by is_read if provided
        # Count unread total
        # Return list + unread count

    async def mark_read(self, notification_id: str, user: User) -> None:
        # Load notification -> 404 if not found or wrong user
        # Set is_read=True, read_at=now()
        # Reset grouping: group_count=1, is_grouped=False
        # (new events after this point start a fresh group)

    async def mark_all_read(self, user: User) -> dict:
        # Bulk update all unread notifications for user
        # Reset grouping on all
        # Return count of marked

    async def delete_notification(self, notification_id: str, user: User) -> None:
        # Hard delete (notification is disposable)
        # 404 if not found or wrong user

    async def update_preferences(self, user: User, payload: NotificationPreferencesRequest) -> None:
        # Update profile.reply_notifications field on ReaderProfile or PublisherProfile

    async def cleanup_expired(self) -> int:
        # Called by Celery Beat daily
        # Delete all Notification rows where expires_at < now()
        # Return count deleted
```

---

## `app/services/admin_service.py`

```python
class AdminService:
    def __init__(self, db: AsyncSession): ...

    async def get_dashboard(self) -> DashboardResponse:
        # Run parallel queries:
        # - COUNT users by role
        # - COUNT approved books
        # - SUM download_logs
        # - COUNT new registrations today
        # - COUNT pending KYC, book approvals, tags, reported reviews
        # - Latest 5 books submitted
        # - Latest 5 publishers registered
        # - Latest 5 reported reviews
        # Return DashboardResponse

    async def get_audit_log(self, filters, pagination) -> PaginatedResponse:
        # Query AuditLog with optional filters: action, performed_by_id, date range
        # admin|superadmin only (checked in router)
        # Order by performed_at desc

    async def get_activity_feed(self, user: User, filters, pagination) -> PaginatedResponse:
        # Load ActivityFeed entries, filter by category/is_read
        # All staff/admin see the same feed
        # Order by created_at desc

    async def mark_activity_read(self, activity_id: str, user: User) -> None:
        # Set is_read=True, read_at=now()

    async def mark_all_activity_read(self, user: User) -> None:
        # Bulk update unread ActivityFeed entries
```

---

## `app/services/analytics_service.py`

```python
class AnalyticsService:
    def __init__(self, db: AsyncSession): ...

    async def get_publisher_analytics(self, user: User) -> dict:
        # Load all books for publisher
        # Aggregate DownloadLog by book_id
        # Compute totals: all_time, this_month, this_week, today
        # Find most_downloaded_book
        # Return summary + per-book breakdown

    async def get_book_analytics(self, book_uuid: str, period: str, from_date: str, to_date: str, user: User) -> BookDownloadAnalytics:
        # Verify access: publisher owns book OR admin
        # Query DownloadLog grouped by date for this book_uuid + version
        # Group by day|week|month based on period
        # Return chart_data points

    async def get_platform_analytics(self, admin: User) -> dict:
        # Platform-wide aggregation of DownloadLog
        # Total downloads, unique downloaders per month
        # Top 10 books by downloads
        # Top 10 publishers by downloads
        # Monthly chart data (last 12 months)

    async def get_user_download_analytics(self, user_id: str, admin: User) -> dict:
        # Load DownloadLog for specific user
        # Return history with book details and stats
```

---

## `app/services/publisher_service.py`

```python
class PublisherService:
    def __init__(self, db: AsyncSession): ...

    async def get_public_profile(self, publisher_uuid: str) -> PublisherProfileDetail:
        # Load PublisherProfile where uuid=publisher_uuid and is_active=True and is_verified=True
        # -> 404 if not found
        # Count total approved books
        # Return PublisherProfileDetail (social links, bio, logo, verification badge)

    async def get_public_books(self, publisher_uuid: str, pagination) -> PaginatedResponse:
        # Load approved BookVersions for publisher, paginated
        # Return BookListItem list
```
