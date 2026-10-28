# Scripts & main.py

App entry point, seed scripts and Alembic env.py.

---

## `app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.router import api_router
from app.core.config import settings
from app.core.middleware import (
    AuditMiddleware, RequestLoggingMiddleware, global_exception_handler
)
from app.db.session import engine
from app.utils.number_generator import sync_from_db
import redis.asyncio as aioredis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # 1. Create Redis connection pool, store on app.state.redis
    app.state.redis = await aioredis.from_url(settings.REDIS_URL)
    # 2. Sync number generator counters from DB
    #    For each entity type: sync_from_db(entity_type, db, redis)
    # 3. Log startup message with environment and version
    yield
    # --- Shutdown ---
    # 4. Close Redis connection pool
    await app.state.redis.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,   # hide Swagger in production
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware (order matters: outermost = first in, last out)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(AuditMiddleware)

    # Global exception handler
    app.add_exception_handler(Exception, global_exception_handler)

    # Mount local static files (dev only)
    if settings.STORAGE_PROVIDER == "local":
        app.mount("/static", StaticFiles(directory="/tmp/digital-library"), name="static")

    # Include all API routes
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
```

---

## `alembic/env.py`

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.config import settings
from app.db.base import Base
from app.db.models import *   # CRITICAL: imports all models so Alembic detects all tables

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))
# Note: Alembic uses sync URL; strip +asyncpg for migrations

fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    # Standard Alembic offline mode
    ...

def run_migrations_online() -> None:
    # Standard Alembic online mode with engine_from_config
    ...

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

## `scripts/seed_superadmin.py`

```python
"""
One-time script to create the superadmin account.
Run once on first deployment:
    python scripts/seed_superadmin.py

Reads credentials from environment or .env file.
Refuses to run if a superadmin already exists.
"""
import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models.user import User
from app.core.config import settings
from app.auth.password import hash_password
from app.utils.number_generator import generate

async def seed_superadmin():
    async with AsyncSessionLocal() as db:
        # 1. Check if superadmin already exists -> print message and exit if so
        # 2. Generate number: USR-000001
        # 3. Create User(role="superadmin", is_super=True, is_email_verified=True)
        # 4. Create StaffProfile(first_name, last_name)
        # 5. Commit
        # 6. Print: "Superadmin created: {email}"

asyncio.run(seed_superadmin())
```

---

## `scripts/seed_countries.py`

```python
"""
Seeds countries, states, and cities from the countries-states-cities open dataset.
Dataset: https://github.com/dr5hn/countries-states-cities-database

Download countries+cities JSON, place at scripts/data/countries.json
Run: python scripts/seed_countries.py

Idempotent: skips existing records (matched by iso_code for countries, name+country for cities).
Sets is_seeded=True on all inserted rows.
Safe to re-run — will not overwrite manually added entries.
"""
import asyncio, json
from pathlib import Path
from app.db.session import AsyncSessionLocal
from app.db.models.utils import Country, City

async def seed():
    data = json.loads(Path("scripts/data/countries.json").read_text())
    async with AsyncSessionLocal() as db:
        for country_data in data:
            # Upsert country by iso_code (skip if exists)
            # For each city in country_data["cities"]:
            #   Upsert city by name+country_id (skip if exists)
        await db.commit()
        print(f"Seeded {len(data)} countries")

asyncio.run(seed())
```

---

## `scripts/seed_languages.py`

```python
"""
Seeds predefined languages list.
Edit LANGUAGES list below to add/remove supported languages.
Idempotent: skips existing records matched by iso_code.
"""
LANGUAGES = [
    {"name": "English",    "iso_code": "en"},
    {"name": "Arabic",     "iso_code": "ar"},
    {"name": "French",     "iso_code": "fr"},
    {"name": "Spanish",    "iso_code": "es"},
    {"name": "German",     "iso_code": "de"},
    {"name": "Hindi",      "iso_code": "hi"},
    {"name": "Malayalam",  "iso_code": "ml"},
    {"name": "Tamil",      "iso_code": "ta"},
    {"name": "Mandarin",   "iso_code": "zh"},
    {"name": "Portuguese", "iso_code": "pt"},
    {"name": "Japanese",   "iso_code": "ja"},
    {"name": "Russian",    "iso_code": "ru"},
    # Add more as needed
]

async def seed():
    async with AsyncSessionLocal() as db:
        for lang in LANGUAGES:
            # Upsert by iso_code, set is_seeded=True
        await db.commit()
        print(f"Seeded {len(LANGUAGES)} languages")
```

---

## `scripts/sync_redis_counters.py`

```python
"""
Syncs Redis number generator counters with actual DB row counts.
Run after:
- First deployment (before seed_superadmin)
- Redis flush or restart
- Data migration that inserted rows bypassing the app

Also called automatically at app startup via lifespan.
"""
import asyncio
from app.db.session import AsyncSessionLocal
from app.utils.number_generator import sync_from_db
import redis.asyncio as aioredis
from app.core.config import settings

ENTITY_TYPES = ["user", "publisher", "book", "kyc", "download", "review"]

async def sync_all():
    redis = await aioredis.from_url(settings.REDIS_URL)
    async with AsyncSessionLocal() as db:
        for entity_type in ENTITY_TYPES:
            count = await sync_from_db(entity_type, db, redis)
            print(f"  {entity_type}: counter set to {count}")
    await redis.close()
    print("Redis counters synced.")

asyncio.run(sync_all())
```

---

## `app/core/constants.py` — Enums and string constants

```python
from enum import StrEnum

class UserRole(StrEnum):
    READER     = "reader"
    PUBLISHER  = "publisher"
    STAFF      = "staff"
    ADMIN      = "admin"
    SUPERADMIN = "superadmin"

class KYCStatus(StrEnum):
    INCOMPLETE  = "INCOMPLETE"
    PENDING     = "PENDING"
    IN_REVIEW   = "IN_REVIEW"
    APPROVED    = "APPROVED"
    REJECTED    = "REJECTED"
    RESUBMITTED = "RESUBMITTED"

class BookStatus(StrEnum):
    DRAFT    = "DRAFT"
    PENDING  = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

class DocumentType(StrEnum):
    GOVERNMENT_ID       = "government_id"
    PUBLISHING_LICENSE  = "publishing_license"
    BUSINESS_REGISTRATION = "business_registration"

class StaffPermission(StrEnum):
    MANAGE_BOOKS       = "manage_books"
    MANAGE_PUBLISHERS  = "manage_publishers"
    MANAGE_USERS       = "manage_users"
    MANAGE_REVIEWS     = "manage_reviews"
    MANAGE_CATEGORIES  = "manage_categories"
    MANAGE_TAGS        = "manage_tags"
    MANAGE_UTILS       = "manage_utils"
    VIEW_ANALYTICS     = "view_analytics"

class NotificationType(StrEnum):
    OTP_EMAIL_VERIFICATION    = "OTP_EMAIL_VERIFICATION"
    OTP_PASSWORD_RESET        = "OTP_PASSWORD_RESET"
    WELCOME                   = "WELCOME"
    KYC_SUBMITTED             = "KYC_SUBMITTED"
    KYC_APPROVED              = "KYC_APPROVED"
    KYC_REJECTED              = "KYC_REJECTED"
    KYC_RESUBMISSION_REQUESTED= "KYC_RESUBMISSION_REQUESTED"
    KYC_NEW_APPLICATION       = "KYC_NEW_APPLICATION"
    BOOK_SUBMITTED            = "BOOK_SUBMITTED"
    BOOK_APPROVED             = "BOOK_APPROVED"
    BOOK_REJECTED             = "BOOK_REJECTED"
    BOOK_RESUBMITTED          = "BOOK_RESUBMITTED"
    REVIEW_REPLY              = "REVIEW_REPLY"
    PUBLISHER_RESPONSE        = "PUBLISHER_RESPONSE"
    DOWNLOAD_LIMIT_WARNING    = "DOWNLOAD_LIMIT_WARNING"
    COMMENT_REPORTED          = "COMMENT_REPORTED"
    NEW_PUBLISHER_REGISTRATION= "NEW_PUBLISHER_REGISTRATION"
```

---

## Claude Code instructions

When implementing from this plan, follow this order strictly:

1. **Read all 8 tabs** in full before writing any code
2. **Start with Phase 1** from the Execution Plan checklist in the Project Plan tab
3. **Never deviate from the API shapes** defined in the Project Plan — all request/response schemas are locked
4. **Use the ORM models exactly as defined** — do not add or remove columns without updating the schema tab
5. **Every service method must match its pseudocode signature** — same method name, same parameters, same return type
6. **Routers are thin** — one line per endpoint, all logic in services
7. **Always fire Celery tasks with `.delay()`** — never `await` them inside service methods
8. **Always call `audit_action()`** at the end of every admin/staff mutating service method
9. **Always invalidate Redis cache** after any mutation that affects listed resources (books, categories, tags)
10. **Run `alembic upgrade head`** after adding any new model or column
11. **Tests are mandatory** — write unit test per service method, integration test per router group
