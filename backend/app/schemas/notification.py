"""Schemas for in-app notifications."""

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Single notification in list response."""

    notification_id: str
    type: str
    title: str
    message: str
    is_read: bool
    is_grouped: bool
    group_count: int
    data: dict | None
    created_at: str
    updated_at: str


class NotificationListResponse(BaseModel):
    """Paginated notification list with unread count."""

    unread_count: int
    items: list[NotificationResponse]
    total: int
    page: int
    limit: int
    pages: int


class NotificationPreferencesResponse(BaseModel):
    """Response for GET/PATCH notification preferences."""

    reply_notifications: bool
