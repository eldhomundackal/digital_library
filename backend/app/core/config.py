from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App
    APP_NAME: str = "Digital Library API"
    APP_ENV: str = "development"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/digital_library"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    AUTH_PROVIDER: str = "local"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5

    # OIDC / OAuth2
    OIDC_ISSUER_URL: str = ""
    OIDC_CLIENT_ID: str = ""
    OIDC_CLIENT_SECRET: str = ""
    OIDC_SCOPES: str = "openid email profile"
    OAUTH2_AUTHORIZATION_URL: str = ""
    OAUTH2_TOKEN_URL: str = ""
    OAUTH2_USERINFO_URL: str = ""

    # Storage
    STORAGE_PROVIDER: str = "local"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "digital-library"

    # File limits (MB)
    MAX_BOOK_PDF_SIZE_MB: int = 50
    MAX_THUMBNAIL_SIZE_MB: int = 2
    MAX_KYC_DOCUMENT_SIZE_MB: int = 10

    # Download limits
    MAX_DOWNLOADS_PER_DAY: int = 5
    MAX_DOWNLOADS_PER_MONTH: int = 15
    DOWNLOAD_URL_EXPIRY_SECONDS: int = 600

    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@library.com"

    # Superadmin seed
    SUPERADMIN_EMAIL: str = "superadmin@example.com"
    SUPERADMIN_PASSWORD: str = "SuperAdmin123!"
    SUPERADMIN_FIRST_NAME: str = "Super"
    SUPERADMIN_LAST_NAME: str = "Admin"

    class Config:
        """Pydantic settings config."""

        env_file = ".env"
        case_sensitive = True


settings = Settings()
