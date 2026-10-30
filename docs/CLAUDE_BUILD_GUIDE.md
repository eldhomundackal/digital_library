# Digital Library — Claude Code Instructions

You are implementing a FastAPI backend for a Digital Library platform.
Read this file fully before writing a single line of code.

---

## How to use the plan docs

All 8 plan files are in the `docs/` folder. Read them in this order before starting:

| File | Read when |
|---|---|
| `docs/01-project-plan.md` | Always — architecture, folder structure, execution phases |
| `docs/02-orm-models.md` | Before touching any DB model or migration |
| `docs/03-schemas.md` | Before writing any Pydantic schema |
| `docs/04-routers.md` | Before writing any router file |
| `docs/05-services.md` | Before writing any service file |
| `docs/06-core.md` | Before writing auth, middleware, dependencies |
| `docs/07-tasks-storage.md` | Before writing Celery tasks or storage providers |
| `docs/08-scripts-main.md` | Before writing main.py or any script |

**Do not write any file without first reading its relevant doc.**
When writing `auth_service.py` → read `05-services.md` + `06-core.md`.
When writing a router → read `04-routers.md` + `03-schemas.md`.
When writing a model → read `02-orm-models.md`.

---

## Execution order

Follow the 5 phases in `docs/01-project-plan.md` exactly. Do not skip ahead.

### Phase 1 — Foundation
1. Scaffold the full folder structure from `docs/01-project-plan.md`
2. Create `pyproject.toml` with all dependencies listed in the Execution Plan
3. Create `docker-compose.yml` exactly as shown in `docs/08-scripts-main.md`
4. Create `.env` from `.env.example` in `docs/08-scripts-main.md`
5. Write `app/db/base.py` and `app/db/session.py` from `docs/02-orm-models.md`
6. Write all ORM models from `docs/02-orm-models.md` into their correct files
7. Write `alembic/env.py` from `docs/08-scripts-main.md`
8. Run: `alembic revision --autogenerate -m "initial schema"` then `alembic upgrade head`
9. Write `app/core/constants.py` from `docs/08-scripts-main.md`
10. Write `app/core/config.py` from `docs/08-scripts-main.md`
11. Write `app/auth/base.py`, `app/auth/local.py`, `app/auth/jwt.py`, `app/auth/otp.py` from `docs/06-core.md`
12. Write `app/core/dependencies.py` from `docs/06-core.md`
13. Write `app/core/middleware.py` from `docs/06-core.md`
14. Write `app/schemas/common.py` and `app/schemas/auth.py` from `docs/03-schemas.md`
15. Write `app/services/auth_service.py` from `docs/05-services.md`
16. Write `app/api/v1/auth.py` from `docs/04-routers.md`
17. Write `app/main.py` from `docs/08-scripts-main.md`
18. Write `scripts/seed_superadmin.py` from `docs/08-scripts-main.md`
19. Run seed: `python scripts/seed_superadmin.py`
20. Write unit tests for AuthService in `tests/unit/test_auth_service.py`
21. Verify: `docker compose up` — API must start and return 200 on GET /docs

### Phase 2 — Users, KYC & Publisher onboarding
22. Write all remaining schemas from `docs/03-schemas.md`
23. Write `app/storage/base.py`, `app/storage/s3.py`, `app/storage/local.py`, `app/storage/factory.py`, `app/storage/validators.py` from `docs/07-tasks-storage.md`
24. Write `app/utils/number_generator.py`, `app/utils/audit.py`, `app/utils/cache.py`, `app/utils/slug.py`, `app/utils/pagination.py` from `docs/06-core.md`
25. Write `app/services/user_service.py` and `app/services/publisher_service.py` from `docs/05-services.md`
26. Write `app/services/kyc_service.py` from `docs/05-services.md`
27. Write `app/api/v1/users.py`, `app/api/v1/publishers.py`, `app/api/v1/kyc.py` from `docs/04-routers.md`
28. Write `app/api/v1/admin/users.py`, `app/api/v1/admin/kyc.py` from `docs/04-routers.md`
29. Write `app/tasks/celery_app.py`, `app/tasks/email_tasks.py` from `docs/07-tasks-storage.md`
30. Write `scripts/seed_countries.py`, `scripts/seed_languages.py`, `scripts/sync_redis_counters.py` from `docs/08-scripts-main.md`
31. Write `app/api/v1/utils.py`, `app/api/v1/admin/utils.py` from `docs/04-routers.md`
32. Write integration tests for KYC flow in `tests/integration/test_kyc_api.py`

### Phase 3 — Books
33. Write `app/services/book_service.py` and `app/services/author_service.py` from `docs/05-services.md`
34. Write all book routers from `docs/04-routers.md`: `books.py`, `publisher_books.py`, `authors.py`, `categories.py`, `tags.py`
35. Write admin book routers: `admin/books.py`, `admin/tags.py`, `admin/categories.py`, `admin/authors.py`
36. Write integration tests in `tests/integration/test_books_api.py`

### Phase 4 — Reviews, Downloads & Notifications
37. Write `app/services/review_service.py`, `app/services/download_service.py`, `app/services/notification_service.py`, `app/services/analytics_service.py` from `docs/05-services.md`
38. Write `app/api/v1/reviews.py`, `app/api/v1/admin/reviews.py` from `docs/04-routers.md`
39. Write `app/api/v1/admin/analytics.py` from `docs/04-routers.md`
40. Write `app/tasks/notification_tasks.py` from `docs/07-tasks-storage.md`
41. Write integration tests in `tests/integration/test_reviews_api.py`, `tests/integration/test_downloads_api.py`

### Phase 5 — Admin Panel & Hardening
42. Write `app/services/admin_service.py` from `docs/05-services.md`
43. Write `app/api/v1/admin/dashboard.py`, `app/api/v1/admin/audit.py`, `app/api/v1/admin/activity.py`, `app/api/v1/admin/notifications.py` from `docs/04-routers.md`
44. Write `app/auth/oidc.py` and `app/auth/oauth2.py` from `docs/06-core.md`
45. Wire `app/api/router.py` with all routers from `docs/04-routers.md`
46. Write integration tests in `tests/integration/test_admin_api.py`
47. Final: run full test suite — all tests must pass

---

## Rules — never break these

1. **Routers are thin.** One line per endpoint: validate input, call service, return response. Zero business logic in routers.
2. **All business logic lives in services.** If you are writing more than 3 lines of logic in a router, stop and move it to the service.
3. **Never expose integer IDs in the API.** Always use `uuid` in URLs and responses. Integer `id` is internal DB only.
4. **Never store files in the database.** Only S3 paths/URLs. Use `storage_provider.upload()` always.
5. **Never hardcode limits or file sizes.** Always read from `settings.*` (e.g. `settings.MAX_BOOK_PDF_SIZE_MB`).
6. **Always call `audit_action()`** at the end of every admin/staff mutating service method. No exceptions.
7. **Always fire Celery tasks with `.delay()`** — never `await` them inside service methods.
8. **Always invalidate Redis cache** after any mutation affecting books, categories or tags.
9. **Always run `alembic upgrade head`** after adding any new model or column before writing service code.
10. **Auth guards on every protected endpoint.** Check `docs/04-routers.md` for the exact guard per endpoint.
11. **Match schema field names exactly.** The API shapes in `docs/03-schemas.md` are locked — do not rename fields.
12. **Soft deletes only.** Never hard delete users, books, reviews, publishers. Set `is_active=False` and `deleted_at=now()`.
13. **One rating per user per book.** Enforce at DB level (UniqueConstraint) and service level.
14. **Publishers cannot rate their own books.** Check in `review_service.submit_review()`.
15. **Download URL is never stored.** Generate pre-signed S3 URL on demand, return to client, never save to DB.

---

## Key business rules (quick reference)

```
User roles:       superadmin > admin > staff > publisher > reader > anonymous
Publisher access: KYC must be APPROVED before any book upload
Book lifecycle:   DRAFT -> PENDING -> APPROVED | REJECTED -> (edit) -> PENDING
KYC lifecycle:    INCOMPLETE -> PENDING -> APPROVED | REJECTED -> RESUBMITTED -> PENDING
Download limits:  5/day, 15/month per user per book (configurable via env vars)
Download URL TTL: 10 minutes (pre-signed S3)
OTP TTL:          10 minutes, max 5 attempts then locked
Refresh token:    7 days, HttpOnly cookie, path=/api/v1/auth/refresh
Access token:     15 minutes, Bearer header
Notifications:    expire after 7 days (Celery Beat cleanup daily at midnight)
File limits:      PDF 50MB, thumbnail 2MB, KYC docs 10MB (all configurable)
```

---

## Project structure (top level)

```
digital-library-api/
├── app/
│   ├── api/v1/          # Routers (see docs/04-routers.md)
│   ├── auth/            # Auth providers (see docs/06-core.md)
│   ├── core/            # Config, deps, middleware (see docs/06-core.md)
│   ├── db/models/       # ORM models (see docs/02-orm-models.md)
│   ├── db/migrations/   # Alembic migrations
│   ├── schemas/         # Pydantic schemas (see docs/03-schemas.md)
│   ├── services/        # Business logic (see docs/05-services.md)
│   ├── storage/         # S3 + Local providers (see docs/07-tasks-storage.md)
│   ├── tasks/           # Celery tasks (see docs/07-tasks-storage.md)
│   └── utils/           # Shared helpers
├── scripts/             # Seed scripts (see docs/08-scripts-main.md)
├── tests/               # Unit + integration tests
├── docs/                # Plan files (this directory)
├── alembic.ini
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── Makefile
└── CLAUDE.md            # This file
```

---

## Common commands

```bash
# Start everything
make dev

# Run migrations
make migrate

# Seed database (run once on first deploy)
make seed

# Run tests
make test

# Lint
make lint

# Start Celery worker separately
celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery beat scheduler
celery -A app.tasks.celery_app beat --loglevel=info
```

---

## Code style & quality rules

### Formatter — Black

**Every Python file must be Black-formatted before it is considered done.**

Black is non-negotiable — do not write code that would fail Black formatting.

```bash
# Format a single file
black app/services/auth_service.py

# Format entire project
black app/ tests/ scripts/

# Check without changing (used in CI)
black --check app/ tests/ scripts/
```

Black configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ["py312"]
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | alembic/versions
)/
'''
```

**Black rules Claude Code must follow while writing code:**

- Maximum line length is **88 characters** — never exceed this
- Use **double quotes** for all strings — Black enforces this; never use single quotes in Python code
- Always add a **trailing comma** in multi-line function arguments, lists and dicts — Black requires this
- Never manually align assignment operators or dictionary values — Black will reformat them
- Leave **two blank lines** between top-level definitions (classes, functions)
- Leave **one blank line** between methods inside a class
- After writing any file, mentally verify it would pass `black --check` before moving on

---

### Linter — Pylint

**Every Python file must pass Pylint with a minimum score of 8.0/10.**

```bash
# Lint a single file
pylint app/services/auth_service.py

# Lint entire app
pylint app/ --fail-under=8.0

# Lint with project config (reads pyproject.toml)
pylint app/ tests/
```

Pylint configuration in `pyproject.toml`:
```toml
[tool.pylint.main]
py-version = "3.12"
jobs = 0                          # auto-detect CPU count
recursive = true
fail-under = 8.0

[tool.pylint.messages_control]
disable = [
    "missing-module-docstring",   # top-level module docstrings not required
    "too-few-public-methods",     # Pydantic models and simple classes are fine
    "too-many-arguments",         # service methods legitimately need many args
    "too-many-instance-attributes",# SQLAlchemy models have many columns
    "import-outside-toplevel",    # used in factory functions intentionally
]

[tool.pylint.format]
max-line-length = 88              # match Black

[tool.pylint.design]
max-args = 10                     # allow up to 10 function arguments
max-locals = 20                   # allow up to 20 local variables
max-returns = 6
max-branches = 12

[tool.pylint.similarities]
min-similarity-lines = 10         # ignore short duplicate blocks
```

**Pylint rules Claude Code must follow while writing code:**

- Every **class** must have a docstring — at minimum one line describing its purpose
- Every **public method** must have a docstring — describe what it does, not how
- Every **module** (file) does NOT need a docstring (disabled above)
- All **imports** must be at the top of the file, grouped: stdlib → third party → local
- No **unused imports** — remove any import that is not referenced in the file
- No **unused variables** — prefix intentionally unused variables with `_`
- No **bare except** clauses — always catch a specific exception type
- No **wildcard imports** — never use `from module import *`
- All **constants** at module level must be UPPER_SNAKE_CASE
- All **private methods** must be prefixed with `_`
- Variable names must be **descriptive** — no single-letter names except loop counters (`i`, `j`) and type vars (`T`)
- No **hardcoded magic numbers** — extract to a named constant or read from settings

---

### Import ordering — isort

isort keeps imports consistent and avoids Pylint import-order warnings.

```bash
# Sort imports in a file
isort app/services/auth_service.py

# Sort entire project
isort app/ tests/ scripts/
```

isort configuration in `pyproject.toml`:
```toml
[tool.isort]
profile = "black"                 # compatible with Black formatting
line_length = 88
known_first_party = ["app"]
known_third_party = ["fastapi", "sqlalchemy", "pydantic", "celery", "redis", "boto3"]
```

**Import order Claude Code must follow in every file:**

```python
# 1. Standard library
import uuid
from datetime import datetime
from typing import AsyncGenerator

# 2. Third-party packages
from fastapi import Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

# 3. Local application imports
from app.core.config import settings
from app.db.models.user import User
from app.schemas.auth import LoginRequest
```

---

### Type hints

All code must use **full type hints** — Pylint and mypy both check these.

```python
# Correct
async def get_user(user_id: int, db: AsyncSession) -> User | None:
    ...

# Wrong — missing return type and parameter types
async def get_user(user_id, db):
    ...
```

Rules:
- Every function and method must have **parameter types** and a **return type**
- Use `X | None` (Python 3.10+ union syntax) — never `Optional[X]`
- Use `list[X]` and `dict[K, V]` — never `List[X]` or `Dict[K, V]` (no need to import from typing)
- Use `AsyncGenerator[X, None]` for async generator functions (e.g. `get_db`)
- Pydantic model fields must have explicit types — never rely on inference

---

### Pre-commit workflow

After writing each file, run this sequence before moving to the next file:

```bash
# Step 1: Sort imports
isort path/to/file.py

# Step 2: Format with Black
black path/to/file.py

# Step 3: Lint with Pylint
pylint path/to/file.py

# Step 4: Fix any Pylint issues, then re-run until score >= 8.0
```

Or run all at once across the whole project:
```bash
make lint       # runs isort check + black check + pylint
make format     # runs isort + black (auto-fixes)
```

Add these to the `Makefile`:
```makefile
format:
	isort app/ tests/ scripts/
	black app/ tests/ scripts/

lint:
	isort --check app/ tests/ scripts/
	black --check app/ tests/ scripts/
	pylint app/ --fail-under=8.0

typecheck:
	mypy app/
```

---

### Dev dependencies to add to `pyproject.toml`

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.3"
pytest-asyncio = "^0.24"
httpx = "^0.28"
factory-boy = "^3.3"
faker = "^33.0"
black = "^24.0"
pylint = "^3.3"
isort = "^5.13"
mypy = "^1.13"
```

---

## Anti-hallucination rules — strictly enforced

These rules exist to prevent invented code, guessed behaviour and undocumented decisions
from entering the codebase. Follow every rule without exception.

---

### The single most important rule

> **If it is not written in the docs, do not implement it.**

Every endpoint, every field, every business rule, every error message, every Redis key,
every Celery task — all of it is already defined in the 8 doc files. Your job is to
translate the docs into working code, not to design new behaviour.

---

### What you must never invent

| Category | What is forbidden |
|---|---|
| **Endpoints** | Never add an endpoint that is not in `docs/04-routers.md` |
| **Schema fields** | Never add, rename or remove a field that is not in `docs/03-schemas.md` |
| **DB columns** | Never add, rename or remove a column not in `docs/02-orm-models.md` |
| **Business rules** | Never add validation, logic or a side effect not in `docs/05-services.md` |
| **Error messages** | Never invent an error message — use the exact wording from the docs |
| **Status values** | Never add a new status string — all enums are defined in `app/core/constants.py` |
| **Redis keys** | Never invent a new Redis key pattern — all keys are defined in `docs/07-tasks-storage.md` |
| **Celery tasks** | Never create a new Celery task — all 7 tasks are defined in `docs/07-tasks-storage.md` |
| **Relationships** | Never add a new ORM relationship not shown in `docs/02-orm-models.md` |
| **Config keys** | Never add a new `settings.*` key — all env vars are defined in `docs/08-scripts-main.md` |
| **Tables** | Never create a new DB table — all 28 tables are defined in `docs/02-orm-models.md` |
| **Permissions** | Never invent a new permission string — all permissions are in `app/core/constants.py` |

---

### When you are unsure — STOP and ask

If you encounter any of these situations, **stop immediately and ask** rather than guessing:

```
- The docs do not cover this specific case
- Two doc files seem to contradict each other
- A library behaves differently than described
- You would need to add a field or endpoint not in the docs
- You are about to write logic the docs did not describe
- You are unsure which of two approaches the docs intend
```

**Never silently fill in gaps with your own judgement.**
Write a comment like:

```python
# QUESTION: docs/05-services.md does not specify what happens when
# the publisher tries to resubmit a document that is already APPROVED.
# Stopping here — please clarify before I continue.
```

Then stop. Do not proceed past that point until clarified.

---

### Source of truth hierarchy

When there is any ambiguity, resolve it using this hierarchy — highest authority first:

```
1. docs/02-orm-models.md     → DB schema, column names, relationships
2. docs/03-schemas.md        → API field names, types, validation rules
3. docs/05-services.md       → Business logic, error conditions, side effects
4. docs/04-routers.md        → Endpoint paths, auth guards, HTTP methods
5. docs/01-project-plan.md   → Architecture decisions, tech choices
6. docs/06-core.md           → Auth, middleware, dependency behaviour
7. docs/07-tasks-storage.md  → Celery tasks, Redis keys, S3 paths
8. docs/08-scripts-main.md   → main.py, scripts, env vars, constants
```

If two sources conflict, the **higher-ranked doc wins**. Report the conflict in a comment
and follow the higher-ranked doc.

---

### No creative improvements

Do not improve the design while implementing it. Specifically:

- Do not add extra fields to a response "because they would be useful"
- Do not add extra validation "because it seems safer"
- Do not optimise a query in a way that changes its behaviour
- Do not add caching to something the docs do not say to cache
- Do not add a new notification type the docs do not define
- Do not add logging beyond what is needed for errors
- Do not add helper endpoints "for convenience"

If you think something should be improved, write a `# TODO:` comment describing the
improvement and continue implementing exactly what the docs say.

---

### Third-party libraries — use only what is listed

Only use libraries that appear in the `pyproject.toml` dependencies defined in
`docs/01-project-plan.md`. Do not introduce any new package.

If a task genuinely requires a library not in the list:

```python
# MISSING DEPENDENCY: this task requires `python-slugify` which is not in pyproject.toml.
# Please add it to dependencies before I continue.
```

Stop and ask. Do not `pip install` anything not already listed.

---

### No assumptions about external services

- Do not assume the S3 bucket has any specific policy — use the storage provider abstraction
- Do not assume the SMTP server supports any specific feature — use only standard SMTP calls
- Do not assume Redis supports any command not in the standard Redis client
- Do not assume the IDP (Keycloak/Okta/Cognito) exposes any endpoint not in the OIDC standard

---

### Self-check before submitting any file

Before marking a file as done, answer every question:

```
✓ Does every method signature match docs/05-services.md exactly?
✓ Does every endpoint path match docs/04-routers.md exactly?
✓ Does every schema field match docs/03-schemas.md exactly?
✓ Does every ORM column match docs/02-orm-models.md exactly?
✓ Did I invent any business logic not described in the docs?
✓ Did I add any field, endpoint or table not in the docs?
✓ Did I use any library not in pyproject.toml?
✓ Did I hardcode any value that should come from settings?
✓ Did I write any bare except, wildcard import or magic number?
✓ Does the file pass black --check and pylint with score >= 8.0?
```

If any answer is "no" or "not sure" — fix it before moving on.

---

## If you are unsure about anything

1. Check the relevant doc file in `docs/` first
2. The API shapes in `docs/03-schemas.md` are the source of truth for request/response
3. The service pseudocode in `docs/05-services.md` is the source of truth for business logic
4. The ORM models in `docs/02-orm-models.md` are the source of truth for the DB schema
5. **When in doubt, stop and ask — wrong architecture is harder to fix than missing code**
6. Write a `# QUESTION:` comment at the exact line where you are unsure and stop there
7. Never guess, never fill gaps silently, never improve without being asked
