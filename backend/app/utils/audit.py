from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import ActivityFeed, AuditLog
from app.db.models.user import User

ACTIVITY_FEED_ACTIONS: dict[str, dict[str, str]] = {
    "KYC_NEW_APPLICATION": {
        "category": "actionable",
        "title": "New KYC Application",
    },
    "BOOK_SUBMITTED": {
        "category": "actionable",
        "title": "New Book Pending Review",
    },
    "BOOK_RESUBMITTED": {
        "category": "actionable",
        "title": "Book Resubmitted",
    },
    "BOOK_APPROVED": {
        "category": "informational",
        "title": "Book Approved",
    },
    "BOOK_REJECTED": {
        "category": "informational",
        "title": "Book Rejected",
    },
    "KYC_APPROVED": {
        "category": "informational",
        "title": "KYC Approved",
    },
    "KYC_REJECTED": {
        "category": "informational",
        "title": "KYC Rejected",
    },
    "COMMENT_REPORTED": {
        "category": "actionable",
        "title": "Review Reported",
    },
    "NEW_PUBLISHER_REG": {
        "category": "actionable",
        "title": "New Publisher Registered",
    },
}


async def audit_action(
    db: AsyncSession,
    action: str,
    performed_by: User,
    target_type: str,
    target_id: int,
    target_label: str,
    request: Request | None = None,
    metadata: dict | None = None,
    note: str | None = None,
) -> None:
    """
    Creates an AuditLog row and optionally an ActivityFeed entry.
    Called at the end of every admin/staff mutating service method.
    """
    ip_address: str | None = None
    if request is not None:
        ip_address = getattr(request.state, "ip_address", None)

    audit_log = AuditLog(
        action=action,
        performed_by_id=performed_by.id,
        target_type=target_type,
        target_id=target_id,
        target_label=target_label,
        metadata_=metadata,
        note=note,
        ip_address=ip_address,
    )
    db.add(audit_log)

    if action in ACTIVITY_FEED_ACTIONS:
        feed_meta = ACTIVITY_FEED_ACTIONS[action]
        activity = ActivityFeed(
            type=action,
            category=feed_meta["category"],
            title=feed_meta["title"],
            message=f"{action} by {performed_by.email}",
            actor_type=performed_by.role,
            actor_id=performed_by.id,
            actor_name=performed_by.email,
        )
        db.add(activity)

    await db.commit()
