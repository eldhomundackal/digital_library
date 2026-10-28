"""Integration test stubs for Admin Panel API.

These tests verify the admin HTTP layer (router → service).
Full integration tests require a running PostgreSQL + Redis instance.
Mark with pytest.mark.integration to skip in unit-only CI runs.
"""

import pytest


@pytest.mark.integration
class TestAdminDashboardAPI:
    """Admin dashboard endpoint."""

    def test_admin_can_view_dashboard(self) -> None:
        """GET /admin/dashboard returns DashboardResponse with all sections."""
        pytest.skip("Requires running DB + admin token")

    def test_staff_can_view_dashboard(self) -> None:
        """GET /admin/dashboard returns 200 for staff role."""
        pytest.skip("Requires running DB + staff token")

    def test_anonymous_cannot_view_dashboard(self) -> None:
        """GET /admin/dashboard returns 401 for unauthenticated request."""
        pytest.skip("Requires running app")

    def test_dashboard_pending_counts_are_accurate(self) -> None:
        """DashboardResponse.pending_actions counts match actual DB state."""
        pytest.skip("Requires running DB with known fixture state")


@pytest.mark.integration
class TestAdminAuditLogAPI:
    """Admin audit log endpoint."""

    def test_admin_can_view_audit_log(self) -> None:
        """GET /admin/audit-log returns paginated AuditLogResponse items."""
        pytest.skip("Requires running DB + admin token")

    def test_staff_cannot_view_audit_log(self) -> None:
        """GET /admin/audit-log returns 403 for staff role."""
        pytest.skip("Requires running DB + staff token")

    def test_audit_log_filterable_by_action(self) -> None:
        """GET /admin/audit-log?action=KYC_APPROVED returns only matching entries."""
        pytest.skip("Requires running DB")

    def test_audit_log_filterable_by_date_range(self) -> None:
        """GET /admin/audit-log?from=...&to=... returns entries in range."""
        pytest.skip("Requires running DB")


@pytest.mark.integration
class TestAdminActivityFeedAPI:
    """Admin activity feed endpoints."""

    def test_staff_can_view_activity_feed(self) -> None:
        """GET /admin/activity-feed returns ActivityFeedResponse items."""
        pytest.skip("Requires running DB + staff token")

    def test_activity_feed_filterable_by_category(self) -> None:
        """GET /admin/activity-feed?category=actionable filters correctly."""
        pytest.skip("Requires running DB")

    def test_staff_can_mark_activity_read(self) -> None:
        """PATCH /admin/activity-feed/{id}/read sets is_read=True."""
        pytest.skip("Requires running DB")

    def test_staff_can_mark_all_activity_read(self) -> None:
        """POST /admin/activity-feed/read-all marks all unread entries."""
        pytest.skip("Requires running DB")


@pytest.mark.integration
class TestAdminNotificationsAPI:
    """Admin notifications endpoints."""

    def test_admin_can_view_notifications(self) -> None:
        """GET /admin/notifications returns notification list."""
        pytest.skip("Requires running DB + admin token")

    def test_admin_can_mark_all_notifications_read(self) -> None:
        """POST /admin/notifications/read-all marks all as read."""
        pytest.skip("Requires running DB")

    def test_admin_can_mark_single_notification_read(self) -> None:
        """PATCH /admin/notifications/{id}/read sets is_read=True."""
        pytest.skip("Requires running DB")


@pytest.mark.integration
class TestOIDCOAuth2AuthFlow:
    """OIDC and OAuth2 external auth provider flows."""

    def test_get_oidc_authorization_url_returns_redirect(self) -> None:
        """GET /auth/external-login?provider=oidc returns authorization URL."""
        pytest.skip("Requires OIDC_ISSUER_URL configured")

    def test_oidc_callback_creates_or_links_user(self) -> None:
        """POST /auth/callback/oidc creates user if not exists, returns tokens."""
        pytest.skip("Requires OIDC provider running")

    def test_oauth2_authorization_url_returns_redirect(self) -> None:
        """GET /auth/external-login?provider=oauth2 returns authorization URL."""
        pytest.skip("Requires OAUTH2_AUTHORIZATION_URL configured")

    def test_unconfigured_oidc_returns_501(self) -> None:
        """GET /auth/external-login?provider=oidc returns 501 when not configured."""
        pytest.skip("Requires running app with OIDC_ISSUER_URL empty")


@pytest.mark.integration
class TestFullSystemIntegration:
    """End-to-end flow tests covering the full user journey."""

    def test_full_reader_journey(self) -> None:
        """Register → verify email → login → browse books → download → review."""
        pytest.skip("Requires full stack: DB + Redis + storage")

    def test_full_publisher_journey(self) -> None:
        """Register → verify → KYC upload → KYC approval → upload book → approval."""
        pytest.skip("Requires full stack + admin to approve KYC and book")

    def test_superadmin_can_manage_everything(self) -> None:
        """Superadmin can access all admin endpoints without permission restrictions."""
        pytest.skip("Requires running DB + superadmin token")
