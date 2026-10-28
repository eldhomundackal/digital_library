"""User profile router — /users/me endpoints."""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_current_user, get_db
from app.schemas.common import SuccessResponse
from app.schemas.user import (
    AvatarResponse,
    NotificationPreferencesRequest,
    UpdatePasswordRequest,
    UpdatePublisherProfileRequest,
    UpdateReaderProfileRequest,
)
from app.services.user_service import UserService
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_my_profile(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Return current user's profile."""
    storage = get_storage_provider()
    service = UserService(db, storage)
    profile = await service.get_my_profile(current_user)
    return SuccessResponse(data=profile)


@router.patch("/me")
async def update_my_profile(
    payload: UpdateReaderProfileRequest | UpdatePublisherProfileRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Update current user's profile."""
    storage = get_storage_provider()
    service = UserService(db, storage)
    updated = await service.update_my_profile(current_user, payload)
    return SuccessResponse(data=updated)


@router.delete("/me")
async def deactivate_my_account(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Soft-delete current user's account."""
    storage = get_storage_provider()
    service = UserService(db, storage)
    await service.deactivate_my_account(current_user)
    return SuccessResponse(data={"message": "Account deactivated."})


@router.patch("/me/avatar")
async def update_avatar(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Upload a new avatar."""
    storage = get_storage_provider()
    service = UserService(db, storage)
    result = await service.update_avatar(current_user, file)
    return SuccessResponse(data=result)


@router.patch("/me/password")
async def change_password(
    payload: UpdatePasswordRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Change password (local auth only)."""
    storage = get_storage_provider()
    service = UserService(db, storage)
    await service.change_password(current_user, payload)
    return SuccessResponse(data={"message": "Password changed successfully."})


@router.get("/me/notifications")
async def get_notifications(
    current_user=Depends(get_current_user),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get current user's notifications."""
    from app.services.notification_service import NotificationService

    service = NotificationService(db)
    result = await service.get_my_notifications(current_user, params)
    return SuccessResponse(data=result)


@router.patch("/me/notifications/preferences")
async def update_notification_prefs(
    payload: NotificationPreferencesRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Update notification preferences."""
    from app.services.notification_service import NotificationService

    service = NotificationService(db)
    result = await service.update_preferences(current_user, payload)
    return SuccessResponse(data=result)


@router.post("/me/notifications/read-all")
async def mark_all_notifications_read(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Mark all notifications as read."""
    from app.services.notification_service import NotificationService

    service = NotificationService(db)
    await service.mark_all_read(current_user)
    return SuccessResponse(data={"message": "All notifications marked as read."})


@router.patch("/me/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Mark a single notification as read."""
    from app.services.notification_service import NotificationService

    service = NotificationService(db)
    await service.mark_read(notification_id, current_user)
    return SuccessResponse(data={"message": "Notification marked as read."})


@router.delete("/me/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Delete a notification."""
    from app.services.notification_service import NotificationService

    service = NotificationService(db)
    await service.delete_notification(notification_id, current_user)
    return SuccessResponse(data={"message": "Notification deleted."})


@router.get("/me/downloads")
async def get_download_history(
    current_user=Depends(get_current_user),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Get current user's download history."""
    from app.services.download_service import DownloadService

    service = DownloadService(db, None)
    result = await service.get_my_history(current_user, params)
    return SuccessResponse(data=result)


@router.delete("/me/downloads/{book_id}")
async def delete_download_history(
    book_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Soft-delete a download history entry."""
    from app.services.download_service import DownloadService

    service = DownloadService(db, None)
    await service.soft_delete_history(book_id, current_user)
    return SuccessResponse(data={"message": "Download history entry removed."})
