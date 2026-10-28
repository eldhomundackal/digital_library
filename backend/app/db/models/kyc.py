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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class KYCApplication(Base):
    """Publisher KYC application with document tracking."""

    __tablename__ = "kyc_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )  # KYC-000001
    publisher_id: Mapped[int] = mapped_column(
        ForeignKey("publisher_profiles.id"), unique=True, nullable=False
    )
    overall_status: Mapped[str] = mapped_column(
        Enum(
            "INCOMPLETE",
            "PENDING",
            "IN_REVIEW",
            "APPROVED",
            "REJECTED",
            "RESUBMITTED",
            name="kyc_overall_status_enum",
        ),
        nullable=False,
        default="INCOMPLETE",
    )
    terms_accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    terms_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    publisher: Mapped["PublisherProfile"] = relationship(
        back_populates="kyc_application"
    )
    reviewed_by: Mapped["User | None"] = relationship(
        foreign_keys=[reviewed_by_id]
    )
    documents: Mapped[list["KYCDocument"]] = relationship(
        back_populates="kyc_application", cascade="all, delete-orphan"
    )
    action_logs: Mapped[list["KYCActionLog"]] = relationship(
        back_populates="kyc_application", cascade="all, delete-orphan"
    )


class KYCDocument(Base):
    """Individual KYC document (one per document type per application)."""

    __tablename__ = "kyc_documents"
    __table_args__ = (UniqueConstraint("kyc_application_id", "document_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    kyc_application_id: Mapped[int] = mapped_column(
        ForeignKey("kyc_applications.id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(
        Enum(
            "government_id",
            "publishing_license",
            "business_registration",
            name="kyc_document_type_enum",
        ),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "NOT_UPLOADED",
            "UPLOADED",
            "PENDING",
            "APPROVED",
            "REJECTED",
            name="kyc_document_status_enum",
        ),
        nullable=False,
        default="NOT_UPLOADED",
    )
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size_mb: Mapped[float | None] = mapped_column(nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    kyc_application: Mapped["KYCApplication"] = relationship(
        back_populates="documents"
    )
    reviewed_by: Mapped["User | None"] = relationship(
        foreign_keys=[reviewed_by_id]
    )


class KYCActionLog(Base):
    """Immutable log of every action taken on a KYC application."""

    __tablename__ = "kyc_action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    kyc_application_id: Mapped[int] = mapped_column(
        ForeignKey("kyc_applications.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(
        Enum(
            "SUBMITTED",
            "APPROVED",
            "REJECTED",
            "RESUBMISSION_REQUESTED",
            "RESUBMITTED",
            "DOCUMENT_APPROVED",
            "DOCUMENT_REJECTED",
            name="kyc_action_enum",
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
            name="kyc_actor_enum",
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

    kyc_application: Mapped["KYCApplication"] = relationship(
        back_populates="action_logs"
    )
    performed_by: Mapped["User | None"] = relationship(
        foreign_keys=[performed_by_id]
    )
