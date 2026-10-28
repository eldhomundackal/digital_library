from abc import ABC, abstractmethod


class BaseAuthProvider(ABC):
    """Abstract base for all auth providers (local, OIDC, OAuth2)."""

    @abstractmethod
    async def get_authorization_url(self) -> str:
        """Return the IDP authorization URL for redirect-based flows."""

    @abstractmethod
    async def handle_callback(self, code: str, state: str) -> dict:
        """Exchange an auth code for tokens. Returns TokenSchema dict."""

    @abstractmethod
    async def validate_token(self, token: str) -> dict:
        """Decode and validate an access token. Returns TokenPayloadSchema dict."""

    @abstractmethod
    async def refresh_token(self, token: str) -> dict:
        """Issue a new access token from a refresh token."""

    @abstractmethod
    async def logout(self, token: str) -> None:
        """Invalidate the given token."""

    @abstractmethod
    async def get_user_info(self, token: str) -> dict:
        """Return normalized user info from the token or userinfo endpoint."""

    # --- Optional methods for local provider only ---

    async def register(self, payload: object) -> dict:
        """Hash password and return user info. Local provider only."""
        raise NotImplementedError("register() is only for LocalAuthProvider")

    async def send_otp(self, email: str, otp_type: str) -> None:
        """Generate and store OTP. Local provider only."""
        raise NotImplementedError("send_otp() is only for LocalAuthProvider")

    async def reset_password(self, token: str, password: str) -> None:
        """Apply a new password via reset session token. Local provider only."""
        raise NotImplementedError("reset_password() is only for LocalAuthProvider")
