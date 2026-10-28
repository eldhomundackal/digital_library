# Digital Library API

A production-ready FastAPI backend for a digital library platform. Supports reader and publisher roles, book management, KYC verification, download tracking, reviews, and a full admin panel.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115+ (async) |
| ORM | SQLAlchemy 2.0 async |
| Database | PostgreSQL 16 |
| Cache / Queue broker | Redis 7 |
| Task queue | Celery 5 |
| Auth | JWT (HS256) + OTP + OIDC/OAuth2 |
| Storage | Local filesystem or AWS S3 |
| Schema validation | Pydantic v2 |
| Migrations | Alembic |
| Python | 3.12+ |

---

## Project Structure

```
digital-library-api/
├── app/
│   ├── api/v1/              # HTTP routers (thin — one line per endpoint)
│   │   └── admin/           # Admin-only routers
│   ├── auth/                # Auth providers (local, JWT, OTP, OIDC, OAuth2)
│   ├── core/                # Config, dependencies, middleware
│   ├── db/
│   │   ├── models/          # SQLAlchemy ORM models (28 tables)
│   │   └── migrations/      # Alembic migration scripts
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # All business logic
│   ├── storage/             # S3 + local file storage abstraction
│   ├── tasks/               # Celery async tasks
│   └── utils/               # Shared helpers (audit, cache, pagination, slug)
├── scripts/                 # One-off seed scripts
├── tests/
│   ├── unit/                # Unit tests (no DB/Redis required)
│   └── integration/         # Integration test stubs (require live services)
├── docs/                    # Architecture and design docs
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
├── Makefile
└── .env.example
```

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd digital-library-api
cp .env.example .env
# Edit .env — set SECRET_KEY, SMTP credentials, S3 keys, etc.
```

### 2. Start Postgres and Redis

```bash
docker compose up postgres redis -d
```

### 3. Install dependencies

```bash
pip install poetry
poetry install
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Seed the database

```bash
python scripts/seed_superadmin.py
python scripts/seed_countries.py
python scripts/seed_languages.py
```

### 6. Start the API

```bash
uvicorn app.main:app --reload
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 7. Start Celery workers (separate terminal)

```bash
celery -A app.tasks.celery_app worker --loglevel=info
celery -A app.tasks.celery_app beat --loglevel=info
```

---

## Docker (full stack)

Start everything — API, Postgres, Redis, Celery worker and beat — in one command:

```bash
docker compose up --build
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:password@localhost:5432/digital_library` | Postgres connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key — **change this** |
| `AUTH_PROVIDER` | `local` | `local`, `oidc`, or `oauth2` |
| `STORAGE_PROVIDER` | `local` | `local` or `s3` |
| `MAX_BOOK_PDF_SIZE_MB` | `50` | Max PDF upload size |
| `MAX_DOWNLOADS_PER_DAY` | `5` | Per-user daily download cap |
| `MAX_DOWNLOADS_PER_MONTH` | `15` | Per-user monthly download cap |
| `SUPERADMIN_EMAIL` | `superadmin@library.com` | Seed superadmin email |
| `SUPERADMIN_PASSWORD` | `SuperAdmin123!` | Seed superadmin password — **change this** |

Full variable list is in `.env.example`.

---

## API Overview

### Public endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login, returns access + refresh tokens |
| POST | `/api/v1/auth/verify-email` | Verify email with OTP |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Invalidate refresh token |
| GET | `/api/v1/books` | Browse approved books |
| GET | `/api/v1/books/{book_id}` | Book detail |
| GET | `/api/v1/authors` | List authors |
| GET | `/api/v1/categories` | List categories |
| GET | `/api/v1/tags` | List tags |

### Reader endpoints (authenticated)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/users/me` | My profile |
| PATCH | `/api/v1/users/me` | Update profile |
| POST | `/api/v1/books/{book_id}/download` | Download a book (pre-signed URL) |
| POST | `/api/v1/books/{book_id}/reviews` | Submit a review |
| POST | `/api/v1/reviews/{review_id}/replies` | Reply to a review |

### Publisher endpoints (KYC approved)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/publisher/books` | My books |
| POST | `/api/v1/publisher/books` | Upload a new book |
| PATCH | `/api/v1/publisher/books/{book_id}` | Edit a book |
| POST | `/api/v1/publisher/books/{book_id}/submit` | Submit for review |
| GET | `/api/v1/publisher/analytics/downloads` | Download analytics |
| POST | `/api/v1/kyc/apply` | Submit KYC application |

### Admin endpoints (staff / admin / superadmin)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/admin/dashboard` | Platform overview |
| GET | `/api/v1/admin/audit-log` | Audit trail |
| GET | `/api/v1/admin/users` | Manage users |
| GET | `/api/v1/admin/kyc` | Review KYC applications |
| POST | `/api/v1/admin/kyc/{kyc_id}/approve` | Approve KYC |
| GET | `/api/v1/admin/books` | Book moderation queue |
| POST | `/api/v1/admin/books/{book_id}/approve` | Approve a book |
| GET | `/api/v1/admin/analytics` | Platform analytics |
| GET | `/api/v1/admin/activity-feed` | Activity feed |

Full interactive docs: `GET /docs` (Swagger UI) or `GET /redoc`.

---

## User Roles

```
superadmin  →  full access to everything
admin       →  all admin endpoints
staff       →  dashboard, KYC review, book moderation
publisher   →  upload books (requires KYC approval)
reader      →  browse, download, review
anonymous   →  read-only public endpoints
```

---

## Key Business Rules

- **KYC required** — publishers must have an approved KYC before uploading books.
- **Book lifecycle** — `DRAFT → PENDING → APPROVED | REJECTED`. Approved books are publicly visible.
- **Download limits** — 5/day and 15/month per user per book (configurable).
- **Download URLs** — pre-signed S3 URLs, valid for 10 minutes, never stored in DB.
- **One review per user per book** — enforced at DB and service level.
- **Publishers cannot review their own books.**
- **Soft deletes only** — no hard deletes on users, books, reviews, or publishers.
- **OTP** — 10-minute TTL, 5 attempt limit before lockout.

---

## Development Commands

```bash
make dev          # Start full stack (docker compose up --build)
make migrate      # Run alembic upgrade head
make seed         # Run all seed scripts
make test         # Run test suite
make lint         # isort check + black check + pylint
make format       # Auto-fix imports and formatting
```

---

## Running Tests

```bash
# Unit tests only (no DB/Redis needed)
pytest tests/unit/

# All tests (integration tests require running Postgres + Redis)
pytest tests/
```

Unit tests: **18 passing**. Integration tests are stubs that skip until a live stack is available.

---

## License

MIT
