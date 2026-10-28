"""Author service — create, list, merge, and manage authors."""

from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.author import Author
from app.db.models.book import BookAuthor
from app.db.models.publisher import PublisherProfile
from app.db.models.user import User
from app.schemas.book import AuthorDetail, CreateAuthorRequest, MergeAuthorsRequest
from app.schemas.common import PaginatedResponse
from app.storage.base import BaseStorageProvider
from app.storage.validators import validate_file
from app.utils.audit import audit_action
from app.utils.pagination import compute_pages
from app.utils.slug import slugify


class AuthorService:
    """Handles author CRUD and merging."""

    def __init__(self, db: AsyncSession, storage: BaseStorageProvider) -> None:
        """Initialise with DB session and storage provider."""
        self.db = db
        self.storage = storage

    async def _build_author_detail(self, author: Author) -> AuthorDetail:
        """Build AuthorDetail from an Author ORM object."""
        count_result = await self.db.execute(
            select(func.count(BookAuthor.id)).where(BookAuthor.author_id == author.id)
        )
        total_books = count_result.scalar() or 0
        return AuthorDetail(
            author_id=str(author.uuid),
            first_name=author.first_name,
            last_name=author.last_name,
            bio=author.bio,
            avatar=author.avatar,
            total_books=total_books,
        )

    async def create_author(
        self,
        payload: CreateAuthorRequest,
        avatar: UploadFile | None,
        user: User,
    ) -> AuthorDetail:
        """Create a new author, checking for slug duplicates first."""
        full_name_slug = slugify(f"{payload.first_name} {payload.last_name}")
        existing = await self.db.execute(
            select(Author).where(
                Author.is_active.is_(True),
                or_(
                    Author.first_name.ilike(payload.first_name),
                    Author.last_name.ilike(payload.last_name),
                ),
            )
        )
        similar = existing.scalars().all()
        for candidate in similar:
            if (
                slugify(f"{candidate.first_name} {candidate.last_name}")
                == full_name_slug
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"An author with this name already exists (author_id={candidate.uuid}).",
                )

        pub_result = await self.db.execute(
            select(PublisherProfile).where(PublisherProfile.user_id == user.id)
        )
        pub = pub_result.scalar_one_or_none()

        avatar_url = None
        if avatar:
            validate_file(avatar, "avatar")
            ext = (avatar.filename or "jpg").rsplit(".", 1)[-1]
            path = f"authors/{full_name_slug}.{ext}"
            avatar_url = await self.storage.upload(avatar, path)

        author = Author(
            first_name=payload.first_name,
            last_name=payload.last_name,
            bio=payload.bio,
            avatar=avatar_url,
            created_by_id=pub.id if pub else None,
        )
        self.db.add(author)
        await self.db.commit()
        await self.db.refresh(author)
        return await self._build_author_detail(author)

    async def update_author(
        self,
        author_uuid: str,
        payload: CreateAuthorRequest,
        user: User,
    ) -> AuthorDetail:
        """Update an author record (owner or admin/superadmin)."""
        result = await self.db.execute(
            select(Author).where(Author.uuid == author_uuid, Author.is_active.is_(True))
        )
        author = result.scalar_one_or_none()
        if not author:
            raise HTTPException(status_code=404, detail="Author not found.")

        if user.role not in ("admin", "superadmin"):
            pub_result = await self.db.execute(
                select(PublisherProfile).where(PublisherProfile.user_id == user.id)
            )
            pub = pub_result.scalar_one_or_none()
            if not pub or author.created_by_id != pub.id:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to edit this author.",
                )

        if payload.first_name:
            author.first_name = payload.first_name
        if payload.last_name:
            author.last_name = payload.last_name
        if payload.bio is not None:
            author.bio = payload.bio
        await self.db.commit()
        await self.db.refresh(author)
        return await self._build_author_detail(author)

    async def merge_authors(
        self, payload: MergeAuthorsRequest, admin: User
    ) -> dict:
        """Merge duplicate authors into the primary one."""
        primary_result = await self.db.execute(
            select(Author).where(Author.uuid == payload.primary_author_id)
        )
        primary = primary_result.scalar_one_or_none()
        if not primary:
            raise HTTPException(status_code=404, detail="Primary author not found.")

        reassigned = 0
        for dup_uuid in payload.duplicate_author_ids:
            dup_result = await self.db.execute(
                select(Author).where(Author.uuid == dup_uuid)
            )
            dup = dup_result.scalar_one_or_none()
            if not dup:
                raise HTTPException(
                    status_code=404, detail=f"Duplicate author {dup_uuid} not found."
                )

            book_authors = await self.db.execute(
                select(BookAuthor).where(BookAuthor.author_id == dup.id)
            )
            for ba in book_authors.scalars().all():
                existing_check = await self.db.execute(
                    select(BookAuthor).where(
                        BookAuthor.book_id == ba.book_id,
                        BookAuthor.author_id == primary.id,
                    )
                )
                if not existing_check.scalar_one_or_none():
                    ba.author_id = primary.id
                    reassigned += 1
                else:
                    await self.db.delete(ba)

            dup.is_active = False
            dup.deleted_at = datetime.now(timezone.utc)

        await self.db.commit()
        await audit_action(
            self.db,
            "AUTHORS_MERGED",
            admin,
            "author",
            primary.id,
            payload.primary_author_id,
            {
                "duplicates": payload.duplicate_author_ids,
                "reason": payload.reason,
            },
        )
        return {
            "primary_author_id": payload.primary_author_id,
            "duplicates_merged": len(payload.duplicate_author_ids),
            "book_authors_reassigned": reassigned,
        }

    async def list_authors(
        self, search: str | None, page: int, limit: int
    ) -> PaginatedResponse:
        """List active authors with optional name search."""
        query = select(Author).where(Author.is_active.is_(True))
        if search:
            query = query.where(
                or_(
                    Author.first_name.ilike(f"%{search}%"),
                    Author.last_name.ilike(f"%{search}%"),
                )
            )
        total = (
            await self.db.execute(select(func.count()).select_from(query.subquery()))
        ).scalar() or 0

        offset = (page - 1) * limit
        result = await self.db.execute(query.offset(offset).limit(limit))
        authors = result.scalars().all()

        items = []
        for author in authors:
            items.append(await self._build_author_detail(author))

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=compute_pages(total, limit),
        )

    async def get_author_detail(self, author_uuid: str) -> AuthorDetail:
        """Return author detail or 404."""
        result = await self.db.execute(
            select(Author).where(Author.uuid == author_uuid, Author.is_active.is_(True))
        )
        author = result.scalar_one_or_none()
        if not author:
            raise HTTPException(status_code=404, detail="Author not found.")
        return await self._build_author_detail(author)

    async def deactivate_author(self, author_uuid: str, admin: User) -> None:
        """Soft-deactivate an author."""
        result = await self.db.execute(
            select(Author).where(Author.uuid == author_uuid)
        )
        author = result.scalar_one_or_none()
        if not author:
            raise HTTPException(status_code=404, detail="Author not found.")
        author.is_active = False
        author.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()
        await audit_action(
            self.db, "AUTHOR_DEACTIVATED", admin, "author", author.id, author_uuid
        )
