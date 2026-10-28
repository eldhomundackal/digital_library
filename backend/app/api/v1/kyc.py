"""KYC verification router — /kyc endpoints (publisher only)."""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.common import SuccessResponse
from app.schemas.kyc import KYCSubmitRequest
from app.services.kyc_service import KYCService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/kyc", tags=["KYC"])


@router.get("")
async def get_kyc_dashboard(
    current_user=Depends(require_roles("publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Return current publisher's KYC dashboard."""
    storage = get_storage_provider()
    service = KYCService(db, storage)
    result = await service.get_my_kyc(current_user)
    return SuccessResponse(data=result)


@router.post("/documents/{document_type}")
async def upload_document(
    document_type: str,
    file: UploadFile = File(...),
    current_user=Depends(require_roles("publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Upload a KYC document (PDF only)."""
    storage = get_storage_provider()
    service = KYCService(db, storage)
    result = await service.upload_document(document_type, file, current_user)
    return SuccessResponse(data=result)


@router.delete("/documents/{document_type}")
async def remove_document(
    document_type: str,
    current_user=Depends(require_roles("publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Remove an uploaded KYC document (INCOMPLETE status only)."""
    storage = get_storage_provider()
    service = KYCService(db, storage)
    await service.remove_document(document_type, current_user)
    return SuccessResponse(data={"message": "Document removed."})


@router.post("/submit")
async def submit_kyc(
    payload: KYCSubmitRequest,
    current_user=Depends(require_roles("publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Submit KYC application for review."""
    storage = get_storage_provider()
    service = KYCService(db, storage)
    await service.submit_kyc(payload.terms_accepted, current_user)
    return SuccessResponse(data={"message": "KYC application submitted for review."})


@router.post("/resubmit")
async def resubmit_documents(
    government_id: UploadFile | None = File(default=None),
    publishing_license: UploadFile | None = File(default=None),
    business_registration: UploadFile | None = File(default=None),
    current_user=Depends(require_roles("publisher")),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Resubmit rejected KYC documents."""
    storage = get_storage_provider()
    service = KYCService(db, storage)
    files = {}
    if government_id:
        files["government_id"] = government_id
    if publishing_license:
        files["publishing_license"] = publishing_license
    if business_registration:
        files["business_registration"] = business_registration
    await service.resubmit_documents(files, current_user)
    return SuccessResponse(data={"message": "Documents resubmitted for review."})
