# Import all models here so Alembic autogenerate detects them
from app.db.models.audit import ActivityFeed, AuditLog
from app.db.models.author import Author
from app.db.models.book import Book, BookAuthor, BookTag, BookVersion, BookVersionActionLog
from app.db.models.category import Category, Tag
from app.db.models.download import DownloadLog
from app.db.models.kyc import KYCActionLog, KYCApplication, KYCDocument
from app.db.models.notification import Notification
from app.db.models.publisher import PublisherProfile, StaffPermission, StaffProfile
from app.db.models.review import Rating, Review, ReviewReply, ReviewReport
from app.db.models.user import (
    ReaderPreferredCategory,
    ReaderPreferredTag,
    ReaderProfile,
    User,
)
from app.db.models.utils import City, Country, Language

__all__ = [
    "User",
    "ReaderProfile",
    "ReaderPreferredCategory",
    "ReaderPreferredTag",
    "PublisherProfile",
    "StaffProfile",
    "StaffPermission",
    "Country",
    "City",
    "Language",
    "KYCApplication",
    "KYCDocument",
    "KYCActionLog",
    "Category",
    "Tag",
    "Author",
    "Book",
    "BookVersion",
    "BookAuthor",
    "BookTag",
    "BookVersionActionLog",
    "Rating",
    "Review",
    "ReviewReply",
    "ReviewReport",
    "DownloadLog",
    "Notification",
    "AuditLog",
    "ActivityFeed",
]
