"""KYC verification service — document upload, submission, review workflow."""

from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.kyc import KYCActionLog, KYCApplication, KYCDocument
from app.db.models.publisher import PublisherProfile
from app.db.models.user import User
from app.schemas.kyc import (
    KYCDashboardResponse,
    KYCDocumentDetail,
    KYCRequestResubmissionRequest,
)
from app.storage.base import BaseStorageProvider
from app.storage.validators import validate_file
from app.utils.audit import audit_action
from app.utils.number_generator import generate

ALLOWED_DOC_TYPES = {"government_id", "publishing_license", "business_registration"}
REQUIRED_DOC_TYPES = {"government_id", "publishing_license", "business_registration"}


class KYCService:
    """Handles KYC document upload, submission and admin review."""

    def __init__(self, db: AsyncSession, storage: BaseStorageProvider) -> None:
        """Initialise with DB session and storage provider."""
        self.db = db
        self.storage = storage

    async def _get_publisher(self, user: User) -> PublisherProfile:
        """Return publisher profile or 404."""
        result = await self.db.execute(
            select(PublisherProfile).where(PublisherProfile.user_id == user.id)
        )
        pub = result.scalar_one_or_none()
        if not pub:
            raise HTTPException(status_code=404, detail="Publisher profile not found.")
        return pub

    async def _get_kyc_application(self, user: User) -> KYCApplication:
        """Load or create a KYC application for publisher."""
        pub = await self._get_publisher(user)
        result = await self.db.execute(
            select(KYCApplication).where(KYCApplication.publisher_id == pub.id)
        )
        kyc = result.scalar_one_or_none()
        if not kyc:
            import redis.asyncio as aioredis
            from app.core.config import settings as _settings

            redis_client = await aioredis.from_url(
                _settings.REDIS_URL, decode_responses=True
            )
            kyc_number = await generate("kyc", redis_client)
            await redis_client.aclose()

            kyc = KYCApplication(
                number=kyc_number,
                publisher_id=pub.id,
                overall_status="INCOMPLETE",
            )
            self.db.add(kyc)
            await self.db.flush()
        return kyc

    async def get_my_kyc(self, user: User) -> KYCDashboardResponse:
        """Return publisher's KYC dashboard."""
        kyc = await self._get_kyc_application(user)
        await self.db.refresh(kyc, ["documents"])
        docs_map = {doc.document_type: doc for doc in kyc.documents}

        doc_labels: dict[str, str] = {
            "government_id": "Government ID",
            "publishing_license": "Publishing License",
            "business_registration": "Business Registration",
        }
        documents_dict: dict[str, KYCDocumentDetail] = {}
        resubmission_required = []
        for doc_type in ALLOWED_DOC_TYPES:
            doc = docs_map.get(doc_type)
            if doc:
                documents_dict[doc_type] = KYCDocumentDetail(
                    document_id=doc.uuid,
                    type=doc.document_type,
                    label=doc_labels.get(doc.document_type, doc.document_type),
                    status=doc.status,
                    file_url=doc.file_url,
                    file_name=doc.file_name,
                    file_size_mb=doc.file_size_mb,
                    rejection_reason=doc.rejection_reason,
                    uploaded_at=doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    reviewed_at=doc.reviewed_at.isoformat() if doc.reviewed_at else None,
                )
                if doc.status == "REJECTED":
                    resubmission_required.append(doc_type)
            else:
                documents_dict[doc_type] = KYCDocumentDetail(
                    document_id=None,
                    type=doc_type,
                    label=doc_labels.get(doc_type, doc_type),
                    status="NOT_UPLOADED",
                    file_url=None,
                    file_name=None,
                    file_size_mb=None,
                    rejection_reason=None,
                    uploaded_at=None,
                    reviewed_at=None,
                )

        uploaded_types = {
            dt
            for dt, doc in docs_map.items()
            if doc.status == "UPLOADED"
        }
        can_submit = (
            REQUIRED_DOC_TYPES.issubset(uploaded_types)
            and not kyc.terms_accepted
            and kyc.overall_status not in ("PENDING", "APPROVED")
        )

        await self.db.commit()

        return KYCDashboardResponse(
            kyc_id=kyc.uuid,
            overall_status=kyc.overall_status,
            can_submit=can_submit,
            resubmission_required=resubmission_required,
            submitted_at=kyc.submitted_at.isoformat() if kyc.submitted_at else None,
            reviewed_at=kyc.reviewed_at.isoformat() if kyc.reviewed_at else None,
            terms_accepted=kyc.terms_accepted,
            terms_accepted_at=kyc.terms_accepted_at.isoformat()
            if kyc.terms_accepted_at
            else None,
            documents=documents_dict,
        )

    async def upload_document(
        self, doc_type: str, file: UploadFile, user: User
    ) -> KYCDocumentDetail:
        """Upload a single KYC document PDF."""
        if doc_type not in ALLOWED_DOC_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document type. Allowed: {list(ALLOWED_DOC_TYPES)}",
            )
        validate_file(file, "kyc_doc")

        kyc = await self._get_kyc_application(user)
        if kyc.overall_status in ("PENDING", "APPROVED"):
            raise HTTPException(
                status_code=400,
                detail="Cannot upload documents when KYC is PENDING or APPROVED.",
            )

        pub = await self._get_publisher(user)
        result = await self.db.execute(
            select(KYCDocument).where(
                KYCDocument.kyc_application_id == kyc.id,
                KYCDocument.document_type == doc_type,
            )
        )
        existing_doc = result.scalar_one_or_none()
        if existing_doc and existing_doc.file_url:
            await self.storage.delete(existing_doc.file_url)

        path = f"kyc/{pub.uuid}/{doc_type}.pdf"
        url = await self.storage.upload(file, path)
        size_mb = round((file.size or 0) / (1024 * 1024), 4) if file.size else 0.0

        now = datetime.now(timezone.utc)
        if existing_doc:
            existing_doc.file_url = url
            existing_doc.file_name = file.filename
            existing_doc.file_size_mb = size_mb
            existing_doc.status = "UPLOADED"
            existing_doc.uploaded_at = now
            existing_doc.rejection_reason = None
            doc = existing_doc
        else:
            doc = KYCDocument(
                kyc_application_id=kyc.id,
                document_type=doc_type,
                status="UPLOADED",
                file_url=url,
                file_name=file.filename,
                file_size_mb=size_mb,
                uploaded_at=now,
            )
            self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        doc_labels: dict[str, str] = {
            "government_id": "Government ID",
            "publishing_license": "Publishing License",
            "business_registration": "Business Registration",
        }
        return KYCDocumentDetail(
            document_id=doc.uuid,
            type=doc.document_type,
            label=doc_labels.get(doc.document_type, doc.document_type),
            status=doc.status,
            file_url=doc.file_url,
            file_name=doc.file_name,
            file_size_mb=doc.file_size_mb,
            rejection_reason=doc.rejection_reason,
            uploaded_at=doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            reviewed_at=doc.reviewed_at.isoformat() if doc.reviewed_at else None,
        )

    async def remove_document(self, doc_type: str, user: User) -> None:
        """Remove an uploaded KYC document (only while INCOMPLETE)."""
        kyc = await self._get_kyc_application(user)
        if kyc.overall_status != "INCOMPLETE":
            raise HTTPException(
                status_code=400,
                detail="Documents can only be removed when KYC status is INCOMPLETE.",
            )
        result = await self.db.execute(
            select(KYCDocument).where(
                KYCDocument.kyc_application_id == kyc.id,
                KYCDocument.document_type == doc_type,
            )
        )
        doc = result.scalar_one_or_none()
        if doc and doc.file_url:
            await self.storage.delete(doc.file_url)
            doc.file_url = None
            doc.file_name = None
            doc.file_size_mb = None
            doc.status = "NOT_UPLOADED"
            doc.uploaded_at = None
            await self.db.commit()

    async def submit_kyc(self, terms_accepted: bool, user: User) -> None:
        """Submit KYC application for review."""
        if not terms_accepted:
            raise HTTPException(
                status_code=400, detail="You must accept the terms to submit KYC."
            )
        kyc = await self._get_kyc_application(user)
        if kyc.overall_status in ("PENDING", "APPROVED"):
            raise HTTPException(
                status_code=400,
                detail="KYC is already PENDING or APPROVED.",
            )

        await self.db.refresh(kyc, ["documents"])
        docs_map = {doc.document_type: doc for doc in kyc.documents}
        for doc_type in REQUIRED_DOC_TYPES:
            doc = docs_map.get(doc_type)
            if not doc or doc.status != "UPLOADED":
                raise HTTPException(
                    status_code=400,
                    detail=f"Document '{doc_type}' must be uploaded before submission.",
                )

        now = datetime.now(timezone.utc)
        for doc in kyc.documents:
            doc.status = "PENDING"
        kyc.overall_status = "PENDING"
        kyc.submitted_at = now
        kyc.terms_accepted = True
        kyc.terms_accepted_at = now

        log = KYCActionLog(
            kyc_application_id=kyc.id,
            action="SUBMITTED",
            performed_by_id=user.id,
            performed_by_type=user.role,
        )
        self.db.add(log)
        await self.db.commit()

        from app.tasks.email_tasks import send_kyc_status_email
        from app.tasks.notification_tasks import create_in_app_notification

        send_kyc_status_email.delay(str(user.uuid), "submitted")
        create_in_app_notification.delay(str(user.uuid), "KYC_SUBMITTED")

    async def resubmit_documents(
        self, files: dict[str, UploadFile], user: User
    ) -> None:
        """Resubmit rejected KYC documents."""
        kyc = await self._get_kyc_application(user)
        await self.db.refresh(kyc, ["documents"])
        rejected_types = {
            doc.document_type for doc in kyc.documents if doc.status == "REJECTED"
        }

        for doc_type in files:
            if doc_type not in rejected_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Document '{doc_type}' is not flagged for resubmission.",
                )
            validate_file(files[doc_type], "kyc_doc")

        pub = await self._get_publisher(user)
        for doc_type, file in files.items():
            path = f"kyc/{pub.uuid}/{doc_type}.pdf"
            url = await self.storage.upload(file, path)
            size_mb = round((file.size or 0) / (1024 * 1024), 4) if file.size else 0.0
            result = await self.db.execute(
                select(KYCDocument).where(
                    KYCDocument.kyc_application_id == kyc.id,
                    KYCDocument.document_type == doc_type,
                )
            )
            doc = result.scalar_one()
            doc.file_url = url
            doc.file_name = file.filename
            doc.file_size_mb = size_mb
            doc.status = "PENDING"
            doc.rejection_reason = None
            doc.uploaded_at = datetime.now(timezone.utc)

        kyc.overall_status = "RESUBMITTED"
        log = KYCActionLog(
            kyc_application_id=kyc.id,
            action="RESUBMITTED",
            performed_by_id=user.id,
            performed_by_type=user.role,
        )
        self.db.add(log)
        await self.db.commit()

        from app.tasks.notification_tasks import create_in_app_notification

        create_in_app_notification.delay(str(user.uuid), "KYC_RESUBMITTED")

    async def approve_kyc(self, kyc_id: str, admin: User) -> None:
        """Approve a KYC application."""
        result = await self.db.execute(
            select(KYCApplication).where(KYCApplication.uuid == kyc_id)
        )
        kyc = result.scalar_one_or_none()
        if not kyc:
            raise HTTPException(status_code=404, detail="KYC application not found.")

        await self.db.refresh(kyc, ["documents", "publisher"])
        for doc in kyc.documents:
            doc.status = "APPROVED"
        kyc.overall_status = "APPROVED"
        kyc.reviewed_at = datetime.now(timezone.utc)
        kyc.reviewed_by_id = admin.id

        pub = kyc.publisher
        pub.is_verified = True
        pub.kyc_status = "APPROVED"

        log = KYCActionLog(
            kyc_application_id=kyc.id,
            action="APPROVED",
            performed_by_id=admin.id,
            performed_by_type=admin.role,
        )
        self.db.add(log)
        await self.db.commit()

        from app.tasks.email_tasks import send_kyc_status_email
        from app.tasks.notification_tasks import create_in_app_notification

        publisher_user_result = await self.db.execute(
            select(User).where(User.id == pub.user_id)
        )
        publisher_user = publisher_user_result.scalar_one()
        send_kyc_status_email.delay(str(publisher_user.uuid), "approved")
        create_in_app_notification.delay(str(publisher_user.uuid), "KYC_APPROVED")
        await audit_action(self.db, "KYC_APPROVED", admin, "kyc_application", kyc.id, kyc_id)

    async def reject_kyc(self, kyc_id: str, reason: str, admin: User) -> None:
        """Reject a KYC application with a reason."""
        result = await self.db.execute(
            select(KYCApplication).where(KYCApplication.uuid == kyc_id)
        )
        kyc = result.scalar_one_or_none()
        if not kyc:
            raise HTTPException(status_code=404, detail="KYC application not found.")

        kyc.overall_status = "REJECTED"
        kyc.rejection_reason = reason
        kyc.reviewed_at = datetime.now(timezone.utc)
        kyc.reviewed_by_id = admin.id

        await self.db.refresh(kyc, ["publisher"])
        kyc.publisher.kyc_status = "REJECTED"

        log = KYCActionLog(
            kyc_application_id=kyc.id,
            action="REJECTED",
            performed_by_id=admin.id,
            performed_by_type=admin.role,
            note=reason,
        )
        self.db.add(log)
        await self.db.commit()

        from app.tasks.email_tasks import send_kyc_status_email

        publisher_user_result = await self.db.execute(
            select(User).where(User.id == kyc.publisher.user_id)
        )
        publisher_user = publisher_user_result.scalar_one()
        send_kyc_status_email.delay(str(publisher_user.uuid), "rejected")
        await audit_action(
            self.db,
            "KYC_REJECTED",
            admin,
            "kyc_application",
            kyc.id,
            kyc_id,
            {"reason": reason},
        )

    async def approve_document(
        self, kyc_id: str, doc_type: str, admin: User
    ) -> None:
        """Approve a single KYC document."""
        result = await self.db.execute(
            select(KYCApplication).where(KYCApplication.uuid == kyc_id)
        )
        kyc = result.scalar_one_or_none()
        if not kyc:
            raise HTTPException(status_code=404, detail="KYC application not found.")

        doc_result = await self.db.execute(
            select(KYCDocument).where(
                KYCDocument.kyc_application_id == kyc.id,
                KYCDocument.document_type == doc_type,
            )
        )
        doc = doc_result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")

        doc.status = "APPROVED"
        doc.reviewed_by_id = admin.id
        doc.reviewed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await audit_action(
            self.db, "KYC_DOCUMENT_APPROVED", admin, "kyc_document", doc.id, doc_type
        )

    async def reject_document(
        self, kyc_id: str, doc_type: str, reason: str, admin: User
    ) -> None:
        """Reject a single KYC document with a reason."""
        result = await self.db.execute(
            select(KYCApplication).where(KYCApplication.uuid == kyc_id)
        )
        kyc = result.scalar_one_or_none()
        if not kyc:
            raise HTTPException(status_code=404, detail="KYC application not found.")

        doc_result = await self.db.execute(
            select(KYCDocument).where(
                KYCDocument.kyc_application_id == kyc.id,
                KYCDocument.document_type == doc_type,
            )
        )
        doc = doc_result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")

        doc.status = "REJECTED"
        doc.rejection_reason = reason
        doc.reviewed_by_id = admin.id
        doc.reviewed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await audit_action(
            self.db, "KYC_DOCUMENT_REJECTED", admin, "kyc_document", doc.id, doc_type
        )

    async def request_resubmission(
        self, kyc_id: str, payload: KYCRequestResubmissionRequest, admin: User
    ) -> None:
        """Flag specific documents for resubmission and notify publisher."""
        result = await self.db.execute(
            select(KYCApplication).where(KYCApplication.uuid == kyc_id)
        )
        kyc = result.scalar_one_or_none()
        if not kyc:
            raise HTTPException(status_code=404, detail="KYC application not found.")

        for rejection in payload.documents:
            doc_result = await self.db.execute(
                select(KYCDocument).where(
                    KYCDocument.kyc_application_id == kyc.id,
                    KYCDocument.document_type == rejection.type,
                )
            )
            doc = doc_result.scalar_one_or_none()
            if doc:
                doc.status = "REJECTED"
                doc.rejection_reason = rejection.reason

        kyc.overall_status = "REJECTED"
        kyc.reviewed_at = datetime.now(timezone.utc)
        kyc.reviewed_by_id = admin.id

        await self.db.refresh(kyc, ["publisher"])
        kyc.publisher.kyc_status = "REJECTED"

        log = KYCActionLog(
            kyc_application_id=kyc.id,
            action="RESUBMISSION_REQUESTED",
            performed_by_id=admin.id,
            performed_by_type=admin.role,
            metadata_={
                "rejections": [
                    {"document_type": r.type, "reason": r.reason}
                    for r in payload.documents
                ]
            },
        )
        self.db.add(log)
        await self.db.commit()

        from app.tasks.email_tasks import send_kyc_status_email

        publisher_user_result = await self.db.execute(
            select(User).where(User.id == kyc.publisher.user_id)
        )
        publisher_user = publisher_user_result.scalar_one()
        send_kyc_status_email.delay(str(publisher_user.uuid), "resubmission_requested")
        await audit_action(
            self.db,
            "KYC_RESUBMISSION_REQUESTED",
            admin,
            "kyc_application",
            kyc.id,
            kyc_id,
        )
