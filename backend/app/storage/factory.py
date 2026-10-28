"""Storage provider factory."""

from app.core.config import settings
from app.storage.base import BaseStorageProvider


def get_storage_provider() -> BaseStorageProvider:
    """Return the correct storage provider based on STORAGE_PROVIDER setting."""
    match settings.STORAGE_PROVIDER:
        case "s3":
            from app.storage.s3 import S3StorageProvider

            return S3StorageProvider()
        case "local":
            from app.storage.local import LocalStorageProvider

            return LocalStorageProvider()
        case _:
            raise ValueError(f"Unknown storage provider: {settings.STORAGE_PROVIDER}")
