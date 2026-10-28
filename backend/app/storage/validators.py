"""File type and size validators for uploaded files."""

from fastapi import HTTPException, UploadFile

from app.core.config import settings

ALLOWED_MIME_TYPES: dict[str, set[str]] = {
    "book_pdf": {"application/pdf"},
    "thumbnail": {"image/jpeg", "image/png", "image/webp"},
    "kyc_doc": {"application/pdf"},
    "avatar": {"image/jpeg", "image/png", "image/webp"},
}


def _max_sizes_bytes() -> dict[str, int]:
    """Build max size mapping from settings — read at call time, not module import."""
    return {
        "book_pdf": settings.MAX_BOOK_PDF_SIZE_MB * 1024 * 1024,
        "thumbnail": settings.MAX_THUMBNAIL_SIZE_MB * 1024 * 1024,
        "kyc_doc": settings.MAX_KYC_DOCUMENT_SIZE_MB * 1024 * 1024,
        "avatar": settings.MAX_THUMBNAIL_SIZE_MB * 1024 * 1024,
    }


def validate_file(file: UploadFile, file_type: str) -> None:
    """
    Raises HTTPException 400 on wrong MIME type or size exceeding limit.
    """
    allowed = ALLOWED_MIME_TYPES.get(file_type, set())
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail={"file": [f"Only {allowed} accepted for {file_type}"]},
        )
    max_bytes = _max_sizes_bytes().get(file_type, 0)
    size = file.size or 0
    if max_bytes and size > max_bytes:
        mb_limit = max_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail={"file": [f"File must not exceed {mb_limit}MB"]},
        )
