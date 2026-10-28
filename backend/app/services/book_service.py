"""Book service — create, list, approve, reject, archive books; manage categories and tags."""

import json
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.book import Book, BookAuthor, BookTag, BookVersion, BookVersionActionLog
from app.db.models.category import Category, Tag
from app.db.models.author import Author
from app.db.models.publisher import PublisherProfile
from app.db.models.user import User
from app.schemas.book import (
    AuthorDetail,
    AuthorSummary,
    BookDetailResponse,
    BookListItem,
    BookStatusSummary,
    BookVersionSummary,
    CategorySummary,
    CreateBookRequest,
    PDFFileSummary,
    PublisherBookListItem,
    PublisherBookListResponse,
    TagSummary,
)
from app.schemas.common import PaginatedResponse
from app.schemas.utils import LanguageSummary, PublisherSummary
from app.storage.base import BaseStorageProvider
from app.storage.validators import validate_file
from app.utils.audit import audit_action
from app.utils.cache import get_cached, invalidate, invalidate_pattern, set_cached
from app.utils.number_generator import generate
from app.utils.pagination import compute_pages
from app.utils.slug import slugify

CACHE_CATEGORIES_KEY = "cache:categories"
CACHE_TAGS_KEY = "cache:tags"


class BookService:
    """Handles book lifecycle, categories, tags, and analytics."""

    def __init__(
        self, db: AsyncSession, storage: BaseStorageProvider, redis: Redis
    ) -> None:
        """Initialise with DB session, storage provider, and Redis."""
        self.db = db
        self.storage = storage
        self.redis = redis

    async def _get_publisher(self, user: User) -> PublisherProfile:
        """Return publisher profile for user or 404."""
        result = await self.db.execute(
            select(PublisherProfile).where(PublisherProfile.user_id == user.id)
        )
        pub = result.scalar_one_or_none()
        if not pub:
            raise HTTPException(status_code=404, detail="Publisher profile not found.")
        return pub

    async def _build_book_detail(
        self, book: Book, version: BookVersion, user: User | None
    ) -> BookDetailResponse:
        """Assemble a BookDetailResponse from ORM objects."""
        await self.db.refresh(book, ["category", "language", "publisher", "book_authors", "book_tags", "versions"])

        category = book.category
        language = book.language
        pub = book.publisher

        pub_user_result = await self.db.execute(
            select(User).where(User.id == pub.user_id)
        )
        pub_user = pub_user_result.scalar_one()

        authors = []
        for ba in book.book_authors:
            author_result = await self.db.execute(
                select(Author).where(Author.id == ba.author_id)
            )
            author = author_result.scalar_one()
            book_count_result = await self.db.execute(
                select(func.count(BookAuthor.id)).where(BookAuthor.author_id == author.id)
            )
            authors.append(
                AuthorDetail(
                    author_id=str(author.uuid),
                    first_name=author.first_name,
                    last_name=author.last_name,
                    bio=author.bio,
                    avatar=author.avatar,
                    total_books=book_count_result.scalar() or 0,
                )
            )

        tags = []
        for bt in book.book_tags:
            tag_result = await self.db.execute(
                select(Tag).where(Tag.id == bt.tag_id)
            )
            tag = tag_result.scalar_one()
            tags.append(
                TagSummary(
                    tag_id=str(tag.uuid),
                    name=tag.name,
                    slug=tag.slug,
                )
            )

        versions_list = []
        for v in book.versions:
            versions_list.append(
                BookVersionSummary(
                    version_id=str(v.uuid),
                    version_number=v.version_number,
                    version_label=v.version_label,
                    is_current=v.is_current,
                    status=v.status,
                    total_downloads=v.total_downloads,
                    approved_at=v.approved_at.isoformat() if v.approved_at else None,
                )
            )

        current_version_summary = BookVersionSummary(
            version_id=str(version.uuid),
            version_number=version.version_number,
            version_label=version.version_label,
            is_current=version.is_current,
            status=version.status,
            total_downloads=version.total_downloads,
            approved_at=version.approved_at.isoformat() if version.approved_at else None,
        )

        is_downloadable = user is not None and user.role in ("reader", "publisher")

        return BookDetailResponse(
            book_id=str(book.uuid),
            title=version.title,
            thumbnail=version.thumbnail,
            description=version.description,
            category=CategorySummary(
                category_id=str(category.uuid),
                name=category.name,
                slug=category.slug,
            ),
            tags=tags,
            authors=authors,
            publisher=PublisherSummary(
                publisher_id=str(pub_user.uuid),
                display_name=pub.display_name,
                logo=pub.logo,
                is_verified=pub.is_verified,
            ),
            language=LanguageSummary(
                language_id=str(language.uuid),
                name=language.name,
                iso_code=language.iso_code,
            ),
            page_count=version.page_count,
            publication_year=version.publication_year,
            isbn=version.isbn,
            average_rating=float(book.average_rating),
            total_ratings=book.total_ratings,
            total_downloads=book.total_downloads,
            versions=versions_list,
            current_version=current_version_summary,
            pdf_file=PDFFileSummary(
                file_name=version.pdf_file_name,
                file_size_mb=float(version.pdf_file_size_mb),
            ),
            is_downloadable=is_downloadable,
            status=version.status,
            archive_notice=None,
            created_at=book.created_at.isoformat() if book.created_at else "",
        )

    async def create_book(
        self,
        payload: CreateBookRequest,
        thumbnail: UploadFile,
        pdf_file: UploadFile,
        user: User,
    ) -> BookDetailResponse:
        """Create a new book in DRAFT status with initial version."""
        validate_file(thumbnail, "thumbnail")
        validate_file(pdf_file, "book_pdf")

        import redis.asyncio as aioredis
        from app.core.config import settings as _settings

        redis_client = await aioredis.from_url(
            _settings.REDIS_URL, decode_responses=True
        )
        book_number = await generate("book", redis_client)
        await redis_client.aclose()

        pub = await self._get_publisher(user)

        book = Book(
            number=book_number,
            publisher_id=pub.id,
            category_id=payload.category_id,
            language_id=payload.language_id,
            title=payload.title,
        )
        self.db.add(book)
        await self.db.flush()

        thumb_path = f"books/{book.uuid}/v1/thumbnail.jpg"
        thumb_url = await self.storage.upload(thumbnail, thumb_path)

        pdf_ext = (pdf_file.filename or "book.pdf").rsplit(".", 1)[-1]
        pdf_path = f"books/{book.uuid}/v1/book.{pdf_ext}"
        pdf_url = await self.storage.upload(pdf_file, pdf_path)
        pdf_size_mb = round((pdf_file.size or 0) / (1024 * 1024), 2)

        version = BookVersion(
            book_id=book.id,
            version_number=1,
            version_label=payload.version_label,
            title=payload.title,
            description=payload.description,
            isbn=payload.isbn,
            page_count=payload.page_count,
            publication_year=payload.publication_year,
            thumbnail=thumb_url,
            pdf_file=pdf_url,
            pdf_file_name=pdf_file.filename or "book.pdf",
            pdf_file_size_mb=pdf_size_mb,
            status="DRAFT",
        )
        self.db.add(version)
        await self.db.flush()

        book.current_version_id = version.id

        for author_input in payload.authors:
            if author_input.author_id:
                author_result = await self.db.execute(
                    select(Author).where(Author.id == author_input.author_id)
                )
                author = author_result.scalar_one_or_none()
                if author:
                    self.db.add(BookAuthor(book_id=book.id, author_id=author.id))
            elif author_input.first_name and author_input.last_name:
                new_author = Author(
                    first_name=author_input.first_name,
                    last_name=author_input.last_name,
                    bio=author_input.bio,
                    created_by_id=pub.id,
                )
                self.db.add(new_author)
                await self.db.flush()
                self.db.add(BookAuthor(book_id=book.id, author_id=new_author.id))

        for tag_id in payload.tag_ids:
            self.db.add(BookTag(book_id=book.id, tag_id=tag_id))

        for tag_name in payload.new_tags:
            tag_slug = slugify(tag_name)
            existing_tag = await self.db.execute(
                select(Tag).where(Tag.slug == tag_slug)
            )
            tag = existing_tag.scalar_one_or_none()
            if not tag:
                tag = Tag(
                    name=tag_name,
                    slug=tag_slug,
                    status="PENDING",
                    suggested_by_id=pub.id,
                )
                self.db.add(tag)
                await self.db.flush()
            self.db.add(BookTag(book_id=book.id, tag_id=tag.id))

        log = BookVersionActionLog(
            book_version_id=version.id,
            action="CREATED",
            performed_by_id=user.id,
            performed_by_type=user.role,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(book)
        await self.db.refresh(version)

        return await self._build_book_detail(book, version, user)

    async def submit_book(self, book_uuid: str, user: User) -> None:
        """Submit book version for admin review."""
        book, version = await self._load_book_and_verify_owner(book_uuid, user)
        if version.status not in ("DRAFT", "REJECTED"):
            raise HTTPException(
                status_code=400,
                detail="Book can only be submitted from DRAFT or REJECTED status.",
            )
        is_resubmission = version.status == "REJECTED"
        version.status = "PENDING"
        version.submitted_at = datetime.now(timezone.utc)
        if is_resubmission:
            version.is_resubmission = True
            version.resubmission_count += 1
            version.rejection_reason = None
            action = "RESUBMITTED"
        else:
            action = "SUBMITTED"

        log = BookVersionActionLog(
            book_version_id=version.id,
            action=action,
            performed_by_id=user.id,
            performed_by_type=user.role,
        )
        self.db.add(log)
        await self.db.commit()

        from app.tasks.notification_tasks import create_in_app_notification

        create_in_app_notification.delay(str(user.uuid), "BOOK_SUBMITTED")

    async def approve_book(self, book_uuid: str, admin: User) -> None:
        """Approve a book version and set it as current."""
        result = await self.db.execute(
            select(Book).where(Book.uuid == book_uuid, Book.is_active.is_(True))
        )
        book = result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        version_result = await self.db.execute(
            select(BookVersion).where(
                BookVersion.book_id == book.id,
                BookVersion.id == book.current_version_id,
            )
        )
        version = version_result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Book version not found.")

        now = datetime.now(timezone.utc)
        version.status = "APPROVED"
        version.approved_at = now
        version.reviewed_by_id = admin.id
        version.is_current = True

        await self.db.refresh(book, ["category", "book_tags"])
        book.category.total_books += 1
        for bt in book.book_tags:
            tag_result = await self.db.execute(
                select(Tag).where(Tag.id == bt.tag_id)
            )
            tag = tag_result.scalar_one_or_none()
            if tag:
                tag.total_books += 1

        log = BookVersionActionLog(
            book_version_id=version.id,
            action="APPROVED",
            performed_by_id=admin.id,
            performed_by_type=admin.role,
        )
        self.db.add(log)
        await self.db.commit()

        await invalidate(self.redis, f"cache:book:{book_uuid}")
        await invalidate_pattern(self.redis, "cache:books:*")
        await invalidate(self.redis, CACHE_CATEGORIES_KEY)

        pub_user_result = await self.db.execute(
            select(User).where(User.id == book.publisher.user_id)
        )
        pub_user = pub_user_result.scalar_one()

        from app.tasks.email_tasks import send_book_status_email
        from app.tasks.notification_tasks import create_in_app_notification

        send_book_status_email.delay(str(pub_user.uuid), "approved", str(book.uuid))
        create_in_app_notification.delay(str(pub_user.uuid), "BOOK_APPROVED")
        await audit_action(self.db, "BOOK_APPROVED", admin, "book", book.id, book_uuid)

    async def reject_book(self, book_uuid: str, reason: str, admin: User) -> None:
        """Reject a book with a reason."""
        result = await self.db.execute(select(Book).where(Book.uuid == book_uuid))
        book = result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        version_result = await self.db.execute(
            select(BookVersion).where(
                BookVersion.book_id == book.id,
                BookVersion.id == book.current_version_id,
            )
        )
        version = version_result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Book version not found.")

        version.status = "REJECTED"
        version.rejection_reason = reason
        version.rejected_at = datetime.now(timezone.utc)
        version.reviewed_by_id = admin.id

        log = BookVersionActionLog(
            book_version_id=version.id,
            action="REJECTED",
            performed_by_id=admin.id,
            performed_by_type=admin.role,
            note=reason,
        )
        self.db.add(log)
        await self.db.commit()

        await self.db.refresh(book, ["publisher"])
        pub_user_result = await self.db.execute(
            select(User).where(User.id == book.publisher.user_id)
        )
        pub_user = pub_user_result.scalar_one()

        from app.tasks.email_tasks import send_book_status_email
        from app.tasks.notification_tasks import create_in_app_notification

        send_book_status_email.delay(str(pub_user.uuid), "rejected", str(book.uuid))
        create_in_app_notification.delay(str(pub_user.uuid), "BOOK_REJECTED")
        await audit_action(self.db, "BOOK_REJECTED", admin, "book", book.id, book_uuid)

    async def archive_book(self, book_uuid: str, user: User) -> None:
        """Archive a publisher's own book."""
        book, version = await self._load_book_and_verify_owner(book_uuid, user)
        version.status = "ARCHIVED"
        version.archived_at = datetime.now(timezone.utc)
        book.is_active = False

        await self.db.refresh(book, ["category"])
        if book.category.total_books > 0:
            book.category.total_books -= 1

        log = BookVersionActionLog(
            book_version_id=version.id,
            action="ARCHIVED",
            performed_by_id=user.id,
            performed_by_type=user.role,
        )
        self.db.add(log)
        await self.db.commit()

        await invalidate(self.redis, f"cache:book:{book_uuid}")
        await invalidate_pattern(self.redis, "cache:books:*")

    async def unarchive_book(self, book_uuid: str, user: User) -> None:
        """Unarchive a book, reverting to DRAFT."""
        book, version = await self._load_book_and_verify_owner(book_uuid, user)
        version.status = "DRAFT"
        version.archived_at = None
        book.is_active = True
        await self.db.commit()

    async def update_book(
        self,
        book_uuid: str,
        payload: CreateBookRequest,
        thumbnail: UploadFile | None,
        pdf_file: UploadFile | None,
        user: User,
    ) -> BookDetailResponse:
        """Update a book in DRAFT or REJECTED status."""
        book, version = await self._load_book_and_verify_owner(book_uuid, user)
        if version.status not in ("DRAFT", "REJECTED"):
            raise HTTPException(
                status_code=400, detail="Book can only be edited when DRAFT or REJECTED."
            )
        if payload.title:
            version.title = payload.title
            book.title = payload.title
        if payload.description:
            version.description = payload.description
        if payload.isbn is not None:
            version.isbn = payload.isbn
        if payload.page_count is not None:
            version.page_count = payload.page_count
        if payload.publication_year is not None:
            version.publication_year = payload.publication_year
        if payload.category_id:
            book.category_id = payload.category_id
        if payload.language_id:
            book.language_id = payload.language_id

        if thumbnail:
            validate_file(thumbnail, "thumbnail")
            thumb_path = f"books/{book.uuid}/v{version.version_number}/thumbnail.jpg"
            version.thumbnail = await self.storage.upload(thumbnail, thumb_path)

        if pdf_file:
            validate_file(pdf_file, "book_pdf")
            pdf_ext = (pdf_file.filename or "book.pdf").rsplit(".", 1)[-1]
            pdf_path = f"books/{book.uuid}/v{version.version_number}/book.{pdf_ext}"
            version.pdf_file = await self.storage.upload(pdf_file, pdf_path)
            version.pdf_file_name = pdf_file.filename or "book.pdf"
            version.pdf_file_size_mb = round((pdf_file.size or 0) / (1024 * 1024), 2)

        version.rejection_reason = None
        await self.db.commit()
        await self.db.refresh(book)
        await self.db.refresh(version)
        return await self._build_book_detail(book, version, user)

    async def get_publisher_book_detail(
        self, book_uuid: str, user: User
    ) -> BookDetailResponse:
        """Get a publisher's own book detail (all statuses)."""
        book, version = await self._load_book_and_verify_owner(book_uuid, user)
        return await self._build_book_detail(book, version, user)

    async def list_approved_books(
        self, filters: dict, page: int, limit: int
    ) -> PaginatedResponse:
        """List public approved books with filters and pagination."""
        import hashlib

        cache_key = f"cache:books:list:{hashlib.md5(str(filters).encode()).hexdigest()}"
        cached = await get_cached(self.redis, cache_key)
        if cached:
            return PaginatedResponse(**cached)

        query = (
            select(BookVersion)
            .join(Book, Book.id == BookVersion.book_id)
            .where(
                BookVersion.status == "APPROVED",
                BookVersion.is_current.is_(True),
                Book.is_active.is_(True),
            )
        )

        if filters.get("category_id"):
            query = query.where(Book.category_id == filters["category_id"])
        if filters.get("language_id"):
            query = query.where(Book.language_id == filters["language_id"])
        if filters.get("publication_year"):
            query = query.where(BookVersion.publication_year == filters["publication_year"])
        if filters.get("search"):
            from sqlalchemy import text as sa_text

            query = query.where(
                BookVersion.search_vector.op("@@")(
                    func.plainto_tsquery("english", filters["search"])
                )
            )
        if filters.get("tag_id"):
            query = query.join(
                BookTag, BookTag.book_id == Book.id
            ).where(BookTag.tag_id == filters["tag_id"])

        sort_by = filters.get("sort_by", "latest")
        if sort_by == "popular":
            query = query.order_by(Book.total_downloads.desc())
        elif sort_by == "rating":
            query = query.order_by(Book.average_rating.desc())
        else:
            query = query.order_by(Book.created_at.desc())

        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        offset = (page - 1) * limit
        result = await self.db.execute(query.offset(offset).limit(limit))
        versions = result.scalars().all()

        items = []
        for version in versions:
            book_result = await self.db.execute(
                select(Book).where(Book.id == version.book_id)
            )
            book = book_result.scalar_one()
            await self.db.refresh(book, ["category", "language", "publisher", "book_authors"])

            pub = book.publisher
            pub_user_result = await self.db.execute(
                select(User).where(User.id == pub.user_id)
            )
            pub_user = pub_user_result.scalar_one()

            authors = []
            for ba in book.book_authors:
                a_result = await self.db.execute(
                    select(Author).where(Author.id == ba.author_id)
                )
                author = a_result.scalar_one()
                authors.append(
                    AuthorSummary(
                        author_id=str(author.uuid),
                        first_name=author.first_name,
                        last_name=author.last_name,
                        avatar=author.avatar,
                    )
                )

            items.append(
                BookListItem(
                    book_id=str(book.uuid),
                    title=version.title,
                    thumbnail=version.thumbnail,
                    description=version.description,
                    category=CategorySummary(
                        category_id=str(book.category.uuid),
                        name=book.category.name,
                        slug=book.category.slug,
                    ),
                    authors=authors,
                    publisher=PublisherSummary(
                        publisher_id=str(pub_user.uuid),
                        display_name=pub.display_name,
                        logo=pub.logo,
                        is_verified=pub.is_verified,
                    ),
                    language=LanguageSummary(
                        language_id=str(book.language.uuid),
                        name=book.language.name,
                        iso_code=book.language.iso_code,
                    ),
                    average_rating=float(book.average_rating),
                    total_ratings=book.total_ratings,
                    total_downloads=book.total_downloads,
                    publication_year=version.publication_year,
                    created_at=book.created_at.isoformat() if book.created_at else "",
                )
            )

        result_data = PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=compute_pages(total, limit),
        )
        await set_cached(self.redis, cache_key, result_data.model_dump())
        return result_data

    async def get_book_detail(
        self, book_uuid: str, user: User | None
    ) -> BookDetailResponse:
        """Return book detail, respecting visibility rules."""
        cache_key = f"cache:book:{book_uuid}"
        cached = await get_cached(self.redis, cache_key)
        if cached and not user:
            return BookDetailResponse(**cached)

        result = await self.db.execute(select(Book).where(Book.uuid == book_uuid))
        book = result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        if not book.is_active:
            if not user:
                raise HTTPException(status_code=404, detail="Book not found.")

        version_result = await self.db.execute(
            select(BookVersion).where(
                BookVersion.id == book.current_version_id
            )
        )
        version = version_result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Book version not found.")

        detail = await self._build_book_detail(book, version, user)
        if not user:
            await set_cached(self.redis, cache_key, detail.model_dump())
        return detail

    async def get_publisher_books(
        self, user: User, status: str | None, page: int, limit: int
    ) -> PublisherBookListResponse:
        """Return publisher's own books with status summary."""
        pub = await self._get_publisher(user)
        query = (
            select(BookVersion)
            .join(Book, Book.id == BookVersion.book_id)
            .where(
                Book.publisher_id == pub.id,
                BookVersion.is_current.is_(True),
            )
        )
        if status:
            query = query.where(BookVersion.status == status)

        total = (
            await self.db.execute(select(func.count()).select_from(query.subquery()))
        ).scalar() or 0

        offset = (page - 1) * limit
        result = await self.db.execute(query.offset(offset).limit(limit))
        versions = result.scalars().all()

        items = [
            PublisherBookListItem(
                book_id=str(
                    (
                        await self.db.execute(
                            select(Book.uuid).where(Book.id == v.book_id)
                        )
                    ).scalar()
                ),
                title=v.title,
                thumbnail=v.thumbnail,
                status=v.status,
                total_downloads=v.total_downloads,
                average_rating=float(
                    (
                        await self.db.execute(
                            select(Book.average_rating).where(Book.id == v.book_id)
                        )
                    ).scalar()
                    or 0
                ),
                submitted_at=v.submitted_at.isoformat() if v.submitted_at else None,
                approved_at=v.approved_at.isoformat() if v.approved_at else None,
                rejection_reason=v.rejection_reason,
                is_resubmission=v.is_resubmission,
                resubmission_count=v.resubmission_count,
            )
            for v in versions
        ]

        counts: dict[str, int] = {}
        for status_name in ("DRAFT", "PENDING", "APPROVED", "REJECTED", "ARCHIVED"):
            count_result = await self.db.execute(
                select(func.count(BookVersion.id))
                .join(Book, Book.id == BookVersion.book_id)
                .where(
                    Book.publisher_id == pub.id,
                    BookVersion.is_current.is_(True),
                    BookVersion.status == status_name,
                )
            )
            counts[status_name.lower()] = count_result.scalar() or 0

        summary = BookStatusSummary(
            total=sum(counts.values()),
            draft=counts["draft"],
            pending=counts["pending"],
            approved=counts["approved"],
            rejected=counts["rejected"],
            archived=counts["archived"],
        )
        return PublisherBookListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=compute_pages(total, limit),
            summary=summary,
        )

    async def list_categories(self) -> list[CategorySummary]:
        """Return active categories, cached in Redis."""
        cached = await get_cached(self.redis, CACHE_CATEGORIES_KEY)
        if cached:
            return [CategorySummary(**c) for c in cached]

        result = await self.db.execute(
            select(Category).where(Category.is_active.is_(True)).order_by(Category.name)
        )
        categories = result.scalars().all()
        data = [
            CategorySummary(
                category_id=str(c.uuid), name=c.name, slug=c.slug
            )
            for c in categories
        ]
        await set_cached(
            self.redis, CACHE_CATEGORIES_KEY, [d.model_dump() for d in data]
        )
        return data

    async def list_approved_tags(self) -> list[TagSummary]:
        """Return approved active tags."""
        cached = await get_cached(self.redis, CACHE_TAGS_KEY)
        if cached:
            return [TagSummary(**t) for t in cached]

        result = await self.db.execute(
            select(Tag).where(
                Tag.status == "APPROVED", Tag.is_active.is_(True)
            ).order_by(Tag.name)
        )
        tags = result.scalars().all()
        data = [
            TagSummary(tag_id=str(t.uuid), name=t.name, slug=t.slug, status=t.status)
            for t in tags
        ]
        await set_cached(self.redis, CACHE_TAGS_KEY, [d.model_dump() for d in data])
        return data

    async def manage_tag(
        self, tag_id: str, action: str, admin: User, **kwargs
    ) -> None:
        """Approve, reject, update, or deactivate a tag."""
        result = await self.db.execute(select(Tag).where(Tag.uuid == tag_id))
        tag = result.scalar_one_or_none()
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found.")

        now = datetime.now(timezone.utc)
        if action == "approve":
            tag.status = "APPROVED"
            tag.reviewed_by_id = admin.id
            tag.reviewed_at = now
        elif action == "reject":
            tag.status = "REJECTED"
            tag.reviewed_by_id = admin.id
            tag.reviewed_at = now
        elif action == "update":
            if kwargs.get("name"):
                tag.name = kwargs["name"]
                tag.slug = slugify(kwargs["name"])
        elif action == "deactivate":
            tag.is_active = False
            tag.deleted_at = now

        await self.db.commit()
        await invalidate(self.redis, CACHE_TAGS_KEY)
        await audit_action(
            self.db, f"TAG_{action.upper()}", admin, "tag", tag.id, tag_id
        )

    async def manage_category(
        self, action: str, admin: User, **kwargs
    ) -> Category | None:
        """Create, update, or deactivate a category."""
        now = datetime.now(timezone.utc)
        category_id = kwargs.get("category_id")

        if action == "create":
            name = kwargs["name"]
            slug = slugify(name)
            existing = await self.db.execute(
                select(Category).where(Category.slug == slug)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=400, detail="Category with this name already exists."
                )
            category = Category(name=name, slug=slug)
            self.db.add(category)
            await self.db.commit()
            await invalidate(self.redis, CACHE_CATEGORIES_KEY)
            await audit_action(
                self.db, "CATEGORY_CREATED", admin, "category", category.id, slug
            )
            return category

        result = await self.db.execute(
            select(Category).where(Category.uuid == category_id)
        )
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")

        if action == "update":
            if kwargs.get("name"):
                category.name = kwargs["name"]
                category.slug = slugify(kwargs["name"])
        elif action == "deactivate":
            category.is_active = False
            category.deleted_at = now

        await self.db.commit()
        await invalidate(self.redis, CACHE_CATEGORIES_KEY)
        await audit_action(
            self.db,
            f"CATEGORY_{action.upper()}",
            admin,
            "category",
            category.id,
            str(category_id),
        )
        return category

    async def _load_book_and_verify_owner(
        self, book_uuid: str, user: User
    ) -> tuple[Book, BookVersion]:
        """Load a book and verify the caller is its publisher."""
        pub = await self._get_publisher(user)
        result = await self.db.execute(select(Book).where(Book.uuid == book_uuid))
        book = result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")
        if book.publisher_id != pub.id:
            raise HTTPException(
                status_code=403, detail="You do not own this book."
            )
        version_result = await self.db.execute(
            select(BookVersion).where(
                BookVersion.id == book.current_version_id
            )
        )
        version = version_result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Book version not found.")
        return book, version
