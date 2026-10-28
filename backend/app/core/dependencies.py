from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.base import BaseAuthProvider
from app.auth.factory import get_auth_provider
from app.db.models.user import User
from app.db.session import AsyncSessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session; auto-closes after the request."""
    async with AsyncSessionLocal() as session:
        yield session


def get_redis(request: Request) -> Redis:
    """Return the shared Redis client stored on app.state at startup."""
    return request.app.state.redis


def get_provider() -> BaseAuthProvider:
    """Return the configured auth provider."""
    return get_auth_provider()


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    auth_provider: BaseAuthProvider = Depends(get_provider),
) -> User:
    """Decode the Bearer token and return the active User. Raises 401 if invalid."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = await auth_provider.validate_token(token)
    user_uuid: str | None = payload.get("sub")
    if not user_uuid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.uuid == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    auth_provider: BaseAuthProvider = Depends(get_provider),
) -> User | None:
    """Same as get_current_user but returns None instead of raising on missing token."""
    if not token:
        return None
    try:
        return await get_current_user(token, db, auth_provider)
    except HTTPException:
        return None


def require_roles(*roles: str):
    """Dependency factory that enforces one of the given roles."""

    async def guard(current_user: User = Depends(get_current_user)) -> User:
        """Raise 403 if current user's role is not in the allowed list."""
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return guard


def require_permission(permission: str):
    """Dependency factory that checks a specific staff permission."""

    async def guard(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        """Admin/superadmin pass; staff must have the named permission."""
        if current_user.role in ("admin", "superadmin"):
            return current_user
        if current_user.role != "staff":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        await db.refresh(current_user, ["staff_profile"])
        staff_profile = current_user.staff_profile
        if not staff_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff profile not found",
            )
        await db.refresh(staff_profile, ["permissions"])
        perms = [p.permission for p in staff_profile.permissions]
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return current_user

    return guard


async def require_approved_publisher(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Publisher must have KYC approved to access publisher-gated endpoints."""
    if current_user.role != "publisher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Publisher account required",
        )
    await db.refresh(current_user, ["publisher_profile"])
    profile = current_user.publisher_profile
    if not profile or profile.kyc_status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="KYC must be approved before accessing this resource",
        )
    return current_user


class PaginationParams:
    """Reusable pagination query parameter dependency."""

    def __init__(self, page: int = 1, limit: int = 20) -> None:
        """Clamp page and limit to safe ranges."""
        self.page = min(max(page, 1), 1000)
        self.limit = min(max(limit, 1), 100)
        self.offset = (self.page - 1) * self.limit
