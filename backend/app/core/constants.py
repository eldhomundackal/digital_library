from enum import StrEnum


class UserRole(StrEnum):
    """All user roles in the system."""

    READER = "reader"
    PUBLISHER = "publisher"
    STAFF = "staff"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class KYCStatus(StrEnum):
    """KYC application lifecycle statuses."""

    INCOMPLETE = "INCOMPLETE"
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RESUBMITTED = "RESUBMITTED"


class BookStatus(StrEnum):
    """Book version lifecycle statuses."""

    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class DocumentType(StrEnum):
    """KYC document types required for publisher onboarding."""

    GOVERNMENT_ID = "government_id"
    PUBLISHING_LICENSE = "publishing_license"
    BUSINESS_REGISTRATION = "business_registration"


class StaffPermission(StrEnum):
    """Permissions that can be granted to staff members."""

    MANAGE_BOOKS = "manage_books"
    MANAGE_PUBLISHERS = "manage_publishers"
    MANAGE_USERS = "manage_users"
    MANAGE_REVIEWS = "manage_reviews"
    MANAGE_CATEGORIES = "manage_categories"
    MANAGE_TAGS = "manage_tags"
    MANAGE_UTILS = "manage_utils"
    VIEW_ANALYTICS = "view_analytics"


class NotificationType(StrEnum):
    """All in-app notification types."""

    OTP_EMAIL_VERIFICATION = "OTP_EMAIL_VERIFICATION"
    OTP_PASSWORD_RESET = "OTP_PASSWORD_RESET"
    WELCOME = "WELCOME"
    KYC_SUBMITTED = "KYC_SUBMITTED"
    KYC_APPROVED = "KYC_APPROVED"
    KYC_REJECTED = "KYC_REJECTED"
    KYC_RESUBMISSION_REQUESTED = "KYC_RESUBMISSION_REQUESTED"
    KYC_NEW_APPLICATION = "KYC_NEW_APPLICATION"
    BOOK_SUBMITTED = "BOOK_SUBMITTED"
    BOOK_APPROVED = "BOOK_APPROVED"
    BOOK_REJECTED = "BOOK_REJECTED"
    BOOK_RESUBMITTED = "BOOK_RESUBMITTED"
    REVIEW_REPLY = "REVIEW_REPLY"
    PUBLISHER_RESPONSE = "PUBLISHER_RESPONSE"
    DOWNLOAD_LIMIT_WARNING = "DOWNLOAD_LIMIT_WARNING"
    COMMENT_REPORTED = "COMMENT_REPORTED"
    NEW_PUBLISHER_REGISTRATION = "NEW_PUBLISHER_REGISTRATION"
