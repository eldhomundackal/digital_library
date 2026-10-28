"""Integration test stubs for KYC API flow.

These tests verify the KYC HTTP layer (router → service).
Full integration tests require a running PostgreSQL + Redis instance.
Mark with pytest.mark.integration to skip in unit-only CI runs.
"""

import pytest


@pytest.mark.integration
class TestKYCFlow:
    """KYC lifecycle: upload → submit → approve/reject."""

    def test_publisher_can_get_kyc_dashboard(self) -> None:
        """GET /kyc returns 200 with dashboard for authenticated publisher."""
        pytest.skip("Requires running DB + auth token fixture")

    def test_publisher_can_upload_document(self) -> None:
        """POST /kyc/documents/government_id returns KYCDocumentDetail."""
        pytest.skip("Requires running DB + S3/local storage")

    def test_publisher_cannot_upload_invalid_doc_type(self) -> None:
        """POST /kyc/documents/invalid_type returns 400."""
        pytest.skip("Requires running DB")

    def test_publisher_can_remove_uploaded_document(self) -> None:
        """DELETE /kyc/documents/government_id returns 200 when INCOMPLETE."""
        pytest.skip("Requires running DB")

    def test_publisher_cannot_remove_document_when_pending(self) -> None:
        """DELETE /kyc/documents/... returns 400 when KYC is PENDING."""
        pytest.skip("Requires running DB")

    def test_publisher_can_submit_kyc_with_all_docs(self) -> None:
        """POST /kyc/submit sets status=PENDING when all 3 docs uploaded."""
        pytest.skip("Requires running DB")

    def test_publisher_cannot_submit_with_missing_docs(self) -> None:
        """POST /kyc/submit returns 400 if any doc not UPLOADED."""
        pytest.skip("Requires running DB")

    def test_admin_can_approve_kyc(self) -> None:
        """POST /admin/kyc/{id}/approve sets publisher is_verified=True."""
        pytest.skip("Requires running DB + admin token fixture")

    def test_admin_can_reject_kyc(self) -> None:
        """POST /admin/kyc/{id}/reject sets overall_status=REJECTED."""
        pytest.skip("Requires running DB + admin token fixture")

    def test_admin_can_request_resubmission(self) -> None:
        """POST /admin/kyc/{id}/request-resubmission flags docs as REJECTED."""
        pytest.skip("Requires running DB + admin token fixture")

    def test_publisher_can_resubmit_rejected_docs(self) -> None:
        """POST /kyc/resubmit sets overall_status=RESUBMITTED."""
        pytest.skip("Requires running DB")

    def test_non_publisher_cannot_access_kyc(self) -> None:
        """GET /kyc returns 403 for reader/staff roles."""
        pytest.skip("Requires running DB")
