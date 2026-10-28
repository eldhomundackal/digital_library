"""Local filesystem storage provider — development only."""

import os
from pathlib import Path

from fastapi import UploadFile

from app.storage.base import BaseStorageProvider

BASE_PATH = Path("/tmp/digital-library")
BASE_URL = "http://localhost:8000/static"


class LocalStorageProvider(BaseStorageProvider):
    """Stores files under /tmp/digital-library/ and serves via static files mount."""

    async def upload(self, file: UploadFile, path: str) -> str:
        """Write file bytes to local disk and return its static URL."""
        dest = BASE_PATH / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = await file.read()
        dest.write_bytes(content)
        return f"{BASE_URL}/{path}"

    async def delete(self, path: str) -> None:
        """Remove file from disk; silently ignores missing files."""
        target = BASE_PATH / path
        try:
            target.unlink()
        except FileNotFoundError:
            pass

    async def generate_presigned_url(self, path: str, expires_seconds: int) -> str:
        """Return static URL — no expiry in local dev."""
        return f"{BASE_URL}/{path}"

    async def get_public_url(self, path: str) -> str:
        """Return permanent static URL."""
        return f"{BASE_URL}/{path}"
