import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DownloadLog(Base):
    """Immutable record of every book download event."""

    __tablename__ = "download_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )  # DL-000001
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    book_version_id: Mapped[int] = mapped_column(
        ForeignKey("book_versions.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # soft-hide from history
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # no updated_at — immutable event log

    book: Mapped["Book"] = relationship()
    book_version: Mapped["BookVersion"] = relationship()
    user: Mapped["User"] = relationship()
