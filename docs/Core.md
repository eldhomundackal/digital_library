# Core — Dependencies, Middleware & Auth Providers

Everything in app/core/ and app/auth/ — the foundation every router and service builds on.

---

## `app/auth/local.py` — LocalAuthProvider

```python
class LocalAuthProvider(BaseAuthProvider):
    """Handles all auth when AUTH_PROVIDER=local."""

    async def register(self, payload: RegisterRequest) -> UserInfoSchema:
        # Hash password with passlib bcrypt
        # Return UserInfoSchema (no IDP sub, email_verified=False)

    async def validate_token(self, token: str) -> TokenPayloadSchema:
        # Decode JWT using SECRET_KEY and HS256
        # Raise 401 if expired or invalid signature
        # Return TokenPayloadSchema(user_id, role, exp)

    async def refresh_token(self, token: str) -> TokenSchema:
        # Decode refresh token
        # Issue new access token
        # Return TokenSchema

    async def logout(self, token: str) -> None:
        # Add refresh token to Redis blacklist: SET blacklist:{token} 1 EX {remaining_ttl}

    async def get_user_info(self, token: str) -> UserInfoSchema:
        # Decode token, load user from DB, return UserInfoSchema

    async def get_authorization_url(self) -> str:
        raise NotImplementedError("Local provider has no authorization URL")

    async def handle_callback(self, code: str, state: str) -> TokenSchema:
        raise NotImplementedError
```

---

## `app/auth/oidc.py` — OIDCAuthProvider

```python
class OIDCAuthProvider(BaseAuthProvider):
    """
    Generic OIDC provider.
    Configured via env vars — works for Keycloak, Okta, Cognito unchanged.
    """

    def __init__(self):
        self.issuer_url = settings.OIDC_ISSUER_URL
        self.client_id = settings.OIDC_CLIENT_ID
        self.client_secret = settings.OIDC_CLIENT_SECRET
        self.scopes = settings.OIDC_SCOPES
        self._jwks = None   # cached JWK set

    async def get_authorization_url(self) -> str:
        # Build authorization URL with code challenge (PKCE)
        # Store state + code_verifier in Redis (TTL 10min)
        # Return URL for frontend redirect

    async def handle_callback(self, code: str, state: str) -> TokenSchema:
        # 1. Verify state from Redis -> 400 if not found (CSRF)
        # 2. Exchange code for tokens at OIDC_ISSUER_URL/token endpoint
        # 3. Return TokenSchema(id_token, access_token)

    async def validate_token(self, token: str) -> TokenPayloadSchema:
        # 1. Fetch JWKS from {issuer_url}/.well-known/jwks.json (cached)
        # 2. Decode and verify JWT signature using JWKS
        # 3. Verify iss, aud, exp claims
        # 4. Return TokenPayloadSchema

    async def get_user_info(self, token: str) -> UserInfoSchema:
        # Decode ID token claims OR call {issuer_url}/userinfo endpoint
        # Map to normalized UserInfoSchema(sub, email, first_name, last_name, email_verified)

    async def refresh_token(self, token: str) -> TokenSchema:
        # POST to {issuer_url}/token with grant_type=refresh_token

    async def logout(self, token: str) -> None:
        # POST to {issuer_url}/logout (end_session_endpoint)
```

---

## `app/auth/oauth2.py` — OAuth2AuthProvider

```python
class OAuth2AuthProvider(BaseAuthProvider):
    """
    Pure OAuth 2.0 provider (no OIDC identity layer).
    Falls back to userinfo endpoint for user details.
    """

    async def get_authorization_url(self) -> str:
        # Build URL from OAUTH2_AUTHORIZATION_URL + client_id + scopes + state

    async def handle_callback(self, code: str, state: str) -> TokenSchema:
        # Exchange code at OAUTH2_TOKEN_URL

    async def get_user_info(self, token: str) -> UserInfoSchema:
        # GET OAUTH2_USERINFO_URL with Bearer token
        # Map response to UserInfoSchema
        # Raise 501 if OAUTH2_USERINFO_URL not configured

    async def validate_token(self, token: str) -> TokenPayloadSchema:
        # Validate JWT if provider issues JWTs
        # OR introspect at provider's token introspection endpoint
```

---

## `app/auth/jwt.py` — JWT helpers

```python
def create_access_token(user_id: str, role: str, expires_minutes: int = 15) -> str:
    # payload = {sub: user_id, role: role, exp: now + expires_minutes, type: "access"}
    # Sign with SECRET_KEY using HS256
    # Return encoded JWT string

def create_refresh_token(user_id: str, expires_days: int = 7) -> str:
    # payload = {sub: user_id, exp: now + expires_days, type: "refresh"}
    # Sign with SECRET_KEY
    # Return encoded JWT string

def decode_token(token: str) -> dict:
    # Decode with SECRET_KEY
    # Raise 401 HTTPException on ExpiredSignatureError or JWTError
    # Return payload dict

def create_reset_session_token() -> str:
    # Generate secure random 32-byte hex token
    # (Not a JWT — stored in Redis keyed by this token)
```

---

## `app/auth/otp.py` — OTP helpers

```python
async def generate_and_store_otp(redis: Redis, email: str, otp_type: str) -> str:
    # Generate 6-digit random OTP
    # Store in Redis: key=otp:{otp_type}:{email}, value={otp, attempts:0}
    # TTL = OTP_EXPIRE_MINUTES * 60
    # Return OTP string (passed to email task)

async def verify_otp(redis: Redis, email: str, otp_type: str, submitted_otp: str) -> bool:
    # 1. GET from Redis -> raise 400 "OTP expired or not found" if missing
    # 2. Check attempts < OTP_MAX_ATTEMPTS -> raise 429 "Too many attempts" if exceeded
    # 3. Compare submitted_otp to stored otp
    # 4. If wrong: HINCRBY attempts; raise 400 "Invalid OTP"
    # 5. If correct: DEL from Redis; return True
```

---

## `app/core/dependencies.py`

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # Yield AsyncSession from AsyncSessionLocal
    # Auto-close after request

def get_redis() -> Redis:
    # Return shared Redis client (initialized at app startup)

def get_auth_provider() -> BaseAuthProvider:
    # Auth provider factory: return correct provider based on AUTH_PROVIDER setting

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    auth_provider: BaseAuthProvider = Depends(get_auth_provider)
) -> User:
    # 1. Decode token via auth_provider.validate_token(token)
    # 2. Load User from DB by user_id in payload
    # 3. Check user.is_active -> raise 403 if deactivated
    # 4. Return User

async def get_optional_user(token: str | None = ...) -> User | None:
    # Same as get_current_user but returns None instead of raising on missing token

def require_roles(*roles: str):
    # Returns a dependency that calls get_current_user
    # Raises 403 if user.role not in roles

def require_permission(permission: str):
    # Returns a dependency that calls get_current_user
    # admin/superadmin: pass
    # staff: check StaffPermission table for permission
    # others: raise 403

async def require_approved_publisher(user: User = Depends(get_current_user)) -> User:
    # Check user.role == "publisher"
    # Check publisher_profile.kyc_status == "APPROVED"
    # Raise 403 with helpful message if KYC not approved

class PaginationParams:
    def __init__(self, page: int = 1, limit: int = 20):
        self.page = min(max(page, 1), 1000)
        self.limit = min(max(limit, 1), 100)
        self.offset = (self.page - 1) * self.limit
```

---

## `app/core/middleware.py`

```python
class AuditMiddleware(BaseHTTPMiddleware):
    """
    Automatically captures admin action context.
    Stores request info in request.state so audit_action() helper can read it.
    Does NOT write audit logs itself — service methods call audit_action().
    """
    async def dispatch(self, request: Request, call_next):
        request.state.ip_address = request.client.host
        request.state.user_agent = request.headers.get("User-Agent", "")
        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status code, response time for every request."""
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        logger.info(f"{request.method} {request.url.path} {response.status_code} {duration_ms:.1f}ms")
        return response


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches all unhandled exceptions and formats as standard ErrorResponse.
    HTTPException passes through with its own status code.
    All others return 500.
    """
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code,
                            content={"success": False, "message": exc.detail})
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500,
                        content={"success": False, "message": "Internal server error"})
```

---

## `app/utils/audit.py` — Audit action helper

```python
async def audit_action(
    db: AsyncSession,
    action: str,
    performed_by: User,
    target_type: str,
    target_id: int,
    target_label: str,
    request: Request | None = None,
    metadata: dict | None = None,
    note: str | None = None,
) -> None:
    """
    Creates an AuditLog row and optionally an ActivityFeed entry.
    Called at the end of every admin/staff mutating service method.
    """
    # 1. Create AuditLog row
    # 2. Extract ip_address from request.state if request provided
    # 3. If action in ACTIVITY_FEED_ACTIONS:
    #       Create ActivityFeed row with correct category + message
    # 4. Commit both in same transaction

ACTIVITY_FEED_ACTIONS = {
    "KYC_NEW_APPLICATION":   {"category": "actionable",     "title": "New KYC Application"},
    "BOOK_SUBMITTED":        {"category": "actionable",     "title": "New Book Pending Review"},
    "BOOK_RESUBMITTED":      {"category": "actionable",     "title": "Book Resubmitted"},
    "BOOK_APPROVED":         {"category": "informational",  "title": "Book Approved"},
    "BOOK_REJECTED":         {"category": "informational",  "title": "Book Rejected"},
    "KYC_APPROVED":          {"category": "informational",  "title": "KYC Approved"},
    "KYC_REJECTED":          {"category": "informational",  "title": "KYC Rejected"},
    "COMMENT_REPORTED":      {"category": "actionable",     "title": "Review Reported"},
    "NEW_PUBLISHER_REG":     {"category": "actionable",     "title": "New Publisher Registered"},
}
```

---

## `app/utils/number_generator.py`

```python
PREFIXES = {
    "user":      "USR",
    "publisher": "PUB",
    "book":      "BK",
    "kyc":       "KYC",
    "download":  "DL",
    "review":    "REV",
}

async def generate(entity_type: str, redis: Redis) -> str:
    """
    Atomically increments a Redis counter and returns formatted number.
    Counter synced from DB row count on startup (see scripts/sync_redis_counters.py).
    """
    prefix = PREFIXES[entity_type]
    count = await redis.incr(f"counter:{entity_type}")
    return f"{prefix}-{str(count).zfill(6)}"   # USR-000001

async def sync_from_db(entity_type: str, db: AsyncSession, redis: Redis) -> None:
    """Called on startup to sync counter with actual DB row count."""
    table_map = {"user": User, "book": Book, ...}
    count = await db.scalar(select(func.count()).select_from(table_map[entity_type]))
    await redis.set(f"counter:{entity_type}", count)
```

---

## `app/utils/cache.py` — Redis cache helpers

```python
async def get_cached(redis: Redis, key: str) -> dict | None:
    """Get JSON value from Redis. Returns None if key missing."""

async def set_cached(redis: Redis, key: str, value: dict, ttl: int = 300) -> None:
    """Store JSON value in Redis with TTL in seconds."""

async def invalidate(redis: Redis, key: str) -> None:
    """Delete a cache key."""

async def invalidate_pattern(redis: Redis, pattern: str) -> None:
    """Delete all keys matching pattern (e.g. 'cache:books:*')."""

# Cache key conventions:
# cache:books:list:{hash_of_filters}     TTL 5min
# cache:book:{uuid}                       TTL 5min
# cache:categories                        TTL 60min
# cache:tags                              TTL 30min
# cache:publisher:{uuid}                  TTL 10min
```
