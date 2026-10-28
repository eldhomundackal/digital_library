import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Rating(Base):
    """Stores every rating including silent ones (no comment)."""

    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("book_id", "user_id"),
        CheckConstraint("score >= 1 AND score <= 5", name="rating_score_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    book: Mapped["Book"] = relationship()
    user: Mapped["User"] = relationship()
    review: Mapped["Review | None"] = relationship(
        back_populates="rating", uselist=False
    )


class Review(Base):
    """Ratings that also have a comment — shown in the reviews list."""

    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("book_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )  # REV-000001
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    rating_id: Mapped[int] = mapped_column(ForeignKey("ratings.id"), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_publisher_response: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    reply_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    book: Mapped["Book"] = relationship()
    user: Mapped["User"] = relationship()
    rating: Mapped["Rating"] = relationship(back_populates="review")
    replies: Mapped[list["ReviewReply"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )
    reports: Mapped[list["ReviewReport"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )


class ReviewReply(Base):
    """One-level-deep reply to a review."""

    __tablename__ = "review_replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_publisher_response: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    review: Mapped["Review"] = relationship(back_populates="replies")
    user: Mapped["User"] = relationship()
    reports: Mapped[list["ReviewReport"]] = relationship(back_populates="reply")


class ReviewReport(Base):
    """Report filed against a review or reply."""

    __tablename__ = "review_reports"
    __table_args__ = (
        CheckConstraint(
            "(review_id IS NOT NULL AND reply_id IS NULL)"
            " OR (review_id IS NULL AND reply_id IS NOT NULL)",
            name="review_or_reply_check",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    review_id: Mapped[int | None] = mapped_column(
        ForeignKey("reviews.id"), nullable=True
    )
    reply_id: Mapped[int | None] = mapped_column(
        ForeignKey("review_replies.id"), nullable=True
    )
    reported_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(
        Enum(
            "SPAM",
            "OFFENSIVE",
            "MISLEADING",
            "OTHER",
            name="report_reason_enum",
        ),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "PENDING",
            "REVIEWED",
            "DISMISSED",
            name="report_status_enum",
        ),
        nullable=False,
        default="PENDING",
    )
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    review: Mapped["Review | None"] = relationship(
        back_populates="reports", foreign_keys=[review_id]
    )
    reply: Mapped["ReviewReply | None"] = relationship(
        back_populates="reports", foreign_keys=[reply_id]
    )
    reported_by: Mapped["User"] = relationship(foreign_keys=[reported_by_id])
    reviewed_by: Mapped["User | None"] = relationship(
        foreign_keys=[reviewed_by_id]
    )
