"""Review service — ratings, comments, replies, and reports."""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.book import Book
from app.db.models.publisher import PublisherProfile
from app.db.models.review import Rating, Review, ReviewReply, ReviewReport
from app.db.models.user import User
from app.schemas.auth import UserSummary
from app.schemas.review import (
    BookReviewsResponse,
    RatingSummary,
    ReplyResponse,
    ReportRequest,
    ReviewResponse,
    SubmitReplyRequest,
    SubmitReviewRequest,
)
from app.utils.number_generator import generate
from app.utils.pagination import compute_pages


class ReviewService:
    """Handles book ratings, reviews, replies, and reports."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialise with DB session."""
        self.db = db

    async def _recompute_book_rating(self, book: Book) -> None:
        """Recompute and update book average_rating and total_ratings."""
        result = await self.db.execute(
            select(func.avg(Rating.score), func.count(Rating.id)).where(
                Rating.book_id == book.id
            )
        )
        avg, total = result.one()
        book.average_rating = round(float(avg or 0), 1)
        book.total_ratings = total or 0

    async def _build_review_response(
        self, review: Review, rating: Rating
    ) -> ReviewResponse:
        """Assemble a ReviewResponse from ORM objects."""
        await self.db.refresh(review, ["user", "replies"])
        user = review.user
        user_summary = UserSummary(
            user_id=str(user.uuid),
            email=user.email,
        )

        reply_responses = []
        for reply in review.replies:
            if not reply.is_active:
                continue
            await self.db.refresh(reply, ["user"])
            reply_user = reply.user
            reply_responses.append(
                ReplyResponse(
                    reply_id=str(reply.uuid),
                    user=UserSummary(
                        user_id=str(reply_user.uuid),
                        email=reply_user.email,
                    ),
                    comment=reply.comment,
                    is_publisher_response=reply.is_publisher_response,
                    is_edited=reply.is_edited,
                    created_at=reply.created_at.isoformat() if reply.created_at else "",
                )
            )

        book_result = await self.db.execute(
            select(Book).where(Book.id == review.book_id)
        )
        book = book_result.scalar_one()

        return ReviewResponse(
            review_id=str(review.uuid),
            book_id=str(book.uuid),
            user=user_summary,
            rating=rating.score,
            comment=review.comment,
            is_edited=review.is_edited,
            is_publisher_response=review.is_publisher_response,
            reply_count=review.reply_count,
            replies=reply_responses,
            created_at=review.created_at.isoformat() if review.created_at else "",
            updated_at=review.updated_at.isoformat() if review.updated_at else "",
        )

    async def submit_review(
        self, book_uuid: str, payload: SubmitReviewRequest, user: User
    ) -> ReviewResponse:
        """Create a rating (and optional review) for a book."""
        book_result = await self.db.execute(
            select(Book).where(Book.uuid == book_uuid, Book.is_active.is_(True))
        )
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        if user.role == "publisher":
            pub_result = await self.db.execute(
                select(PublisherProfile).where(PublisherProfile.user_id == user.id)
            )
            pub = pub_result.scalar_one_or_none()
            if pub and book.publisher_id == pub.id:
                raise HTTPException(
                    status_code=403,
                    detail="Publishers cannot rate their own books.",
                )

        existing_rating = await self.db.execute(
            select(Rating).where(Rating.book_id == book.id, Rating.user_id == user.id)
        )
        if existing_rating.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="You already rated this book. Use PATCH to update."
            )

        rating = Rating(book_id=book.id, user_id=user.id, score=payload.rating)
        self.db.add(rating)
        await self.db.flush()

        if payload.comment:
            import redis.asyncio as aioredis
            from app.core.config import settings as _settings

            redis_client = await aioredis.from_url(
                _settings.REDIS_URL, decode_responses=True
            )
            review_number = await generate("review", redis_client)
            await redis_client.aclose()

            review = Review(
                number=review_number,
                book_id=book.id,
                user_id=user.id,
                rating_id=rating.id,
                comment=payload.comment,
            )
            self.db.add(review)
            await self.db.flush()
        else:
            review = None

        await self._recompute_book_rating(book)
        await self.db.commit()

        if review:
            await self.db.refresh(review)
            await self.db.refresh(rating)
            return await self._build_review_response(review, rating)

        await self.db.refresh(rating)
        book_result2 = await self.db.execute(
            select(Book).where(Book.id == book.id)
        )
        book_fresh = book_result2.scalar_one()
        raise HTTPException(status_code=200, detail="Rating submitted (no comment).")

    async def update_review(
        self, book_uuid: str, payload: SubmitReviewRequest, user: User
    ) -> ReviewResponse:
        """Update existing rating and optional review comment."""
        book_result = await self.db.execute(
            select(Book).where(Book.uuid == book_uuid)
        )
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        rating_result = await self.db.execute(
            select(Rating).where(Rating.book_id == book.id, Rating.user_id == user.id)
        )
        rating = rating_result.scalar_one_or_none()
        if not rating:
            raise HTTPException(
                status_code=404, detail="You have not rated this book yet."
            )

        rating.score = payload.rating
        await self._recompute_book_rating(book)

        review_result = await self.db.execute(
            select(Review).where(Review.rating_id == rating.id, Review.is_active.is_(True))
        )
        review = review_result.scalar_one_or_none()
        if review:
            if payload.comment:
                review.comment = payload.comment
                review.is_edited = True
        elif payload.comment:
            import redis.asyncio as aioredis
            from app.core.config import settings as _settings

            redis_client = await aioredis.from_url(
                _settings.REDIS_URL, decode_responses=True
            )
            review_number = await generate("review", redis_client)
            await redis_client.aclose()

            review = Review(
                number=review_number,
                book_id=book.id,
                user_id=user.id,
                rating_id=rating.id,
                comment=payload.comment,
            )
            self.db.add(review)
            await self.db.flush()

        await self.db.commit()
        if review:
            await self.db.refresh(review)
            await self.db.refresh(rating)
            return await self._build_review_response(review, rating)

        raise HTTPException(status_code=200, detail="Rating updated (no comment).")

    async def delete_review(self, book_uuid: str, user: User) -> None:
        """Soft delete review and remove rating from book average."""
        book_result = await self.db.execute(
            select(Book).where(Book.uuid == book_uuid)
        )
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        rating_result = await self.db.execute(
            select(Rating).where(Rating.book_id == book.id, Rating.user_id == user.id)
        )
        rating = rating_result.scalar_one_or_none()
        if not rating:
            raise HTTPException(
                status_code=404, detail="You have not rated this book."
            )

        review_result = await self.db.execute(
            select(Review).where(Review.rating_id == rating.id)
        )
        review = review_result.scalar_one_or_none()
        if review:
            review.is_active = False
            review.deleted_at = datetime.now(timezone.utc)

        await self.db.delete(rating)
        await self._recompute_book_rating(book)
        await self.db.commit()

    async def get_my_review(
        self, book_uuid: str, user: User
    ) -> ReviewResponse | None:
        """Return the current user's review for a book, or None."""
        book_result = await self.db.execute(
            select(Book).where(Book.uuid == book_uuid)
        )
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        rating_result = await self.db.execute(
            select(Rating).where(Rating.book_id == book.id, Rating.user_id == user.id)
        )
        rating = rating_result.scalar_one_or_none()
        if not rating:
            return None

        review_result = await self.db.execute(
            select(Review).where(
                Review.rating_id == rating.id, Review.is_active.is_(True)
            )
        )
        review = review_result.scalar_one_or_none()
        if not review:
            return None
        return await self._build_review_response(review, rating)

    async def submit_reply(
        self, review_id: str, payload: SubmitReplyRequest, user: User
    ) -> ReplyResponse:
        """Add a reply to a review."""
        review_result = await self.db.execute(
            select(Review).where(Review.uuid == review_id, Review.is_active.is_(True))
        )
        review = review_result.scalar_one_or_none()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        is_pub_response = False
        if user.role == "publisher":
            pub_result = await self.db.execute(
                select(PublisherProfile).where(PublisherProfile.user_id == user.id)
            )
            pub = pub_result.scalar_one_or_none()
            book_result = await self.db.execute(
                select(Book).where(Book.id == review.book_id)
            )
            book = book_result.scalar_one()
            if pub and book.publisher_id == pub.id:
                is_pub_response = True

        reply = ReviewReply(
            review_id=review.id,
            user_id=user.id,
            comment=payload.comment,
            is_publisher_response=is_pub_response,
        )
        self.db.add(reply)
        review.reply_count += 1
        await self.db.commit()
        await self.db.refresh(reply)

        return ReplyResponse(
            reply_id=str(reply.uuid),
            user=UserSummary(user_id=str(user.uuid), email=user.email),
            comment=reply.comment,
            is_publisher_response=reply.is_publisher_response,
            is_edited=reply.is_edited,
            created_at=reply.created_at.isoformat() if reply.created_at else "",
        )

    async def update_reply(
        self,
        review_id: str,
        reply_id: str,
        payload: SubmitReplyRequest,
        user: User,
    ) -> ReplyResponse:
        """Update a reply (owner only)."""
        reply_result = await self.db.execute(
            select(ReviewReply).where(
                ReviewReply.uuid == reply_id, ReviewReply.is_active.is_(True)
            )
        )
        reply = reply_result.scalar_one_or_none()
        if not reply:
            raise HTTPException(status_code=404, detail="Reply not found.")
        if reply.user_id != user.id:
            raise HTTPException(status_code=403, detail="Cannot edit another user's reply.")
        reply.comment = payload.comment
        reply.is_edited = True
        await self.db.commit()
        await self.db.refresh(reply)
        return ReplyResponse(
            reply_id=str(reply.uuid),
            user=UserSummary(user_id=str(user.uuid), email=user.email),
            comment=reply.comment,
            is_publisher_response=reply.is_publisher_response,
            is_edited=reply.is_edited,
            created_at=reply.created_at.isoformat() if reply.created_at else "",
        )

    async def delete_reply(
        self, review_id: str, reply_id: str, user: User
    ) -> None:
        """Soft-delete a reply (owner only)."""
        reply_result = await self.db.execute(
            select(ReviewReply).where(
                ReviewReply.uuid == reply_id, ReviewReply.is_active.is_(True)
            )
        )
        reply = reply_result.scalar_one_or_none()
        if not reply:
            raise HTTPException(status_code=404, detail="Reply not found.")
        if reply.user_id != user.id:
            raise HTTPException(status_code=403, detail="Cannot delete another user's reply.")

        review_result = await self.db.execute(
            select(Review).where(Review.id == reply.review_id)
        )
        review = review_result.scalar_one()
        review.reply_count = max(0, review.reply_count - 1)

        reply.is_active = False
        reply.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def report_review(
        self, review_id: str, payload: ReportRequest, user: User
    ) -> None:
        """Report a review for moderation."""
        review_result = await self.db.execute(
            select(Review).where(Review.uuid == review_id, Review.is_active.is_(True))
        )
        review = review_result.scalar_one_or_none()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        existing_report = await self.db.execute(
            select(ReviewReport).where(
                ReviewReport.review_id == review.id,
                ReviewReport.reported_by_id == user.id,
            )
        )
        if existing_report.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="You have already reported this review."
            )

        report = ReviewReport(
            review_id=review.id,
            reported_by_id=user.id,
            reason=payload.reason.upper() if payload.reason.upper() in (
                "SPAM", "OFFENSIVE", "MISLEADING", "OTHER"
            ) else "OTHER",
            note=payload.note,
        )
        self.db.add(report)
        review.report_count += 1
        await self.db.commit()

    async def report_reply(
        self, review_id: str, reply_id: str, payload: ReportRequest, user: User
    ) -> None:
        """Report a reply for moderation."""
        reply_result = await self.db.execute(
            select(ReviewReply).where(
                ReviewReply.uuid == reply_id, ReviewReply.is_active.is_(True)
            )
        )
        reply = reply_result.scalar_one_or_none()
        if not reply:
            raise HTTPException(status_code=404, detail="Reply not found.")

        existing_report = await self.db.execute(
            select(ReviewReport).where(
                ReviewReport.reply_id == reply.id,
                ReviewReport.reported_by_id == user.id,
            )
        )
        if existing_report.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="You have already reported this reply."
            )

        report = ReviewReport(
            reply_id=reply.id,
            reported_by_id=user.id,
            reason=payload.reason.upper() if payload.reason.upper() in (
                "SPAM", "OFFENSIVE", "MISLEADING", "OTHER"
            ) else "OTHER",
            note=payload.note,
        )
        self.db.add(report)
        await self.db.commit()

    async def get_book_reviews(
        self, book_uuid: str, sort_by: str, pagination
    ) -> BookReviewsResponse:
        """Return paginated reviews with rating summary."""
        book_result = await self.db.execute(
            select(Book).where(Book.uuid == book_uuid)
        )
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        query = select(Review).where(
            Review.book_id == book.id, Review.is_active.is_(True)
        )
        if sort_by == "highest":
            query = query.join(Rating, Rating.id == Review.rating_id).order_by(
                Rating.score.desc()
            )
        elif sort_by == "lowest":
            query = query.join(Rating, Rating.id == Review.rating_id).order_by(
                Rating.score.asc()
            )
        elif sort_by == "most_replies":
            query = query.order_by(Review.reply_count.desc())
        else:
            query = query.order_by(Review.created_at.desc())

        total = (
            await self.db.execute(
                select(func.count()).select_from(
                    select(Review).where(
                        Review.book_id == book.id, Review.is_active.is_(True)
                    ).subquery()
                )
            )
        ).scalar() or 0

        page = getattr(pagination, "page", 1)
        limit = getattr(pagination, "limit", 20)
        offset = (page - 1) * limit
        result = await self.db.execute(query.offset(offset).limit(limit))
        reviews = result.scalars().all()

        items = []
        for review in reviews:
            rating_result = await self.db.execute(
                select(Rating).where(Rating.id == review.rating_id)
            )
            rating = rating_result.scalar_one()
            items.append(await self._build_review_response(review, rating))

        breakdown: dict[str, int] = {}
        for score in range(1, 6):
            count_result = await self.db.execute(
                select(func.count(Rating.id)).where(
                    Rating.book_id == book.id, Rating.score == score
                )
            )
            breakdown[str(score)] = count_result.scalar() or 0

        review_count_result = await self.db.execute(
            select(func.count(Review.id)).where(
                Review.book_id == book.id, Review.is_active.is_(True)
            )
        )

        return BookReviewsResponse(
            summary=RatingSummary(
                average_rating=float(book.average_rating),
                total_ratings=book.total_ratings,
                total_reviews=review_count_result.scalar() or 0,
                rating_breakdown=breakdown,
            ),
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=compute_pages(total, limit),
        )

    async def remove_review(self, review_id: str, admin: User) -> None:
        """Admin removes a review and closes reports."""
        from app.utils.audit import audit_action

        review_result = await self.db.execute(
            select(Review).where(Review.uuid == review_id)
        )
        review = review_result.scalar_one_or_none()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        rating_result = await self.db.execute(
            select(Rating).where(Rating.id == review.rating_id)
        )
        rating = rating_result.scalar_one_or_none()

        await self.db.refresh(review, ["replies"])
        for reply in review.replies:
            reply.is_active = False
            reply.deleted_at = datetime.now(timezone.utc)

        review.is_active = False
        review.deleted_at = datetime.now(timezone.utc)

        if rating:
            await self.db.delete(rating)

        book_result = await self.db.execute(
            select(Book).where(Book.id == review.book_id)
        )
        book = book_result.scalar_one()
        await self._recompute_book_rating(book)
        await self.db.commit()
        await audit_action(
            self.db, "REVIEW_REMOVED", admin, "review", review.id, review_id
        )

    async def list_all_reviews(self) -> dict:
        """Return all active reviews platform-wide (admin use)."""
        result = await self.db.execute(
            select(Review).where(Review.is_active.is_(True)).order_by(
                Review.created_at.desc()
            )
        )
        reviews = result.scalars().all()
        return {
            "total": len(reviews),
            "items": [await self._build_review_response(r) for r in reviews],
        }

    async def list_reported_reviews(self, status: str | None = None) -> dict:
        """Return reviews that have reports, optionally filtered by report status."""
        query = select(ReviewReport)
        if status:
            query = query.where(ReviewReport.status == status.upper())
        result = await self.db.execute(query)
        reports = result.scalars().all()
        return {
            "total": len(reports),
            "items": [
                {
                    "report_id": rp.uuid,
                    "review_id": rp.review.uuid if rp.review else None,
                    "reason": rp.reason,
                    "status": rp.status,
                    "created_at": rp.created_at.isoformat() if rp.created_at else None,
                }
                for rp in reports
            ],
        }

    async def dismiss_report(
        self, review_id: str, note: str, admin: User
    ) -> None:
        """Dismiss a review report."""
        from app.utils.audit import audit_action

        review_result = await self.db.execute(
            select(Review).where(Review.uuid == review_id)
        )
        review = review_result.scalar_one_or_none()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        reports_result = await self.db.execute(
            select(ReviewReport).where(
                ReviewReport.review_id == review.id,
                ReviewReport.status == "PENDING",
            )
        )
        reports = reports_result.scalars().all()
        now = datetime.now(timezone.utc)
        for report in reports:
            report.status = "DISMISSED"
            report.note = note
            report.reviewed_by_id = admin.id
            report.reviewed_at = now

        await self.db.commit()
        await audit_action(
            self.db, "REPORT_DISMISSED", admin, "review", review.id, review_id
        )
