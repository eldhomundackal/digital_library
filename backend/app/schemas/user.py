"""Schemas for user profiles, staff creation, and avatar responses."""

from pydantic import BaseModel

from app.schemas.utils import (
    CitySummary,
    CountrySummary,
    LanguageSummary,
)


class ReaderProfileDetail(BaseModel):
    """Nested profile detail for readers."""

    first_name: str
    last_name: str
    avatar: str | None
    bio: str | None
    date_of_birth: str | None
    gender: str | None
    country: CountrySummary | None
    city: CitySummary | None
    preferred_language: LanguageSummary | None
    preferred_categories: list[dict]
    preferred_tags: list[dict]
    occupation: str | None


class ReaderProfileResponse(BaseModel):
    """Full reader profile response for GET /users/me."""

    user_id: str
    email: str
    role: str = "reader"
    is_email_verified: bool
    is_active: bool
    profile_completion: int
    created_at: str
    profile: ReaderProfileDetail


class UpdateReaderProfileRequest(BaseModel):
    """PATCH body for reader profile — all fields optional."""

    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    country_id: int | None = None
    city_id: int | None = None
    language_id: int | None = None
    preferred_category_ids: list[int] | None = None
    preferred_tag_ids: list[int] | None = None
    occupation: str | None = None


class SocialLinks(BaseModel):
    """Publisher social media links."""

    twitter: str | None = None
    linkedin: str | None = None
    facebook: str | None = None
    instagram: str | None = None


class PublisherProfileDetail(BaseModel):
    """Nested profile detail for publishers."""

    display_name: str
    bio: str | None
    logo: str | None
    website: str | None
    social_links: SocialLinks
    total_books: int
    joined_date: str
    is_verified: bool


class PublisherProfileResponse(BaseModel):
    """Full publisher profile response for GET /users/me."""

    user_id: str
    email: str
    role: str = "publisher"
    is_email_verified: bool
    is_active: bool
    kyc_status: str
    created_at: str
    profile: PublisherProfileDetail


class UpdatePublisherProfileRequest(BaseModel):
    """PATCH body for publisher profile — all fields optional."""

    display_name: str | None = None
    bio: str | None = None
    website: str | None = None
    social_links: SocialLinks | None = None


class StaffProfileDetail(BaseModel):
    """Nested profile detail for staff."""

    first_name: str
    last_name: str
    permissions: list[str]


class StaffProfileResponse(BaseModel):
    """Full staff profile response for GET /users/me."""

    user_id: str
    email: str
    role: str
    is_active: bool
    created_at: str
    profile: StaffProfileDetail


class CreateStaffRequest(BaseModel):
    """Body for POST /admin/users/create-staff."""

    email: str
    first_name: str
    last_name: str
    permissions: list[str]


class UpdatePasswordRequest(BaseModel):
    """Body for PATCH /users/me/password."""

    current_password: str
    new_password: str
    confirm_password: str


class NotificationPreferencesRequest(BaseModel):
    """Body for PATCH /users/me/notifications/preferences."""

    reply_notifications: bool


class AvatarResponse(BaseModel):
    """Response for PATCH /users/me/avatar."""

    avatar_url: str
