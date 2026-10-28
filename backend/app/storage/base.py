"""Abstract base class for all storage providers."""

from abc import ABC, abstractmethod

from fastapi import UploadFile


class BaseStorageProvider(ABC):
    """Storage abstraction — swap S3 for local by changing STORAGE_PROVIDER env var."""

    @abstractmethod
    async def upload(self, file: UploadFile, path: str) -> str:
        """Upload file to storage. Returns the URL or path stored in DB."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete file from storage. Silently ignores missing files."""

    @abstractmethod
    async def generate_presigned_url(self, path: str, expires_seconds: int) -> str:
        """Generate a time-limited download URL for a private file."""

    @abstractmethod
    async def get_public_url(self, path: str) -> str:
        """Return permanent public URL for a public file (thumbnails, avatars)."""
