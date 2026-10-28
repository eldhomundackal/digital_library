"""Pure OAuth2 auth provider (no OIDC identity layer)."""

import secrets

import httpx
from fastapi import HTTPException, status

from app.auth.base import BaseAuthProvider
from app.core.config import settings


class OAuth2AuthProvider(BaseAuthProvider):
    """Pure OAuth 2.0 provider — falls back to userinfo endpoint for user details."""

    async def get_authorization_url(self) -> str:
        """Build authorization URL from OAUTH2_AUTHORIZATION_URL settings."""
        if not settings.OAUTH2_AUTHORIZATION_URL:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OAUTH2_AUTHORIZATION_URL is not configured.",
            )
        state = secrets.token_urlsafe(32)
        client_id = getattr(settings, "OAUTH2_CLIENT_ID", "")
        redirect_uri = getattr(settings, "OAUTH2_REDIRECT_URI", "")
        params = (
            f"response_type=code"
            f"&client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
        )
        return f"{settings.OAUTH2_AUTHORIZATION_URL}?{params}"

    async def handle_callback(self, code: str, state: str) -> dict:
        """Exchange authorization code at OAUTH2_TOKEN_URL."""
        if not settings.OAUTH2_TOKEN_URL:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OAUTH2_TOKEN_URL is not configured.",
            )
        client_id = getattr(settings, "OAUTH2_CLIENT_ID", "")
        client_secret = getattr(settings, "OAUTH2_CLIENT_SECRET", "")
        redirect_uri = getattr(settings, "OAUTH2_REDIRECT_URI", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.OAUTH2_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                timeout=10,
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange OAuth2 authorization code.",
            )
        return resp.json()

    async def validate_token(self, token: str) -> dict:
        """Validate JWT or call token introspection endpoint."""
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OAuth2 token introspection not configured.",
        )

    async def get_user_info(self, token: str) -> dict:
        """GET OAUTH2_USERINFO_URL with Bearer token."""
        if not settings.OAUTH2_USERINFO_URL:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OAUTH2_USERINFO_URL is not configured.",
            )
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                settings.OAUTH2_USERINFO_URL,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch OAuth2 user info.",
            )
        data = resp.json()
        return {
            "sub": data.get("sub") or data.get("id"),
            "email": data.get("email"),
            "first_name": data.get("given_name") or data.get("name", "").split()[0],
            "last_name": data.get("family_name") or "",
            "email_verified": data.get("email_verified", False),
        }

    async def refresh_token(self, token: str) -> dict:
        """Refresh token via OAuth2 token endpoint."""
        if not settings.OAUTH2_TOKEN_URL:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OAUTH2_TOKEN_URL is not configured.",
            )
        client_id = getattr(settings, "OAUTH2_CLIENT_ID", "")
        client_secret = getattr(settings, "OAUTH2_CLIENT_SECRET", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.OAUTH2_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                timeout=10,
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh OAuth2 token.",
            )
        return resp.json()

    async def logout(self, token: str) -> None:
        """OAuth2 logout is provider-specific — silently succeeds if not configured."""
        return
