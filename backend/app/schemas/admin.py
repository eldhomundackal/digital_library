"""Schemas for admin dashboard, audit logs, and activity feed."""

from pydantic import BaseModel

from app.schemas.auth import UserSummary


class PlatformOverview(BaseModel):
    """High-level platform statistics."""

    total_readers: int
    total_publishers: int
    total_books: int
    total_downloads: int
    new_registrations_today: int
    new_books_today: int


class PendingActions(BaseModel):
    """Count of items awaiting admin action."""

    kyc_applications: int
    book_approvals: int
    tag_approvals: int
    reported_reviews: int


class RecentActivity(BaseModel):
    """Latest items for each category."""

    latest_books: list[dict]
    latest_publishers: list[dict]
    latest_reported_reviews: list[dict]


class DashboardResponse(BaseModel):
    """Admin dashboard response."""

    platform_overview: PlatformOverview
    pending_actions: PendingActions
    recent_activity: RecentActivity


class AuditTarget(BaseModel):
    """Target of an audit log entry."""

    type: str
    id: str
    label: str


class AuditLogResponse(BaseModel):
    """Single audit log entry."""

    audit_id: str
    action: str
    performed_by: UserSummary
    target: AuditTarget
    metadata: dict | None
    note: str | None
    ip_address: str | None
    performed_at: str


class ActivityActor(BaseModel):
    """Actor in an activity feed entry."""

    type: str
    id: str
    name: str


class ActivityFeedResponse(BaseModel):
    """Single activity feed entry."""

    activity_id: str
    type: str
    category: str
    title: str
    message: str
    action_url: str | None
    actor: ActivityActor
    is_read: bool
    created_at: str


class AdminUserListItem(BaseModel):
    """Row in the admin user list."""

    user_id: str
    email: str
    role: str
    is_active: bool
    created_at: str
    profile_summary: dict
