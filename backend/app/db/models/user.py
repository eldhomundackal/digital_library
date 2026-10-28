import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
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


class User(Base):
    """Core user account shared across all roles."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )  # USR-000001
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # null for OIDC
    role: Mapped[str] = mapped_column(
        Enum(
            "reader",
            "publisher",
            "staff",
            "admin",
            "superadmin",
            name="user_role_enum",
        ),
        nullable=False,
    )
    auth_provider: Mapped[str] = mapped_column(
        String(20), nullable=False, default="local"
    )  # local|oidc|oauth2
    idp_sub: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_super: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_first_login: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    reader_profile: Mapped["ReaderProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
    publisher_profile: Mapped["PublisherProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
    staff_profile: Mapped["StaffProfile | None"] = relationship(
        back_populates="user", uselist=False
    )


class ReaderProfile(Base):
    """Reader-specific profile data."""

    __tablename__ = "reader_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_of_birth: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # YYYY-MM-DD
    gender: Mapped[str | None] = mapped_column(
        Enum(
            "Male",
            "Female",
            "Other",
            "Prefer not to say",
            name="gender_enum",
        ),
        nullable=True,
    )
    country_id: Mapped[int | None] = mapped_column(
        ForeignKey("countries.id"), nullable=True
    )
    city_id: Mapped[int | None] = mapped_column(
        ForeignKey("cities.id"), nullable=True
    )
    language_id: Mapped[int | None] = mapped_column(
        ForeignKey("languages.id"), nullable=True
    )
    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reply_notifications: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    profile_completion: Mapped[int] = mapped_column(
        Integer, nullable=False, default=40
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="reader_profile")
    country: Mapped["Country | None"] = relationship(foreign_keys=[country_id])
    city: Mapped["City | None"] = relationship(foreign_keys=[city_id])
    preferred_language: Mapped["Language | None"] = relationship(
        foreign_keys=[language_id]
    )
    preferred_categories: Mapped[list["ReaderPreferredCategory"]] = relationship(
        back_populates="reader", cascade="all, delete-orphan"
    )
    preferred_tags: Mapped[list["ReaderPreferredTag"]] = relationship(
        back_populates="reader", cascade="all, delete-orphan"
    )


class ReaderPreferredCategory(Base):
    """Join table linking a reader to their preferred categories."""

    __tablename__ = "reader_preferred_categories"
    __table_args__ = (UniqueConstraint("reader_id", "category_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reader_id: Mapped[int] = mapped_column(
        ForeignKey("reader_profiles.id"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    reader: Mapped["ReaderProfile"] = relationship(
        back_populates="preferred_categories"
    )
    category: Mapped["Category"] = relationship()


class ReaderPreferredTag(Base):
    """Join table linking a reader to their preferred tags."""

    __tablename__ = "reader_preferred_tags"
    __table_args__ = (UniqueConstraint("reader_id", "tag_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reader_id: Mapped[int] = mapped_column(
        ForeignKey("reader_profiles.id"), nullable=False
    )
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    reader: Mapped["ReaderProfile"] = relationship(back_populates="preferred_tags")
    tag: Mapped["Tag"] = relationship()
