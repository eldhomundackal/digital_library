"""Publisher public profile service."""

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import BookStatus
from app.db.models.book import Book, BookVersion
from app.db.models.publisher import PublisherProfile
from app.db.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.user import PublisherProfileDetail, PublisherProfileResponse, SocialLinks
from app.utils.pagination import compute_pages


class PublisherService:
    """Public-facing publisher profile and book listing."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialise with DB session."""
        self.db = db

    async def get_public_profile(self, publisher_uuid: str) -> PublisherProfileResponse:
        """Return verified publisher's public profile or 404."""
        result = await self.db.execute(
            select(PublisherProfile)
            .join(User, User.id == PublisherProfile.user_id)
            .where(
                User.uuid == publisher_uuid,
                User.is_active.is_(True),
                PublisherProfile.is_verified.is_(True),
            )
        )
        pub = result.scalar_one_or_none()
        if not pub:
            raise HTTPException(status_code=404, detail="Publisher not found.")

        user_result = await self.db.execute(
            select(User).where(User.id == pub.user_id)
        )
        user = user_result.scalar_one()

        count_result = await self.db.execute(
            select(func.count(BookVersion.id))
            .join(Book, Book.id == BookVersion.book_id)
            .where(
                Book.publisher_id == pub.id,
                BookVersion.status == BookStatus.APPROVED,
                BookVersion.is_current.is_(True),
            )
        )
        total_books = count_result.scalar() or 0
        created_at = user.created_at.isoformat() if user.created_at else ""

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
                total_books=total_books,
                joined_date=created_at,
                is_verified=pub.is_verified,
            ),
        )

    async def get_public_books(
        self, publisher_uuid: str, page: int, limit: int
    ) -> PaginatedResponse:
        """Return paginated approved books for a verified publisher."""
        result = await self.db.execute(
            select(PublisherProfile)
            .join(User, User.id == PublisherProfile.user_id)
            .where(
                User.uuid == publisher_uuid,
                PublisherProfile.is_verified.is_(True),
            )
        )
        pub = result.scalar_one_or_none()
        if not pub:
            raise HTTPException(status_code=404, detail="Publisher not found.")

        offset = (page - 1) * limit
        count_result = await self.db.execute(
            select(func.count(BookVersion.id))
            .join(Book, Book.id == BookVersion.book_id)
            .where(
                Book.publisher_id == pub.id,
                BookVersion.status == BookStatus.APPROVED,
                BookVersion.is_current.is_(True),
                Book.is_active.is_(True),
            )
        )
        total = count_result.scalar() or 0

        books_result = await self.db.execute(
            select(BookVersion)
            .join(Book, Book.id == BookVersion.book_id)
            .where(
                Book.publisher_id == pub.id,
                BookVersion.status == BookStatus.APPROVED,
                BookVersion.is_current.is_(True),
                Book.is_active.is_(True),
            )
            .offset(offset)
            .limit(limit)
        )
        versions = books_result.scalars().all()

        items = []
        for version in versions:
            book_q = await self.db.execute(
                select(Book).where(Book.id == version.book_id)
            )
            book = book_q.scalar_one()
            items.append(
                {
                    "book_id": str(book.uuid),
                    "title": version.title,
                    "subtitle": version.subtitle,
                    "thumbnail": version.thumbnail,
                    "status": version.status,
                    "version_number": version.version_number,
                    "published_at": version.approved_at.isoformat()
                    if version.approved_at
                    else None,
                }
            )

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=compute_pages(total, limit),
        )
