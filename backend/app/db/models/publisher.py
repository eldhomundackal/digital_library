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


class PublisherProfile(Base):
    """Publisher-specific profile and KYC status."""

    __tablename__ = "publisher_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )  # PUB-000001
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    twitter: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin: Mapped[str | None] = mapped_column(String(500), nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(500), nullable=True)
    instagram: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    kyc_status: Mapped[str] = mapped_column(
        Enum(
            "INCOMPLETE",
            "PENDING",
            "IN_REVIEW",
            "APPROVED",
            "REJECTED",
            "RESUBMITTED",
            name="publisher_kyc_status_enum",
        ),
        nullable=False,
        default="INCOMPLETE",
    )
    reply_notifications: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
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

    user: Mapped["User"] = relationship(back_populates="publisher_profile")
    kyc_application: Mapped["KYCApplication | None"] = relationship(
        back_populates="publisher", uselist=False
    )
    books: Mapped[list["Book"]] = relationship(back_populates="publisher")


class StaffProfile(Base):
    """Staff/admin profile with permission rows."""

    __tablename__ = "staff_profiles"

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

    user: Mapped["User"] = relationship(back_populates="staff_profile")
    permissions: Mapped[list["StaffPermission"]] = relationship(
        back_populates="staff", cascade="all, delete-orphan"
    )


class StaffPermission(Base):
    """Individual permission granted to a staff member."""

    __tablename__ = "staff_permissions"
    __table_args__ = (UniqueConstraint("staff_id", "permission"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    staff_id: Mapped[int] = mapped_column(
        ForeignKey("staff_profiles.id"), nullable=False
    )
    permission: Mapped[str] = mapped_column(
        Enum(
            "manage_books",
            "manage_publishers",
            "manage_users",
            "manage_reviews",
            "manage_categories",
            "manage_tags",
            "manage_utils",
            "view_analytics",
            name="staff_permission_enum",
        ),
        nullable=False,
    )
    granted_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    staff: Mapped["StaffProfile"] = relationship(back_populates="permissions")
    granted_by: Mapped["User"] = relationship(foreign_keys=[granted_by_id])
