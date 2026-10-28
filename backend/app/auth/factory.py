from app.auth.base import BaseAuthProvider
from app.core.config import settings


def get_auth_provider() -> BaseAuthProvider:
    """Return the configured auth provider based on AUTH_PROVIDER env var."""
    match settings.AUTH_PROVIDER:
        case "oidc":
            from app.auth.oidc import OIDCAuthProvider

            return OIDCAuthProvider()
        case "oauth2":
            from app.auth.oauth2 import OAuth2AuthProvider

            return OAuth2AuthProvider()
        case _:
            from app.auth.local import LocalAuthProvider

            return LocalAuthProvider()
