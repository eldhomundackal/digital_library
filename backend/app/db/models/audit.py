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
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    """Immutable record of every admin/staff action."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    performed_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    target_type: Mapped[str] = mapped_column(
        Enum(
            "book",
            "publisher",
            "user",
            "review",
            "tag",
            "category",
            "author",
            "utils",
            name="audit_target_type_enum",
        ),
        nullable=False,
    )
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_label: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # no updated_at — immutable

    performed_by: Mapped["User"] = relationship(foreign_keys=[performed_by_id])


class ActivityFeed(Base):
    """Curated human-readable stream for the admin operations panel."""

    __tablename__ = "activity_feed"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(
        Enum(
            "actionable",
            "informational",
            name="activity_category_enum",
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    actor_type: Mapped[str] = mapped_column(
        Enum(
            "publisher",
            "reader",
            "staff",
            "admin",
            "superadmin",
            name="activity_actor_enum",
        ),
        nullable=False,
    )
    actor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
