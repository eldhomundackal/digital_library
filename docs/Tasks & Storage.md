# Tasks & Storage

Celery tasks, storage providers and number generator.

---

## `app/tasks/email_tasks.py`

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_otp_email(self, email: str, otp: str, otp_type: str) -> None:
    """
    Sends OTP code to user email.
    otp_type: "email_verify" | "password_reset"
    Subject line differs per type.
    Retries up to 3 times on SMTP failure.
    """
    # Build subject: "Verify your email" or "Reset your password"
    # Build body: plain text + HTML with OTP prominently displayed
    # Send via aiosmtplib using SMTP settings from config
    # On failure: self.retry(exc=exc)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id: int) -> None:
    """
    Sent after email verification.
    Reader: welcome + browse books CTA
    Publisher: welcome + KYC next steps instructions
    """
    # Load user from DB
    # Render appropriate template based on user.role
    # Send email

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_kyc_status_email(self, publisher_id: int, status: str, reason: str | None = None) -> None:
    """
    status: "submitted" | "approved" | "rejected" | "resubmission_requested"
    Sends decision email to publisher with clear next steps.
    Includes rejection reason and which documents were flagged.
    """

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_book_status_email(self, book_id: int, status: str, reason: str | None = None) -> None:
    """
    status: "approved" | "rejected"
    Includes rejection reason and link to edit book.
    """

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_staff_welcome_email(self, email: str, temp_password: str) -> None:
    """
    Sent when admin creates a new staff account.
    Includes temp password and must-change-password instruction.
    """

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_download_warning_email(self, user_id: int, book_id: int, warning_type: str) -> None:
    """
    warning_type: "daily_80_percent" | "monthly_80_percent"
    Informs reader of remaining downloads for the day/month.
    """
```

---

## `app/tasks/notification_tasks.py`

```python
@celery_app.task
def create_in_app_notification(
    user_id: int,
    notification_type: str,
    group_key: str,
    title: str,
    message: str,
    data: dict
) -> None:
    """
    Creates or groups an in-app notification.
    Calls NotificationService.create_or_group_notification() inside a sync DB session.
    """
    # Open sync DB session (Celery runs sync)
    # Call notification logic
    # Commit and close

@celery_app.task
def create_notifications_for_role(
    role: str,
    notification_type: str,
    title: str,
    message: str,
    data: dict
) -> None:
    """
    Bulk notification for all users of a given role.
    Used for: notifying all staff/admin of new KYC application, new book submission.
    Queries all active users with role=role, fires create_in_app_notification per user.
    """

@celery_app.task
def cleanup_expired_notifications() -> dict:
    """
    Scheduled daily by Celery Beat at midnight.
    Deletes all Notification rows where expires_at < now().
    Returns {deleted_count: N}.
    """
```

---

## `app/storage/base.py`

```python
class BaseStorageProvider(ABC):

    @abstractmethod
    async def upload(self, file: UploadFile, path: str) -> str:
        """Upload file to storage. Returns the URL or path stored in DB."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete file from storage. Silently ignores missing files."""

    @abstractmethod
    async def generate_presigned_url(self, path: str, expires_seconds: int) -> str:
        """Generate a time-limited download URL for a private file."""

    @abstractmethod
    async def get_public_url(self, path: str) -> str:
        """Return permanent public URL for a public file (thumbnails, avatars)."""
```

---

## `app/storage/s3.py` — S3StorageProvider

```python
class S3StorageProvider(BaseStorageProvider):
    def __init__(self):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket = settings.S3_BUCKET_NAME

    async def upload(self, file: UploadFile, path: str) -> str:
        # Run boto3 upload in thread pool (boto3 is sync)
        # await asyncio.get_event_loop().run_in_executor(None, self._upload_sync, file, path)
        # Returns: f"https://{bucket}.s3.{region}.amazonaws.com/{path}"

    async def delete(self, path: str) -> None:
        # Extract key from URL or use path directly
        # Run delete_object in thread pool

    async def generate_presigned_url(self, path: str, expires_seconds: int) -> str:
        # generate_presigned_url("get_object", {Bucket, Key, Expires})
        # Run in thread pool
        # Return presigned URL string

    async def get_public_url(self, path: str) -> str:
        # Return direct S3 URL (bucket must allow public read for thumbnails/avatars)
        return f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{path}"
```

---

## `app/storage/local.py` — LocalStorageProvider (dev only)

```python
class LocalStorageProvider(BaseStorageProvider):
    """
    Stores files on local disk under /tmp/digital-library/
    Serves files via a static files mount in main.py.
    Only use in development — never in production.
    """
    BASE_PATH = Path("/tmp/digital-library")
    BASE_URL = "http://localhost:8000/static"

    async def upload(self, file: UploadFile, path: str) -> str:
        # Create directory if not exists
        # Write file bytes to BASE_PATH / path
        # Return f"{BASE_URL}/{path}"

    async def delete(self, path: str) -> None:
        # Unlink file at BASE_PATH / path; ignore FileNotFoundError

    async def generate_presigned_url(self, path: str, expires_seconds: int) -> str:
        # Return static URL (no expiry in local dev)
        return f"{self.BASE_URL}/{path}"

    async def get_public_url(self, path: str) -> str:
        return f"{self.BASE_URL}/{path}"
```

---

## `app/storage/factory.py`

```python
def get_storage_provider() -> BaseStorageProvider:
    match settings.STORAGE_PROVIDER:
        case "s3":    return S3StorageProvider()
        case "local": return LocalStorageProvider()
        case _:       raise ValueError(f"Unknown storage provider: {settings.STORAGE_PROVIDER}")
```

---

## `app/storage/validators.py`

```python
MAX_SIZES_BYTES = {
    "book_pdf":  settings.MAX_BOOK_PDF_SIZE_MB * 1024 * 1024,
    "thumbnail": settings.MAX_THUMBNAIL_SIZE_MB * 1024 * 1024,
    "kyc_doc":   settings.MAX_KYC_DOCUMENT_SIZE_MB * 1024 * 1024,
    "avatar":    settings.MAX_THUMBNAIL_SIZE_MB * 1024 * 1024,
}

ALLOWED_MIME_TYPES = {
    "book_pdf":  {"application/pdf"},
    "thumbnail": {"image/jpeg", "image/png", "image/webp"},
    "kyc_doc":   {"application/pdf"},
    "avatar":    {"image/jpeg", "image/png", "image/webp"},
}

def validate_file(file: UploadFile, file_type: str) -> None:
    """
    Raises HTTPException 400 on:
    - Wrong MIME type
    - File size exceeding limit
    Note: FastAPI UploadFile.size may be None for chunked uploads;
    fall back to reading content length header.
    """
    if file.content_type not in ALLOWED_MIME_TYPES[file_type]:
        raise HTTPException(400, detail={"file": [f"Only {ALLOWED_MIME_TYPES[file_type]} accepted"]})
    size = file.size or int(request.headers.get("content-length", 0))
    if size > MAX_SIZES_BYTES[file_type]:
        mb_limit = MAX_SIZES_BYTES[file_type] // (1024 * 1024)
        raise HTTPException(400, detail={"file": [f"File must not exceed {mb_limit}MB"]})
```
