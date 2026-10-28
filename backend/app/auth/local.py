from fastapi import HTTPException, status

from app.auth.base import BaseAuthProvider
from app.auth.jwt import create_access_token, decode_token
from app.auth.password import hash_password, verify_password
from app.core.config import settings


class LocalAuthProvider(BaseAuthProvider):
    """Handles all auth when AUTH_PROVIDER=local."""

    async def register(self, payload: object) -> dict:
        """Hash password and return normalized user info."""
        hashed = hash_password(payload.password)  # type: ignore[attr-defined]
        return {
            "hashed_password": hashed,
            "auth_provider": "local",
            "idp_sub": None,
            "is_email_verified": False,
        }

    async def validate_token(self, token: str) -> dict:
        """Decode and verify a local JWT. Raises 401 on failure."""
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return payload

    async def refresh_token(self, token: str) -> dict:
        """Decode the refresh token and issue a new access token."""
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return payload

    async def logout(self, token: str) -> None:
        """Blacklisting is handled in AuthService using the Redis client."""

    async def get_user_info(self, token: str) -> dict:
        """Return the payload from a decoded access token."""
        return decode_token(token)

    async def get_authorization_url(self) -> str:
        """Local provider has no external authorization URL."""
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="External login is not available for the local auth provider.",
        )

    async def handle_callback(self, code: str, state: str) -> dict:
        """Not implemented for local provider."""
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="External login callback is not available for the local auth provider.",
        )
