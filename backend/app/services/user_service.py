"""User profile service — profile CRUD, avatar upload, password change, staff creation."""

import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password, verify_password
from app.db.models.publisher import PublisherProfile, StaffPermission, StaffProfile
from app.db.models.user import ReaderProfile, User
from app.schemas.user import (
    AvatarResponse,
    CreateStaffRequest,
    NotificationPreferencesRequest,
    ReaderProfileDetail,
    ReaderProfileResponse,
    PublisherProfileDetail,
    PublisherProfileResponse,
    SocialLinks,
    StaffProfileDetail,
    StaffProfileResponse,
    UpdatePasswordRequest,
    UpdatePublisherProfileRequest,
    UpdateReaderProfileRequest,
)
from app.schemas.utils import CountrySummary, CitySummary, LanguageSummary
from app.storage.base import BaseStorageProvider
from app.storage.validators import validate_file
from app.utils.audit import audit_action
from app.utils.number_generator import generate


class UserService:
    """Handles all user profile operations."""

    def __init__(self, db: AsyncSession, storage: BaseStorageProvider) -> None:
        """Initialise with injected DB session and storage provider."""
        self.db = db
        self.storage = storage

    async def get_my_profile(
        self, user: User
    ) -> ReaderProfileResponse | PublisherProfileResponse | StaffProfileResponse:
        """Load profile based on user role and return typed response."""
        created_at = user.created_at.isoformat() if user.created_at else ""

        if user.role == "reader":
            await self.db.refresh(user, ["reader_profile"])
            profile = user.reader_profile
            if not profile:
                raise HTTPException(status_code=404, detail="Reader profile not found.")

            country_data = None
            city_data = None
            lang_data = None

            if profile.country_id:
                await self.db.refresh(profile, ["country"])
                if profile.country:
                    country_data = CountrySummary(
                        country_id=profile.country.uuid,
                        name=profile.country.name,
                        iso_code=profile.country.iso_code,
                    )
            if profile.city_id:
                await self.db.refresh(profile, ["city"])
                if profile.city:
                    city_data = CitySummary(
                        city_id=profile.city.uuid,
                        name=profile.city.name,
                        state=profile.city.state,
                    )
            if profile.language_id:
                await self.db.refresh(profile, ["preferred_language"])
                if profile.preferred_language:
                    lang_data = LanguageSummary(
                        language_id=profile.preferred_language.uuid,
                        name=profile.preferred_language.name,
                        iso_code=profile.preferred_language.iso_code,
                    )

            return ReaderProfileResponse(
                user_id=user.uuid,
                email=user.email,
                is_email_verified=user.is_email_verified,
                is_active=user.is_active,
                profile_completion=profile.profile_completion,
                created_at=created_at,
                profile=ReaderProfileDetail(
                    first_name=profile.first_name,
                    last_name=profile.last_name,
                    avatar=profile.avatar,
                    bio=profile.bio,
                    date_of_birth=profile.date_of_birth,
                    gender=profile.gender,
                    country=country_data,
                    city=city_data,
                    preferred_language=lang_data,
                    preferred_categories=[],
                    preferred_tags=[],
                    occupation=profile.occupation,
                ),
            )

        if user.role == "publisher":
            await self.db.refresh(user, ["publisher_profile"])
            pub = user.publisher_profile
            if not pub:
                raise HTTPException(status_code=404, detail="Publisher profile not found.")
            return PublisherProfileResponse(
                user_id=user.uuid,
                email=user.email,
                is_email_verified=user.is_email_verified,
                is_active=user.is_active,
                kyc_status=pub.kyc_status,
                created_at=created_at,
                profile=PublisherProfileDetail(
                    display_name=pub.display_name,
                    bio=pub.bio,
                    logo=pub.logo,
                    website=pub.website,
                    social_links=SocialLinks(
                        twitter=pub.twitter,
                        linkedin=pub.linkedin,
                        facebook=pub.facebook,
                        instagram=pub.instagram,
                    ),
                    total_books=0,
                    joined_date=created_at,
                    is_verified=pub.is_verified,
                ),
            )

        # staff / admin / superadmin
        await self.db.refresh(user, ["staff_profile"])
        staff = user.staff_profile
        perms: list[str] = []
        if staff:
            await self.db.refresh(staff, ["permissions"])
            perms = [p.permission for p in staff.permissions]
        return StaffProfileResponse(
            user_id=user.uuid,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=created_at,
            profile=StaffProfileDetail(
                first_name=staff.first_name if staff else "",
                last_name=staff.last_name if staff else "",
                permissions=perms,
            ),
        )

    async def update_my_profile(
        self,
        user: User,
        payload: UpdateReaderProfileRequest | UpdatePublisherProfileRequest,
    ) -> ReaderProfileResponse | PublisherProfileResponse:
        """Apply PATCH semantics to the correct profile model."""
        if user.role == "reader":
            await self.db.refresh(user, ["reader_profile"])
            profile = user.reader_profile
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found.")
            assert isinstance(payload, UpdateReaderProfileRequest)
            for field in (
                "first_name",
                "last_name",
                "bio",
                "date_of_birth",
                "gender",
                "country_id",
                "city_id",
                "language_id",
                "occupation",
            ):
                value = getattr(payload, field, None)
                if value is not None:
                    setattr(profile, field, value)

            if payload.preferred_category_ids is not None:
                from app.db.models.user import ReaderPreferredCategory

                await self.db.execute(
                    __import__("sqlalchemy", fromlist=["delete"]).delete(
                        ReaderPreferredCategory
                    ).where(ReaderPreferredCategory.reader_id == profile.id)
                )
                for cat_id in payload.preferred_category_ids:
                    self.db.add(
                        ReaderPreferredCategory(reader_id=profile.id, category_id=cat_id)
                    )

            if payload.preferred_tag_ids is not None:
                from app.db.models.user import ReaderPreferredTag

                await self.db.execute(
                    __import__("sqlalchemy", fromlist=["delete"]).delete(
                        ReaderPreferredTag
                    ).where(ReaderPreferredTag.reader_id == profile.id)
                )
                for tag_id in payload.preferred_tag_ids:
                    self.db.add(
                        ReaderPreferredTag(reader_id=profile.id, tag_id=tag_id)
                    )

            profile.profile_completion = self._calculate_profile_completion(profile)
            await self.db.commit()

        elif user.role == "publisher":
            await self.db.refresh(user, ["publisher_profile"])
            pub = user.publisher_profile
            if not pub:
                raise HTTPException(status_code=404, detail="Profile not found.")
            assert isinstance(payload, UpdatePublisherProfileRequest)
            if payload.display_name is not None:
                pub.display_name = payload.display_name
            if payload.bio is not None:
                pub.bio = payload.bio
            if payload.website is not None:
                pub.website = payload.website
            if payload.social_links is not None:
                sl = payload.social_links
                if sl.twitter is not None:
                    pub.twitter = sl.twitter
                if sl.linkedin is not None:
                    pub.linkedin = sl.linkedin
                if sl.facebook is not None:
                    pub.facebook = sl.facebook
                if sl.instagram is not None:
                    pub.instagram = sl.instagram
            await self.db.commit()

        return await self.get_my_profile(user)

    async def update_avatar(self, user: User, file: UploadFile) -> AvatarResponse:
        """Validate, upload, and save new avatar URL."""
        validate_file(file, "avatar")
        ext = (file.filename or "jpg").rsplit(".", 1)[-1]
        path = f"avatars/{user.uuid}.{ext}"

        if user.role == "reader":
            await self.db.refresh(user, ["reader_profile"])
            profile = user.reader_profile
            if profile and profile.avatar:
                old_key = profile.avatar.split("/static/", 1)[-1]
                await self.storage.delete(old_key)
        elif user.role == "publisher":
            await self.db.refresh(user, ["publisher_profile"])
            pub = user.publisher_profile
            if pub and pub.logo:
                old_key = pub.logo.split("/static/", 1)[-1]
                await self.storage.delete(old_key)

        url = await self.storage.upload(file, path)

        if user.role == "reader" and user.reader_profile:
            user.reader_profile.avatar = url
        elif user.role == "publisher" and user.publisher_profile:
            user.publisher_profile.logo = url

        await self.db.commit()
        return AvatarResponse(avatar_url=url)

    async def change_password(
        self, user: User, payload: UpdatePasswordRequest
    ) -> None:
        """Change password for local auth users only."""
        if user.auth_provider != "local":
            raise HTTPException(
                status_code=400,
                detail="Password change is only available for local accounts.",
            )
        if not user.hashed_password or not verify_password(
            payload.current_password, user.hashed_password
        ):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")
        if payload.new_password != payload.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match.")
        user.hashed_password = hash_password(payload.new_password)
        await self.db.commit()

    async def deactivate_my_account(self, user: User) -> None:
        """Soft delete: mark user inactive."""
        user.is_active = False
        user.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def create_staff(
        self, payload: CreateStaffRequest, created_by: User
    ) -> StaffProfileResponse:
        """Create a staff user account with given permissions."""
        if created_by.role not in ("admin", "superadmin"):
            raise HTTPException(
                status_code=403, detail="Only admin or superadmin can create staff."
            )
        result = await self.db.execute(
            select(User).where(User.email == payload.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="An account with this email already exists."
            )

        import redis.asyncio as aioredis
        from app.core.config import settings as _settings

        redis_client = await aioredis.from_url(
            _settings.REDIS_URL, decode_responses=True
        )
        user_number = await generate("user", redis_client)
        await redis_client.aclose()

        temp_password = secrets.token_urlsafe(12)
        new_user = User(
            number=user_number,
            email=payload.email,
            hashed_password=hash_password(temp_password),
            role="staff",
            auth_provider="local",
            is_email_verified=True,
        )
        self.db.add(new_user)
        await self.db.flush()

        staff_profile = StaffProfile(
            user_id=new_user.id,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        self.db.add(staff_profile)
        await self.db.flush()

        for perm in payload.permissions:
            self.db.add(
                StaffPermission(
                    staff_id=staff_profile.id,
                    permission=perm,
                    granted_by_id=created_by.id,
                )
            )
        await self.db.commit()

        from app.tasks.email_tasks import send_staff_welcome_email

        send_staff_welcome_email.delay(payload.email, temp_password)
        await audit_action(
            self.db,
            "STAFF_CREATED",
            created_by,
            "user",
            new_user.id,
            new_user.email,
        )

        return StaffProfileResponse(
            user_id=new_user.uuid,
            email=new_user.email,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at.isoformat() if new_user.created_at else "",
            profile=StaffProfileDetail(
                first_name=payload.first_name,
                last_name=payload.last_name,
                permissions=payload.permissions,
            ),
        )

    async def create_admin(
        self, payload: CreateStaffRequest, created_by: User
    ) -> StaffProfileResponse:
        """Create an admin user. Only superadmin can do this."""
        if created_by.role != "superadmin":
            raise HTTPException(
                status_code=403, detail="Only superadmin can create admin accounts."
            )

        result = await self.db.execute(
            select(User).where(User.email == payload.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="An account with this email already exists."
            )

        import redis.asyncio as aioredis
        from app.core.config import settings as _settings

        redis_client = await aioredis.from_url(
            _settings.REDIS_URL, decode_responses=True
        )
        user_number = await generate("user", redis_client)
        await redis_client.aclose()

        temp_password = secrets.token_urlsafe(12)
        new_user = User(
            number=user_number,
            email=payload.email,
            hashed_password=hash_password(temp_password),
            role="admin",
            auth_provider="local",
            is_email_verified=True,
        )
        self.db.add(new_user)
        await self.db.flush()

        staff_profile = StaffProfile(
            user_id=new_user.id,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        self.db.add(staff_profile)
        await self.db.commit()

        from app.tasks.email_tasks import send_staff_welcome_email

        send_staff_welcome_email.delay(payload.email, temp_password)
        await audit_action(
            self.db,
            "ADMIN_CREATED",
            created_by,
            "user",
            new_user.id,
            new_user.email,
        )

        return StaffProfileResponse(
            user_id=new_user.uuid,
            email=new_user.email,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at.isoformat() if new_user.created_at else "",
            profile=StaffProfileDetail(
                first_name=payload.first_name,
                last_name=payload.last_name,
                permissions=[],
            ),
        )

    def _calculate_profile_completion(self, profile: ReaderProfile) -> int:
        """
        Tier 1 (always done): 40%
        Tier 2 (bio + dob + gender + occupation): 75%
        Tier 3 (country + city + language + categories + tags): 100%
        """
        tier2_fields = [profile.bio, profile.date_of_birth, profile.gender, profile.occupation]
        tier3_fields = [profile.country_id, profile.city_id, profile.language_id]

        if all(tier2_fields) and all(tier3_fields):
            return 100
        if all(tier2_fields):
            return 75
        return 40
