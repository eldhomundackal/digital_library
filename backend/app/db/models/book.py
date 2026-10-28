import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Book(Base):
    """Master book record; content lives in BookVersion."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )  # BK-000001
    publisher_id: Mapped[int] = mapped_column(
        ForeignKey("publisher_profiles.id"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False
    )
    language_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    current_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("book_versions.id", use_alter=True), nullable=True
    )
    average_rating: Mapped[float] = mapped_column(
        Numeric(3, 1), nullable=False, default=0.0
    )
    total_ratings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_downloads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    publisher: Mapped["PublisherProfile"] = relationship(
        back_populates="books", foreign_keys=[publisher_id]
    )
    category: Mapped["Category"] = relationship()
    language: Mapped["Language"] = relationship()
    current_version: Mapped["BookVersion | None"] = relationship(
        foreign_keys=[current_version_id], post_update=True
    )
    versions: Mapped[list["BookVersion"]] = relationship(
        back_populates="book",
        foreign_keys="BookVersion.book_id",
        cascade="all, delete-orphan",
    )
    book_authors: Mapped[list["BookAuthor"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    book_tags: Mapped[list["BookTag"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )


class BookVersion(Base):
    """Versioned content for a book (PDF, thumbnail, metadata)."""

    __tablename__ = "book_versions"
    __table_args__ = (UniqueConstraint("book_id", "version_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # system: 1, 2, 3
    version_label: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # publisher: "1.0", "2.1"
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail: Mapped[str] = mapped_column(String(500), nullable=False)
    pdf_file: Mapped[str] = mapped_column(String(500), nullable=False)
    pdf_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    pdf_file_size_mb: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "DRAFT",
            "PENDING",
            "APPROVED",
            "REJECTED",
            "ARCHIVED",
            name="book_status_enum",
        ),
        nullable=False,
        default="DRAFT",
    )
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_resubmission: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    resubmission_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    total_downloads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    search_vector: Mapped[object | None] = mapped_column(
        TSVECTOR, nullable=True
    )  # managed by DB trigger
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    book: Mapped["Book"] = relationship(
        back_populates="versions", foreign_keys=[book_id]
    )
    reviewed_by: Mapped["User | None"] = relationship(
        foreign_keys=[reviewed_by_id]
    )
    action_logs: Mapped[list["BookVersionActionLog"]] = relationship(
        back_populates="book_version", cascade="all, delete-orphan"
    )


class BookAuthor(Base):
    """Join table linking a book to its authors."""

    __tablename__ = "book_authors"
    __table_args__ = (UniqueConstraint("book_id", "author_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    book: Mapped["Book"] = relationship(back_populates="book_authors")
    author: Mapped["Author"] = relationship()


class BookTag(Base):
    """Join table linking a book to its tags."""

    __tablename__ = "book_tags"
    __table_args__ = (UniqueConstraint("book_id", "tag_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    book: Mapped["Book"] = relationship(back_populates="book_tags")
    tag: Mapped["Tag"] = relationship()


class BookVersionActionLog(Base):
    """Immutable log of every action taken on a book version."""

    __tablename__ = "book_version_action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    book_version_id: Mapped[int] = mapped_column(
        ForeignKey("book_versions.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(
        Enum(
            "CREATED",
            "SUBMITTED",
            "APPROVED",
            "REJECTED",
            "ARCHIVED",
            "RESUBMITTED",
            name="book_action_enum",
        ),
        nullable=False,
    )
    performed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    performed_by_type: Mapped[str] = mapped_column(
        Enum(
            "publisher",
            "staff",
            "admin",
            "superadmin",
            name="book_actor_enum",
        ),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # no updated_at — immutable log

    book_version: Mapped["BookVersion"] = relationship(back_populates="action_logs")
    performed_by: Mapped["User | None"] = relationship(
        foreign_keys=[performed_by_id]
    )
