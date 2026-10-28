# Digital Library — Backend Project Plan

Oct 24, 2026 · @Eldho

This plan covers the full FastAPI backend for the Digital Library platform — architecture, folder structure, module breakdown, and execution roadmap.

## Project Overview

A digital library platform where readers browse and download free books, publishers submit titles for approval, and admins manage the full content lifecycle. Phase 1 covers books only; monetisation and advanced roles follow in later phases.

| Dimension | Decision |
| --- | --- |
| Primary entities | Readers, Publishers, Staff, Admin, Superadmin |
| Content type | Books (PDF + thumbnail) |
| Access model | Browse free; login to download or review |
| Publisher onboarding | KYC approval (Gov ID, Publishing Licence, Business Reg) |
| Book approval | Every version goes through staff/admin review |
| Auth strategy | Local (JWT) + IDP-agnostic OIDC/OAuth2 abstraction |
| Backend | Python 3.12 · FastAPI · PostgreSQL · SQLAlchemy · Alembic |
| Background jobs | Celery + Redis |
| File storage | AWS S3 (or Cloudflare R2) — pre-signed URLs |
| Search | PostgreSQL full-text search (GIN index) |
| Notifications | In-app (DB) + email (Celery async); 7-day retention |
| API total | 118 endpoints across 8 modules |

## Architecture

&#91;embedded content: six-layer backend architecture\]

Clients talk to Nginx, which proxies to FastAPI. The application layer holds routers, middleware, dependency injection and Pydantic schemas. Services encapsulate all business logic and call into the data layer (PostgreSQL + Redis) or external services (S3, Celery, SMTP). The IDP abstraction sits below everything — swap the provider via env vars with zero code change.

## Project Folder Structure

Every concern lives in its own layer; nothing bleeds across. Copy this layout exactly when scaffolding the project.

```
digital-library-api/
|
|-- app/                          # Application root
|   |
|   |-- api/                      # All HTTP layer code
|   |   |-- v1/                   # Versioned routers
|   |   |   |-- __init__.py
|   |   |   |-- auth.py           # POST /auth/*
|   |   |   |-- users.py          # GET/PATCH /users/me
|   |   |   |-- publishers.py     # GET /publishers/{id}
|   |   |   |-- kyc.py            # KYC submission endpoints
|   |   |   |-- books.py          # Public book endpoints
|   |   |   |-- publisher_books.py# Publisher book management
|   |   |   |-- authors.py        # Author endpoints
|   |   |   |-- categories.py     # Category listing
|   |   |   |-- tags.py           # Tag listing
|   |   |   |-- reviews.py        # Ratings and reviews
|   |   |   |-- downloads.py      # Download + history
|   |   |   |-- notifications.py  # User notifications
|   |   |   |-- utils.py          # Countries, cities, languages
|   |   |   |-- admin/            # All /admin/* endpoints
|   |   |       |-- __init__.py
|   |   |       |-- users.py      # Admin user management
|   |   |       |-- kyc.py        # Admin KYC management
|   |   |       |-- books.py      # Admin book approval
|   |   |       |-- reviews.py    # Review moderation
|   |   |       |-- tags.py       # Tag approval
|   |   |       |-- authors.py    # Author management
|   |   |       |-- categories.py # Category management
|   |   |       |-- utils.py      # Admin country/city/lang
|   |   |       |-- analytics.py  # Download analytics
|   |   |       |-- dashboard.py  # Admin dashboard
|   |   |       |-- audit.py      # Audit log
|   |   |       |-- activity.py   # Activity feed
|   |   |       |-- notifications.py # Admin notifications
|   |   |-- __init__.py
|   |   |-- router.py             # Master router, mounts v1
|   |
|   |-- auth/                     # Auth provider abstraction
|   |   |-- __init__.py
|   |   |-- base.py               # BaseAuthProvider (ABC)
|   |   |-- local.py              # LocalAuthProvider
|   |   |-- oidc.py               # OIDCAuthProvider
|   |   |-- oauth2.py             # OAuth2AuthProvider
|   |   |-- factory.py            # get_auth_provider() factory
|   |   |-- jwt.py                # JWT create/decode helpers
|   |   |-- otp.py                # OTP generate/verify (Redis)
|   |   |-- password.py           # Hash/verify passwords
|   |
|   |-- core/                     # App-wide config and startup
|   |   |-- __init__.py
|   |   |-- config.py             # Settings (pydantic-settings)
|   |   |-- security.py           # Permission guards, RBAC
|   |   |-- dependencies.py       # get_current_user, get_db etc.
|   |   |-- middleware.py         # Audit, logging, error handlers
|   |   |-- exceptions.py         # Custom HTTP exceptions
|   |   |-- constants.py          # Enums, string constants
|   |
|   |-- db/                       # Database layer
|   |   |-- __init__.py
|   |   |-- session.py            # Async engine, SessionLocal
|   |   |-- base.py               # Base declarative model
|   |   |-- models/               # SQLAlchemy ORM models
|   |   |   |-- __init__.py       # Exports all models
|   |   |   |-- user.py           # User, ReaderProfile, StaffProfile
|   |   |   |-- publisher.py      # PublisherProfile, StaffPermission
|   |   |   |-- kyc.py            # KYCApplication, KYCDocument, KYCActionLog
|   |   |   |-- book.py           # Book, BookVersion, BookVersionActionLog
|   |   |   |-- author.py         # Author
|   |   |   |-- category.py       # Category
|   |   |   |-- tag.py            # Tag
|   |   |   |-- review.py         # Rating, Review, ReviewReply, ReviewReport
|   |   |   |-- download.py       # DownloadLog
|   |   |   |-- notification.py   # Notification
|   |   |   |-- audit.py          # AuditLog, ActivityFeed
|   |   |   |-- utils.py          # Country, City, Language
|   |   |-- migrations/           # Alembic migrations
|   |       |-- env.py
|   |       |-- versions/         # Auto-generated migration files
|   |
|   |-- schemas/                  # Pydantic request/response models
|   |   |-- __init__.py
|   |   |-- auth.py               # RegisterSchema, LoginSchema, TokenSchema
|   |   |-- user.py               # UserSchema, ReaderProfileSchema
|   |   |-- publisher.py          # PublisherProfileSchema
|   |   |-- kyc.py                # KYCSchema, KYCDocumentSchema
|   |   |-- book.py               # BookSchema, BookVersionSchema
|   |   |-- author.py             # AuthorSchema
|   |   |-- review.py             # ReviewSchema, RatingSchema
|   |   |-- download.py           # DownloadSchema
|   |   |-- notification.py       # NotificationSchema
|   |   |-- admin.py              # DashboardSchema, AuditLogSchema
|   |   |-- utils.py              # CountrySchema, CitySchema
|   |   |-- common.py             # PaginatedResponse, ErrorResponse
|   |
|   |-- services/                 # Business logic layer
|   |   |-- __init__.py
|   |   |-- auth_service.py       # Registration, login, OTP flows
|   |   |-- user_service.py       # Profile CRUD, avatar upload
|   |   |-- publisher_service.py  # Publisher profile, public page
|   |   |-- kyc_service.py        # KYC submission, approval workflow
|   |   |-- book_service.py       # Book CRUD, versioning, search
|   |   |-- author_service.py     # Author CRUD, merge
|   |   |-- review_service.py     # Ratings, reviews, replies, reports
|   |   |-- download_service.py   # Download URL, limits, logging
|   |   |-- notification_service.py # Create, group, deliver notifications
|   |   |-- admin_service.py      # Dashboard, audit, activity feed
|   |   |-- analytics_service.py  # Download analytics per book/publisher
|   |
|   |-- tasks/                    # Celery async tasks
|   |   |-- __init__.py
|   |   |-- celery_app.py         # Celery app instance + Beat schedule
|   |   |-- email_tasks.py        # send_otp, send_approval_email etc.
|   |   |-- notification_tasks.py # create_notification, cleanup_expired
|   |   |-- storage_tasks.py      # File processing (if needed)
|   |
|   |-- storage/                  # File storage abstraction
|   |   |-- __init__.py
|   |   |-- base.py               # BaseStorageProvider (ABC)
|   |   |-- s3.py                 # S3StorageProvider
|   |   |-- local.py              # LocalStorageProvider (dev only)
|   |   |-- factory.py            # get_storage_provider() factory
|   |   |-- validators.py         # File type, size validators
|   |
|   |-- utils/                    # Shared utilities
|   |   |-- __init__.py
|   |   |-- number_generator.py   # USR-000001, BK-000001 etc.
|   |   |-- slug.py               # Slug generation for tags/categories
|   |   |-- pagination.py         # Pagination helpers
|   |   |-- audit.py              # audit_action() helper
|   |   |-- cache.py              # Redis cache helpers
|   |
|   |-- __init__.py
|   |-- main.py                   # FastAPI app factory, lifespan
|
|-- scripts/                      # One-time and operational scripts
|   |-- seed_superadmin.py        # Create first superadmin
|   |-- seed_countries.py         # Load countries-states-cities dataset
|   |-- seed_languages.py         # Load predefined languages
|   |-- sync_redis_counters.py    # Sync number counters on startup
|
|-- tests/                        # Test suite
|   |-- conftest.py               # Fixtures: test DB, test client, auth tokens
|   |-- unit/
|   |   |-- test_auth_service.py
|   |   |-- test_book_service.py
|   |   |-- test_kyc_service.py
|   |   |-- test_review_service.py
|   |   |-- test_download_service.py
|   |   |-- test_number_generator.py
|   |-- integration/
|       |-- test_auth_api.py
|       |-- test_books_api.py
|       |-- test_kyc_api.py
|       |-- test_reviews_api.py
|       |-- test_downloads_api.py
|       |-- test_admin_api.py
|
|-- alembic.ini                   # Alembic config
|-- pyproject.toml                # Dependencies (uv or poetry)
|-- .env.example                  # All env vars documented
|-- .env                          # Local secrets (git-ignored)
|-- Dockerfile                    # Production image
|-- docker-compose.yml            # Local dev: api + postgres + redis + celery
|-- docker-compose.test.yml       # Test environment
|-- Makefile                      # Shortcuts: make dev, make test, make migrate
|-- README.md
```

## Database Layer

28 tables across 8 groups. All use integer primary keys internally; UUIDs are exposed in the API. Every table carries `created_at` and `updated_at`; soft-deletes use `is_active` + `deleted_at`.

| Group | Tables | Notes |
| --- | --- | --- |
| Core users | `users`, `reader_profiles`, `reader_preferred_categories`, `reader_preferred_tags`, `publisher_profiles`, `staff_profiles`, `staff_permissions` | One profile row per user; permissions as rows not a bitmask |
| Utils | `countries`, `cities`, `languages` | Seeded from open dataset; `is_seeded` flag protects manual entries on re-seed |
| KYC | `kyc_applications`, `kyc_documents`, `kyc_action_logs` | Document-level status; action log is immutable |
| Books | `books`, `book_versions`, `book_authors`, `book_tags`, `book_version_action_logs` | `books` is the master record; all content lives in `book_versions` |
| Classification | `categories`, `tags`, `authors` | Tags have `PENDING/APPROVED/REJECTED` lifecycle |
| Reviews | `ratings`, `reviews`, `review_replies`, `review_reports` | Separate `ratings` table for silent ratings; one review per user per book |
| Downloads | `download_logs` | Immutable log; `is_deleted` soft-hides from reader history |
| Admin | `notifications`, `audit_logs`, `activity_feed` | Notifications expire after 7 days via Celery Beat cleanup |

### Key design decisions

- **Full-text search** — GIN index on `book_versions.search_vector` (weighted: title A, authors B, description C, tags+ISBN D). Trigger auto-updates vector on insert/update and when authors or tags change.
- **Book versioning** — `books.current_version_id` points to the live version. Old versions remain accessible. Downloads tracked per version via `book_version_id` in `download_logs`.
- **Cascading soft-deletes** — handled in application code (not DB triggers) so audit logs, notifications and Redis cache clears fire alongside the delete.
- **Number generation** — Redis atomic `INCR` counter per entity type (`USR-000001`, `BK-000001`). Counters synced from DB row count on startup.
- **Audit log** — immutable (`no updated_at`). Stores `ip_address` and `metadata JSONB` for full context.

### Alembic workflow

```bash
# Create a new migration
alembic revision --autogenerate -m "add publisher social links"

# Apply all pending migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

### Seed scripts (run once on first deploy)

```bash
python scripts/seed_superadmin.py
python scripts/seed_countries.py
python scripts/seed_languages.py
python scripts/sync_redis_counters.py
```

## API Modules

118 endpoints across 8 modules, all under `/api/v1`. Each module maps to one or more router files and one service file.

| Module | Router file(s) | Service file | Endpoints | Auth required |
| --- | --- | --- | --- | --- |
| 1. Auth | `auth.py` | `auth_service.py` | 12 | Partial |
| 2. Users & Profiles | `users.py`, `publishers.py` | `user_service.py`, `publisher_service.py` | 15 | Partial |
| 3. Publisher KYC | `kyc.py`, `admin/kyc.py` | `kyc_service.py` | 12 | Publisher + Staff/Admin |
| 4. Books | `books.py`, `publisher_books.py`, `authors.py`, `categories.py`, `tags.py`, `admin/books.py` | `book_service.py`, `author_service.py` | 31 | Partial |
| 5. Ratings & Reviews | `reviews.py`, `admin/reviews.py` | `review_service.py` | 15 | Partial |
| 6. Downloads | `downloads.py`, `admin/analytics.py` | `download_service.py`, `analytics_service.py` | 8 | Reader + Admin |
| 7. Notifications | `notifications.py`, `admin/notifications.py` | `notification_service.py` | 8 | All logged-in |
| 8. Admin & Staff | `admin/dashboard.py`, `admin/audit.py`, `admin/activity.py`, `admin/users.py`, `admin/utils.py` | `admin_service.py` | 17 | Staff/Admin only |

### Endpoint counts by access level

| Access level | Count |
| --- | --- |
| Public (no auth) | 14 |
| Any logged-in user | 22 |
| Reader only | 6 |
| Publisher only | 18 |
| Staff or Admin | 41 |
| Admin or Superadmin only | 10 |
| Superadmin only | 7 |

### Router registration in `main.py`

```python
from app.api.router import api_router

app = FastAPI(title="Digital Library API", version="1.0.0")
app.include_router(api_router, prefix="/api/v1")
```

### `app/api/router.py` (master router)

```python
from fastapi import APIRouter
from app.api.v1 import (
    auth, users, publishers, kyc,
    books, publisher_books, authors,
    categories, tags, reviews,
    downloads, notifications, utils
)
from app.api.v1.admin import (
    users as admin_users, kyc as admin_kyc,
    books as admin_books, reviews as admin_reviews,
    tags as admin_tags, authors as admin_authors,
    categories as admin_categories, utils as admin_utils,
    analytics, dashboard, audit, activity,
    notifications as admin_notifications
)

api_router = APIRouter()

# Public + user routes
api_router.include_router(auth.router,           prefix="/auth",          tags=["Auth"])
api_router.include_router(users.router,          prefix="/users",         tags=["Users"])
api_router.include_router(publishers.router,     prefix="/publishers",    tags=["Publishers"])
api_router.include_router(kyc.router,            prefix="/kyc",           tags=["KYC"])
api_router.include_router(books.router,          prefix="/books",         tags=["Books"])
api_router.include_router(publisher_books.router,prefix="/publisher",     tags=["Publisher Books"])
api_router.include_router(authors.router,        prefix="/authors",       tags=["Authors"])
api_router.include_router(categories.router,     prefix="/categories",    tags=["Categories"])
api_router.include_router(tags.router,           prefix="/tags",          tags=["Tags"])
api_router.include_router(reviews.router,        prefix="/reviews",       tags=["Reviews"])
api_router.include_router(downloads.router,      prefix="/downloads",     tags=["Downloads"])
api_router.include_router(notifications.router,  prefix="/users",         tags=["Notifications"])
api_router.include_router(utils.router,          prefix="/utils",         tags=["Utils"])

# Admin routes
api_router.include_router(admin_users.router,    prefix="/admin/users",   tags=["Admin - Users"])
api_router.include_router(admin_kyc.router,      prefix="/admin/kyc",     tags=["Admin - KYC"])
api_router.include_router(admin_books.router,    prefix="/admin/books",   tags=["Admin - Books"])
api_router.include_router(admin_reviews.router,  prefix="/admin/reviews", tags=["Admin - Reviews"])
api_router.include_router(admin_tags.router,     prefix="/admin/tags",    tags=["Admin - Tags"])
api_router.include_router(admin_categories.router,prefix="/admin/categories",tags=["Admin - Categories"])
api_router.include_router(admin_authors.router,  prefix="/admin/authors", tags=["Admin - Authors"])
api_router.include_router(admin_utils.router,    prefix="/admin/utils",   tags=["Admin - Utils"])
api_router.include_router(analytics.router,      prefix="/admin/analytics",tags=["Admin - Analytics"])
api_router.include_router(dashboard.router,      prefix="/admin",         tags=["Admin - Dashboard"])
api_router.include_router(audit.router,          prefix="/admin",         tags=["Admin - Audit"])
api_router.include_router(activity.router,       prefix="/admin",         tags=["Admin - Activity"])
api_router.include_router(admin_notifications.router,prefix="/admin",     tags=["Admin - Notifications"])
```

## Auth & Security Layer

The auth system is provider-agnostic from day one. Swap from local JWT to Keycloak, Okta, Cognito or any OAuth 2.0 / OIDC provider by changing four environment variables.

### Provider abstraction (`app/auth/base.py`)

```python
from abc import ABC, abstractmethod

class BaseAuthProvider(ABC):

    @abstractmethod
    async def get_authorization_url(self) -> str: ...

    @abstractmethod
    async def handle_callback(self, code: str, state: str) -> TokenSchema: ...

    @abstractmethod
    async def validate_token(self, token: str) -> TokenPayloadSchema: ...

    @abstractmethod
    async def refresh_token(self, token: str) -> TokenSchema: ...

    @abstractmethod
    async def logout(self, token: str) -> None: ...

    @abstractmethod
    async def get_user_info(self, token: str) -> UserInfoSchema: ...

    # Local provider only
    async def register(self, payload): raise NotImplementedError
    async def send_otp(self, email, otp_type): raise NotImplementedError
    async def reset_password(self, token, password): raise NotImplementedError
```

### Factory (`app/auth/factory.py`)

```python
def get_auth_provider() -> BaseAuthProvider:
    match settings.AUTH_PROVIDER:
        case "oidc":   return OIDCAuthProvider()
        case "oauth2": return OAuth2AuthProvider()
        case _:        return LocalAuthProvider()
```

### JWT tokens (`app/auth/jwt.py`)

| Token | Storage | Expiry | Purpose |
| --- | --- | --- | --- |
| Access token | Memory / Authorization header | 15 min | API auth on every request |
| Refresh token | HttpOnly cookie (`Path=/api/v1/auth/refresh`) | 7 days | Obtain new access token |
| Reset session token | Response body (short-lived) | 10 min | Password reset step 2 |

### OTP (`app/auth/otp.py`)

OTPs stored in Redis with auto-expiry. Max 5 wrong attempts then locked.

```
Redis keys:
  otp:email_verify:{email}    TTL 10 min
  otp:password_reset:{email}  TTL 10 min
```

### RBAC guards (`app/core/security.py`)

```python
from fastapi import Depends, HTTPException
from app.core.dependencies import get_current_user

def require_roles(*roles: str):
    def guard(user = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return guard

# Usage in a router
@router.post("/{id}/approve")
async def approve_book(
    id: str,
    current_user = Depends(require_roles("staff", "admin", "superadmin"))
):
    ...
```

### Staff permission check

```python
def require_permission(permission: str):
    def guard(user = Depends(get_current_user)):
        if user.role in ("admin", "superadmin"):
            return user  # full access
        perms = [p.permission for p in user.staff_profile.permissions]
        if permission not in perms:
            raise HTTPException(403, f"Missing permission: {permission}")
        return user
    return guard
```

### Middleware (`app/core/middleware.py`)

| Middleware | Purpose |
| --- | --- |
| `AuditMiddleware` | Captures admin actions, writes to `audit_logs` |
| `RequestLoggingMiddleware` | Logs method, path, status, duration |
| `ErrorHandlerMiddleware` | Formats all unhandled exceptions into standard error shape |
| `CORSMiddleware` | FastAPI built-in, configured from `settings.ALLOWED_ORIGINS` |

## Background Tasks

Celery handles all async work: email delivery, notification creation, scheduled cleanup. Redis is the broker and result backend.

### Celery app (`app/tasks/celery_app.py`)

```python
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "digital_library",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.storage_tasks",
    ]
)

celery_app.conf.beat_schedule = {
    "cleanup-expired-notifications": {
        "task": "app.tasks.notification_tasks.cleanup_expired_notifications",
        "schedule": crontab(hour=0, minute=0),  # daily midnight
    },
}
```

### Task inventory

| Task | File | Trigger | Description |
| --- | --- | --- | --- |
| `send_otp_email` | `email_tasks.py` | Auth register / forgot-password | Sends OTP code to user email |
| `send_welcome_email` | `email_tasks.py` | Email verified | Welcome email with next steps |
| `send_kyc_status_email` | `email_tasks.py` | KYC approved / rejected | Notifies publisher of decision |
| `send_book_status_email` | `email_tasks.py` | Book approved / rejected | Notifies publisher of decision |
| `send_download_warning_email` | `email_tasks.py` | 80% download limit hit | Warns reader of remaining downloads |
| `create_in_app_notification` | `notification_tasks.py` | Any notifiable event | Creates or groups notification in DB |
| `cleanup_expired_notifications` | `notification_tasks.py` | Daily midnight (Beat) | Deletes notifications older than 7 days |

### Redis usage summary

| Key pattern | TTL | Purpose |
| --- | --- | --- |
| `otp:email_verify:{email}` | 10 min | Email verification OTP + attempt count |
| `otp:password_reset:{email}` | 10 min | Password reset OTP + attempt count |
| `download:active:{user_id}:{book_id}` | 10 min | Concurrent download lock |
| `download:daily:{user_id}:{book_id}:{date}` | 24 hr | Daily download count |
| `download:monthly:{user_id}:{book_id}:{year}:{month}` | 31 days | Monthly download count |
| `counter:{entity_type}` | Permanent | Number generator counters |
| `cache:books:list:{params_hash}` | 5 min | Book listing cache |
| `cache:book:{uuid}` | 5 min | Single book detail cache |

### Running locally

```bash
# Worker
celery -A app.tasks.celery_app worker --loglevel=info

# Beat scheduler
celery -A app.tasks.celery_app beat --loglevel=info

# Both via docker-compose
docker compose up celery_worker celery_beat
```

## File Storage

All files live in S3 (or Cloudflare R2 — same API). Never stored in the DB; only the S3 key/URL is persisted. A `LocalStorageProvider` handles development without cloud credentials.

### Storage abstraction (`app/storage/base.py`)

```python
class BaseStorageProvider(ABC):

    @abstractmethod
    async def upload(self, file: UploadFile, path: str) -> str:
        """Upload file, return public or private URL"""

    @abstractmethod
    async def delete(self, path: str) -> None: ...

    @abstractmethod
    async def generate_presigned_url(self, path: str, expires: int) -> str:
        """Generate a time-limited download URL"""
```

### S3 bucket layout

```
bucket/
|-- books/
|   |-- {book_uuid}/
|       |-- v{version}/
|           |-- thumbnail.{ext}     # Cover image
|           |-- book.pdf            # Full PDF
|
|-- kyc/
|   |-- {publisher_uuid}/
|       |-- government_id.pdf
|       |-- publishing_license.pdf
|       |-- business_registration.pdf
|
|-- avatars/
    |-- {user_uuid}.{ext}
```

### File rules per type

| File type | Accepted formats | Max size | Bucket visibility | Download method |
| --- | --- | --- | --- | --- |
| Book PDF | PDF | 50 MB | Private | Pre-signed URL (10 min) |
| Thumbnail | JPG, PNG, WEBP | 2 MB | Public | Direct URL |
| KYC document | PDF | 10 MB | Private | Pre-signed URL (admin only) |
| Avatar / Logo | JPG, PNG, WEBP | 2 MB | Public | Direct URL |

### File validator (`app/storage/validators.py`)

```python
MAX_SIZES = {
    "book_pdf":   settings.MAX_BOOK_PDF_SIZE_MB * 1024 * 1024,
    "thumbnail":  settings.MAX_THUMBNAIL_SIZE_MB * 1024 * 1024,
    "kyc_doc":    settings.MAX_KYC_DOCUMENT_SIZE_MB * 1024 * 1024,
    "avatar":     settings.MAX_THUMBNAIL_SIZE_MB * 1024 * 1024,
}

ALLOWED_TYPES = {
    "book_pdf":   {"application/pdf"},
    "thumbnail":  {"image/jpeg", "image/png", "image/webp"},
    "kyc_doc":    {"application/pdf"},
    "avatar":     {"image/jpeg", "image/png", "image/webp"},
}

def validate_file(file: UploadFile, file_type: str) -> None:
    if file.content_type not in ALLOWED_TYPES[file_type]:
        raise HTTPException(400, f"Invalid file type for {file_type}")
    if file.size > MAX_SIZES[file_type]:
        raise HTTPException(400, f"File exceeds size limit")
```

### Pre-signed URL flow (downloads)

```
1. Reader hits GET /api/v1/books/{id}/download
2. DownloadService checks Redis limits and concurrent lock
3. S3Provider.generate_presigned_url(path, expires=600)
4. Pre-signed URL returned to client (never stored)
5. Client downloads directly from S3 (no bandwidth through API server)
6. URL expires after 10 minutes
```

### Environment variables

```env
STORAGE_PROVIDER=s3               # s3 | local
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=digital-library

MAX_BOOK_PDF_SIZE_MB=50
MAX_THUMBNAIL_SIZE_MB=2
MAX_KYC_DOCUMENT_SIZE_MB=10
```

## Configuration & Environment

All config is read from environment variables via `pydantic-settings`. Never hardcode secrets or limits.

### `app/core/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # App
    APP_NAME: str = "Digital Library API"
    APP_ENV: str = "development"          # development | staging | production
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str                      # postgresql+asyncpg://...
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    AUTH_PROVIDER: str = "local"           # local | oidc | oauth2
    SECRET_KEY: str                        # used to sign JWTs (local only)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5

    # OIDC / OAuth2 (set when AUTH_PROVIDER != local)
    OIDC_ISSUER_URL: str = ""
    OIDC_CLIENT_ID: str = ""
    OIDC_CLIENT_SECRET: str = ""
    OIDC_SCOPES: str = "openid email profile"
    OAUTH2_AUTHORIZATION_URL: str = ""
    OAUTH2_TOKEN_URL: str = ""
    OAUTH2_USERINFO_URL: str = ""

    # Storage
    STORAGE_PROVIDER: str = "local"        # local | s3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "digital-library"

    # File limits (all in MB)
    MAX_BOOK_PDF_SIZE_MB: int = 50
    MAX_THUMBNAIL_SIZE_MB: int = 2
    MAX_KYC_DOCUMENT_SIZE_MB: int = 10

    # Download limits
    MAX_DOWNLOADS_PER_DAY: int = 5
    MAX_DOWNLOADS_PER_MONTH: int = 15
    DOWNLOAD_URL_EXPIRY_SECONDS: int = 600

    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@library.com"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Full `.env.example`

```env
# App
APP_NAME=Digital Library API
APP_ENV=development
DEBUG=true
ALLOWED_ORIGINS=["http://localhost:3000"]

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/digital_library
REDIS_URL=redis://localhost:6379/0

# Auth (local)
AUTH_PROVIDER=local
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Auth (OIDC - uncomment to switch)
# AUTH_PROVIDER=oidc
# OIDC_ISSUER_URL=https://keycloak.example.com/realms/library
# OIDC_CLIENT_ID=library-app
# OIDC_CLIENT_SECRET=secret

# Storage (local dev)
STORAGE_PROVIDER=local

# Storage (S3 - uncomment for staging/prod)
# STORAGE_PROVIDER=s3
# AWS_ACCESS_KEY_ID=AKIA...
# AWS_SECRET_ACCESS_KEY=...
# AWS_REGION=us-east-1
# S3_BUCKET_NAME=digital-library

# File limits
MAX_BOOK_PDF_SIZE_MB=50
MAX_THUMBNAIL_SIZE_MB=2
MAX_KYC_DOCUMENT_SIZE_MB=10

# Download limits
MAX_DOWNLOADS_PER_DAY=5
MAX_DOWNLOADS_PER_MONTH=15
DOWNLOAD_URL_EXPIRY_SECONDS=600

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@library.com
```

### `docker-compose.yml` (local dev)

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis]
    volumes: ["./app:/app/app"]   # hot reload
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: digital_library
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  celery_worker:
    build: .
    env_file: .env
    depends_on: [postgres, redis]
    command: celery -A app.tasks.celery_app worker --loglevel=info

  celery_beat:
    build: .
    env_file: .env
    depends_on: [redis]
    command: celery -A app.tasks.celery_app beat --loglevel=info

volumes:
  pgdata:
```

## Execution Plan

Build the backend in five phases. Each phase produces a working, testable slice before the next starts.

### Phase 1 — Foundation (Week 1–2)

Goal: project scaffolded, DB connected, superadmin can log in.

- [ ] Scaffold project from folder structure above
- [ ] Set up `pyproject.toml` with all dependencies
- [ ] Configure `docker-compose.yml` (API + PostgreSQL + Redis)
- [ ] Set up `pydantic-settings` config
- [ ] Create `db/session.py` async engine
- [ ] Write all 28 ORM models
- [ ] Write first Alembic migration (all tables)
- [ ] Run `seed_countries.py`, `seed_languages.py`
- [ ] Implement `LocalAuthProvider` (register, login, JWT, OTP)
- [ ] Implement `POST /auth/register`, `POST /auth/login`, verify-email, refresh, logout
- [ ] Implement `scripts/seed_superadmin.py`
- [ ] Write unit tests for `AuthService`

### Phase 2 — Users, KYC & Publisher onboarding (Week 3–4)

Goal: full publisher onboarding flow works end-to-end.

- [ ] `GET/PATCH /users/me` for all roles
- [ ] Avatar / logo upload (`PATCH /users/me/avatar`)
- [ ] `S3StorageProvider` + `LocalStorageProvider`
- [ ] File validators (type, size)
- [ ] Publisher public page (`GET /publishers/{id}`)
- [ ] Full KYC module (submit, document upload, resubmit)
- [ ] Admin KYC management (approve, reject, request resubmission)
- [ ] Staff account creation (`POST /admin/users/create-staff`)
- [ ] RBAC guards + staff permission checks
- [ ] Celery + Redis setup
- [ ] `send_kyc_status_email` task
- [ ] Write integration tests for KYC flow

### Phase 3 — Books (Week 5–6)

Goal: publishers can upload books, admin can approve, readers can browse.

- [ ] Categories CRUD (admin)
- [ ] Tags lifecycle (suggest, approve, reject)
- [ ] Authors CRUD + merge
- [ ] Full-text search GIN index + triggers
- [ ] Book CRUD (draft, submit, approve, reject, archive)
- [ ] Book versioning (version number + label, version history)
- [ ] `GET /books` with search + filters + pagination
- [ ] `GET /books/{id}` detail
- [ ] Publisher book dashboard (`GET /publisher/books`)
- [ ] Admin book approval endpoints
- [ ] `send_book_status_email` task
- [ ] Number generator (Redis atomic counter)
- [ ] Write integration tests for book flows

### Phase 4 — Reviews, Downloads & Notifications (Week 7–8)

Goal: readers can download and review; limits enforced; notifications flowing.

- [ ] Ratings + reviews (submit, edit, delete)
- [ ] Threaded replies (one level deep)
- [ ] Publisher response tagging
- [ ] Review reporting + admin moderation
- [ ] Download service (pre-signed URL, Redis limits, concurrent lock)
- [ ] Download history + soft-hide
- [ ] Download limit warning notification
- [ ] Full notification module (in-app + email, grouping, preferences)
- [ ] Notification cleanup Celery Beat job
- [ ] Publisher analytics (downloads per book, over time)
- [ ] Admin analytics (platform-wide)
- [ ] Write integration tests for downloads + reviews

### Phase 5 — Admin Panel & Hardening (Week 9–10)

Goal: admin panel complete; production-ready.

- [ ] Admin dashboard (platform stats, pending actions)
- [ ] Audit log (immutable, IP-tracked)
- [ ] Activity feed (actionable vs informational)
- [ ] `AuditMiddleware` wired to all admin actions
- [ ] `RequestLoggingMiddleware` + `ErrorHandlerMiddleware`
- [ ] OIDCAuthProvider + OAuth2AuthProvider (pluggable, tested with env vars)
- [ ] Rate limiting on auth endpoints
- [ ] Full `.env.example` documented
- [ ] `Makefile` shortcuts (`make dev`, `make test`, `make migrate`, `make seed`)
- [ ] End-to-end test run across all modules
- [ ] Dockerfile production image
- [ ] README with setup instructions

### Dependencies to install

```toml
[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.115"
uvicorn = {extras = ["standard"], version = "^0.32"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0"}
alembic = "^1.14"
asyncpg = "^0.30"           # async PostgreSQL driver
pydantic = {extras = ["email"], version = "^2.10"}
pydantic-settings = "^2.7"
python-jose = {extras = ["cryptography"], version = "^3.3"}
passlib = {extras = ["bcrypt"], version = "^1.7"}
python-multipart = "^0.0.20" # file uploads
boto3 = "^1.36"              # AWS S3
celery = {extras = ["redis"], version = "^5.4"}
redis = "^5.2"
httpx = "^0.28"              # async HTTP (OIDC flows)
aiosmtplib = "^3.0"          # async email
pillow = "^11.0"             # image validation

[tool.poetry.group.dev.dependencies]
pytest = "^8.3"
pytest-asyncio = "^0.24"
httpx = "^0.28"              # test client
factory-boy = "^3.3"         # test fixtures
faker = "^33.0"
ruff = "^0.9"                # linting
mypy = "^1.13"
```

### Makefile shortcuts

```makefile
dev:
	docker compose up --build

test:
	docker compose -f docker-compose.test.yml run --rm api pytest

migrate:
	alembic upgrade head

seed:
	python scripts/seed_superadmin.py
	python scripts/seed_countries.py
	python scripts/seed_languages.py
	python scripts/sync_redis_counters.py

lint:
	ruff check app/ tests/

mypy:
	mypy app/
```
