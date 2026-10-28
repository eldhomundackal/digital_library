"""Schemas for KYC application, documents, and admin review."""

from pydantic import BaseModel

from app.schemas.utils import PublisherSummary


class KYCDocumentDetail(BaseModel):
    """Single KYC document detail in the dashboard."""

    document_id: str | None
    type: str
    label: str
    status: str
    file_url: str | None
    file_name: str | None
    file_size_mb: float | None = None
    uploaded_at: str | None
    reviewed_at: str | None = None
    rejection_reason: str | None


class KYCDashboardResponse(BaseModel):
    """Publisher's KYC status dashboard."""

    kyc_id: str
    overall_status: str
    submitted_at: str | None
    reviewed_at: str | None
    terms_accepted: bool
    terms_accepted_at: str | None
    documents: dict[str, KYCDocumentDetail]
    can_submit: bool
    resubmission_required: list[str]


class KYCSubmitRequest(BaseModel):
    """Body for POST /kyc/submit."""

    terms_accepted: bool


class KYCRejectDocumentRequest(BaseModel):
    """Body for PATCH /admin/kyc/{id}/documents/{type}/reject."""

    reason: str


class DocumentRejection(BaseModel):
    """Single document rejection in a resubmission request."""

    type: str
    reason: str


class KYCRequestResubmissionRequest(BaseModel):
    """Body for POST /admin/kyc/{id}/request-resubmission."""

    documents: list[DocumentRejection]
    note: str | None = None


class DocumentsSummary(BaseModel):
    """Document counts for KYC list view."""

    total: int
    approved: int
    pending: int
    rejected: int


class KYCListItem(BaseModel):
    """Row in the admin KYC list."""

    kyc_id: str
    publisher: PublisherSummary
    overall_status: str
    submitted_at: str
    documents_summary: DocumentsSummary
