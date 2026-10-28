"""OIDC auth provider — generic, works with Keycloak, Okta, Cognito."""

import secrets

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt as jose_jwt

from app.auth.base import BaseAuthProvider
from app.core.config import settings

_JWKS_CACHE_KEY = "oidc:jwks"


class OIDCAuthProvider(BaseAuthProvider):
    """Generic OIDC provider configured via environment variables."""

    def __init__(self) -> None:
        """Initialise with OIDC settings from environment."""
        self.issuer_url = settings.OIDC_ISSUER_URL
        self.client_id = settings.OIDC_CLIENT_ID
        self.client_secret = settings.OIDC_CLIENT_SECRET
        self.scopes = settings.OIDC_SCOPES
        self._jwks: dict | None = None

    async def _get_jwks(self) -> dict:
        """Fetch and cache JWKS from the issuer's well-known endpoint."""
        if self._jwks is not None:
            return self._jwks
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.issuer_url}/.well-known/jwks.json", timeout=10
            )
            resp.raise_for_status()
        self._jwks = resp.json()
        return self._jwks

    async def get_authorization_url(self) -> str:
        """Build authorization URL with PKCE code challenge."""
        state = secrets.token_urlsafe(32)
        scope = " ".join(self.scopes) if isinstance(self.scopes, list) else self.scopes
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": getattr(settings, "OIDC_REDIRECT_URI", ""),
            "scope": scope,
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.issuer_url}/authorize?{query}"

    async def handle_callback(self, code: str, state: str) -> dict:
        """Exchange authorization code for tokens at the OIDC token endpoint."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.issuer_url}/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": getattr(settings, "OIDC_REDIRECT_URI", ""),
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=10,
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code.",
            )
        return resp.json()

    async def validate_token(self, token: str) -> dict:
        """Verify JWT signature using JWKS from the OIDC issuer."""
        jwks = await self._get_jwks()
        try:
            payload = jose_jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self.client_id,
            )
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OIDC token.",
            ) from exc
        return payload

    async def get_user_info(self, token: str) -> dict:
        """Fetch user info from the OIDC userinfo endpoint."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.issuer_url}/userinfo",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch OIDC user info.",
            )
        data = resp.json()
        return {
            "sub": data.get("sub"),
            "email": data.get("email"),
            "first_name": data.get("given_name", ""),
            "last_name": data.get("family_name", ""),
            "email_verified": data.get("email_verified", False),
        }

    async def refresh_token(self, token: str) -> dict:
        """Refresh access token via the OIDC token endpoint."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.issuer_url}/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=10,
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh OIDC token.",
            )
        return resp.json()

    async def logout(self, token: str) -> None:
        """Call the OIDC end_session_endpoint."""
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.issuer_url}/logout",
                data={
                    "token": token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=10,
            )
