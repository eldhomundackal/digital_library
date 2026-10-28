"""AWS S3 storage provider."""

import asyncio
from functools import partial

import boto3
from fastapi import UploadFile

from app.core.config import settings
from app.storage.base import BaseStorageProvider


class S3StorageProvider(BaseStorageProvider):
    """Upload files to S3 and generate pre-signed URLs for private files."""

    def __init__(self) -> None:
        """Initialise boto3 S3 client from settings."""
        self._client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket = settings.S3_BUCKET_NAME

    def _upload_sync(self, content: bytes, path: str, content_type: str) -> None:
        """Sync S3 put_object — run in thread pool."""
        self._client.put_object(
            Bucket=self.bucket,
            Key=path,
            Body=content,
            ContentType=content_type,
        )

    def _delete_sync(self, path: str) -> None:
        """Sync S3 delete_object — run in thread pool."""
        self._client.delete_object(Bucket=self.bucket, Key=path)

    def _presign_sync(self, path: str, expires_seconds: int) -> str:
        """Sync presigned URL generation — run in thread pool."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": path},
            ExpiresIn=expires_seconds,
        )

    async def upload(self, file: UploadFile, path: str) -> str:
        """Upload file to S3 in thread pool. Returns the S3 HTTPS URL."""
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, partial(self._upload_sync, content, path, content_type)
        )
        return f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{path}"

    async def delete(self, path: str) -> None:
        """Delete S3 object in thread pool. Silently ignores missing files."""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, partial(self._delete_sync, path))
        except Exception:
            pass

    async def generate_presigned_url(self, path: str, expires_seconds: int) -> str:
        """Generate pre-signed S3 URL in thread pool."""
        loop = asyncio.get_event_loop()
        url: str = await loop.run_in_executor(
            None, partial(self._presign_sync, path, expires_seconds)
        )
        return url

    async def get_public_url(self, path: str) -> str:
        """Return direct S3 URL for public objects (thumbnails, avatars)."""
        return f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{path}"
