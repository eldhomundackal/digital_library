"""Admin KYC management router — /admin/kyc endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.common import SuccessResponse
from app.schemas.kyc import KYCRejectDocumentRequest, KYCRequestResubmissionRequest
from app.services.kyc_service import KYCService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/admin/kyc", tags=["Admin — KYC"])

_STAFF_ROLES = ("staff", "admin", "superadmin")


@router.get("")
async def list_kyc_applications(
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """List all KYC applications with optional status filter."""
    from sqlalchemy import select, func
    from app.db.models.kyc import KYCApplication
    from app.db.models.publisher import PublisherProfile
    from app.db.models.user import User

    query = (
        select(KYCApplication)
        .join(PublisherProfile, PublisherProfile.id == KYCApplication.publisher_id)
    )
    if status:
        query = query.where(KYCApplication.overall_status == status)
    count_q = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_q)
    total = count_result.scalar() or 0

    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    applications = result.scalars().all()

    items = []
    for app in applications:
        items.append(
            {
                "kyc_id": app.uuid,
                "overall_status": app.overall_status,
                "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            }
        )
    return SuccessResponse(data={"items": items, "total": total, "page": page, "limit": limit})


@router.get("/{kyc_id}")
async def get_kyc_detail(
    kyc_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Return full KYC application detail."""
    storage = get_storage_provider()
    from sqlalchemy import select
    from app.db.models.kyc import KYCApplication
    from fastapi import HTTPException

    result = await db.execute(
        select(KYCApplication).where(KYCApplication.uuid == kyc_id)
    )
    kyc = result.scalar_one_or_none()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC application not found.")
    await db.refresh(kyc, ["documents"])
    docs = [
        {
            "document_type": doc.document_type,
            "status": doc.status,
            "file_url": doc.file_url,
            "rejection_reason": doc.rejection_reason,
        }
        for doc in kyc.documents
    ]
    return SuccessResponse(
        data={
            "kyc_id": kyc.uuid,
            "overall_status": kyc.overall_status,
            "submitted_at": kyc.submitted_at.isoformat() if kyc.submitted_at else None,
            "documents": docs,
        }
    )


@router.post("/{kyc_id}/approve")
async def approve_kyc(
    kyc_id: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Approve an entire KYC application."""
    storage = get_storage_provider()
    service = KYCService(db, storage)
    await service.approve_kyc(kyc_id, current_user)
    return SuccessResponse(data={"message": "KYC application approved."})


@router.post("/{kyc_id}/reject")
async def reject_kyc(
    kyc_id: str,
    payload: KYCRejectDocumentRequest,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Reject an entire KYC application with a reason."""
    storage = get_storage_provider()
    service = KYCService(db, storage)
    await service.reject_kyc(kyc_id, payload.reason, current_user)
    return SuccessResponse(data={"message": "KYC application rejected."})


@router.patch("/{kyc_id}/documents/{document_type}/approve")
async def approve_document(
    kyc_id: str,
    document_type: str,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Approve a single KYC document."""
    storage = get_storage_provider()
    service = KYCService(db, storage)
    await service.approve_document(kyc_id, document_type, current_user)
    return SuccessResponse(data={"message": "Document approved."})


@router.patch("/{kyc_id}/documents/{document_type}/reject")
async def reject_document(
    kyc_id: str,
    document_type: str,
    payload: KYCRejectDocumentRequest,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Reject a single KYC document with a reason."""
    storage = get_storage_provider()
    service = KYCService(db, storage)
    await service.reject_document(kyc_id, document_type, payload.reason, current_user)
    return SuccessResponse(data={"message": "Document rejected."})


@router.post("/{kyc_id}/request-resubmission")
async def request_resubmission(
    kyc_id: str,
    payload: KYCRequestResubmissionRequest,
    current_user=Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Request resubmission of specific flagged documents."""
    storage = get_storage_provider()
    service = KYCService(db, storage)
    await service.request_resubmission(kyc_id, payload, current_user)
    return SuccessResponse(data={"message": "Resubmission requested."})
