# ORM Models

Full SQLAlchemy 2.0 async ORM models for all 28 tables. Every model imports from `app/db/base.py`. Copy each group into its matching file under `app/db/models/`.

---

## `app/db/base.py`

```python
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)
```

---

## `app/db/session.py`

```python
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

---

## `app/db/models/user.py` — Users & Profiles

```python
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Enum,
    ForeignKey, Integer, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id:                Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:              Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    number:            Mapped[str]           = mapped_column(String(20), unique=True, nullable=False)          # USR-000001
    email:             Mapped[str]           = mapped_column(String(255), unique=True, nullable=False)
    hashed_password:   Mapped[str | None]    = mapped_column(String(255), nullable=True)                      # null for OIDC
    role:              Mapped[str]           = mapped_column(
                                                  Enum("reader", "publisher", "staff", "admin", "superadmin",
                                                       name="user_role_enum"),
                                                  nullable=False,
                                              )
    auth_provider:     Mapped[str]           = mapped_column(String(20), nullable=False, default="local")     # local|oidc|oauth2
    idp_sub:           Mapped[str | None]    = mapped_column(String(255), nullable=True)
    is_super:          Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    is_email_verified: Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    is_active:         Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    is_first_login:    Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    last_login_at:     Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at:        Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:        Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    reader_profile:    Mapped["ReaderProfile | None"]    = relationship(back_populates="user", uselist=False)
    publisher_profile: Mapped["PublisherProfile | None"] = relationship(back_populates="user", uselist=False)
    staff_profile:     Mapped["StaffProfile | None"]     = relationship(back_populates="user", uselist=False)


class ReaderProfile(Base):
    __tablename__ = "reader_profiles"

    id:                   Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:                 Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id:              Mapped[int]           = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    first_name:           Mapped[str]           = mapped_column(String(100), nullable=False)
    last_name:            Mapped[str]           = mapped_column(String(100), nullable=False)
    avatar:               Mapped[str | None]    = mapped_column(String(500), nullable=True)
    bio:                  Mapped[str | None]    = mapped_column(Text, nullable=True)
    date_of_birth:        Mapped[str | None]    = mapped_column(String(10), nullable=True)                    # YYYY-MM-DD
    gender:               Mapped[str | None]    = mapped_column(
                                                      Enum("Male", "Female", "Other", "Prefer not to say",
                                                           name="gender_enum"),
                                                      nullable=True,
                                                  )
    country_id:           Mapped[int | None]    = mapped_column(ForeignKey("countries.id"), nullable=True)
    city_id:              Mapped[int | None]    = mapped_column(ForeignKey("cities.id"), nullable=True)
    language_id:          Mapped[int | None]    = mapped_column(ForeignKey("languages.id"), nullable=True)
    occupation:           Mapped[str | None]    = mapped_column(String(100), nullable=True)
    reply_notifications:  Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    profile_completion:   Mapped[int]           = mapped_column(Integer, nullable=False, default=40)
    created_at:           Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:           Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user:                 Mapped["User"]                           = relationship(back_populates="reader_profile")
    country:              Mapped["Country | None"]                 = relationship(foreign_keys=[country_id])
    city:                 Mapped["City | None"]                    = relationship(foreign_keys=[city_id])
    preferred_language:   Mapped["Language | None"]               = relationship(foreign_keys=[language_id])
    preferred_categories: Mapped[list["ReaderPreferredCategory"]] = relationship(back_populates="reader", cascade="all, delete-orphan")
    preferred_tags:       Mapped[list["ReaderPreferredTag"]]       = relationship(back_populates="reader", cascade="all, delete-orphan")


class ReaderPreferredCategory(Base):
    __tablename__ = "reader_preferred_categories"
    __table_args__ = (UniqueConstraint("reader_id", "category_id"),)

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    reader_id:   Mapped[int]      = mapped_column(ForeignKey("reader_profiles.id"), nullable=False)
    category_id: Mapped[int]      = mapped_column(ForeignKey("categories.id"), nullable=False)
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    reader:   Mapped["ReaderProfile"] = relationship(back_populates="preferred_categories")
    category: Mapped["Category"]      = relationship()


class ReaderPreferredTag(Base):
    __tablename__ = "reader_preferred_tags"
    __table_args__ = (UniqueConstraint("reader_id", "tag_id"),)

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    reader_id:  Mapped[int]      = mapped_column(ForeignKey("reader_profiles.id"), nullable=False)
    tag_id:     Mapped[int]      = mapped_column(ForeignKey("tags.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    reader: Mapped["ReaderProfile"] = relationship(back_populates="preferred_tags")
    tag:    Mapped["Tag"]           = relationship()
```

---

## `app/db/models/publisher.py` — Publisher & Staff

```python
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey,
    Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PublisherProfile(Base):
    __tablename__ = "publisher_profiles"

    id:                  Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:                Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    number:              Mapped[str]           = mapped_column(String(20), unique=True, nullable=False)     # PUB-000001
    user_id:             Mapped[int]           = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    display_name:        Mapped[str]           = mapped_column(String(255), nullable=False)
    bio:                 Mapped[str | None]    = mapped_column(Text, nullable=True)
    logo:                Mapped[str | None]    = mapped_column(String(500), nullable=True)
    website:             Mapped[str | None]    = mapped_column(String(500), nullable=True)
    twitter:             Mapped[str | None]    = mapped_column(String(500), nullable=True)
    linkedin:            Mapped[str | None]    = mapped_column(String(500), nullable=True)
    facebook:            Mapped[str | None]    = mapped_column(String(500), nullable=True)
    instagram:           Mapped[str | None]    = mapped_column(String(500), nullable=True)
    is_verified:         Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    kyc_status:          Mapped[str]           = mapped_column(
                                                     Enum("INCOMPLETE", "PENDING", "IN_REVIEW",
                                                          "APPROVED", "REJECTED", "RESUBMITTED",
                                                          name="publisher_kyc_status_enum"),
                                                     nullable=False, default="INCOMPLETE",
                                                 )
    reply_notifications: Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    is_active:           Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    deleted_at:          Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:          Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:          Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user:            Mapped["User"]                  = relationship(back_populates="publisher_profile")
    kyc_application: Mapped["KYCApplication | None"] = relationship(back_populates="publisher", uselist=False)
    books:           Mapped[list["Book"]]             = relationship(back_populates="publisher")


class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:       Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id:    Mapped[int]           = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    first_name: Mapped[str]           = mapped_column(String(100), nullable=False)
    last_name:  Mapped[str]           = mapped_column(String(100), nullable=False)
    is_active:  Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    deleted_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user:        Mapped["User"]                  = relationship(back_populates="staff_profile")
    permissions: Mapped[list["StaffPermission"]] = relationship(back_populates="staff", cascade="all, delete-orphan")


class StaffPermission(Base):
    __tablename__ = "staff_permissions"
    __table_args__ = (UniqueConstraint("staff_id", "permission"),)

    id:            Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    staff_id:      Mapped[int]      = mapped_column(ForeignKey("staff_profiles.id"), nullable=False)
    permission:    Mapped[str]      = mapped_column(
                                          Enum(
                                              "manage_books", "manage_publishers", "manage_users",
                                              "manage_reviews", "manage_categories", "manage_tags",
                                              "manage_utils", "view_analytics",
                                              name="staff_permission_enum",
                                          ),
                                          nullable=False,
                                      )
    granted_by_id: Mapped[int]      = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    staff:      Mapped["StaffProfile"] = relationship(back_populates="permissions")
    granted_by: Mapped["User"]         = relationship(foreign_keys=[granted_by_id])
```

---

## `app/db/models/utils.py` — Countries, Cities, Languages

```python
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Country(Base):
    __tablename__ = "countries"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:       Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name:       Mapped[str]           = mapped_column(String(100), nullable=False)
    iso_code:   Mapped[str]           = mapped_column(String(3), unique=True, nullable=False)
    phone_code: Mapped[str | None]    = mapped_column(String(10), nullable=True)
    flag:       Mapped[str | None]    = mapped_column(String(10), nullable=True)
    is_seeded:  Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    is_active:  Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    deleted_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    cities: Mapped[list["City"]] = relationship(back_populates="country")


class City(Base):
    __tablename__ = "cities"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:       Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    country_id: Mapped[int]           = mapped_column(ForeignKey("countries.id"), nullable=False)
    name:       Mapped[str]           = mapped_column(String(100), nullable=False)
    state:      Mapped[str | None]    = mapped_column(String(100), nullable=True)
    is_seeded:  Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    is_active:  Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    deleted_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    country: Mapped["Country"] = relationship(back_populates="cities")


class Language(Base):
    __tablename__ = "languages"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:       Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name:       Mapped[str]           = mapped_column(String(100), nullable=False)
    iso_code:   Mapped[str]           = mapped_column(String(10), unique=True, nullable=False)
    is_seeded:  Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    is_active:  Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    deleted_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
```

---

## `app/db/models/kyc.py` — KYC Application & Documents

```python
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey,
    Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class KYCApplication(Base):
    __tablename__ = "kyc_applications"

    id:               Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:             Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    number:           Mapped[str]           = mapped_column(String(20), unique=True, nullable=False)      # KYC-000001
    publisher_id:     Mapped[int]           = mapped_column(ForeignKey("publisher_profiles.id"), unique=True, nullable=False)
    overall_status:   Mapped[str]           = mapped_column(
                                                 Enum("INCOMPLETE", "PENDING", "IN_REVIEW",
                                                      "APPROVED", "REJECTED", "RESUBMITTED",
                                                      name="kyc_overall_status_enum"),
                                                 nullable=False, default="INCOMPLETE",
                                             )
    terms_accepted:   Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    terms_accepted_at:Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at:     Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at:      Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_id:   Mapped[int | None]    = mapped_column(ForeignKey("users.id"), nullable=True)
    rejection_reason: Mapped[str | None]    = mapped_column(Text, nullable=True)
    created_at:       Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:       Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    publisher:   Mapped["PublisherProfile"]    = relationship(back_populates="kyc_application")
    reviewed_by: Mapped["User | None"]         = relationship(foreign_keys=[reviewed_by_id])
    documents:   Mapped[list["KYCDocument"]]   = relationship(back_populates="kyc_application", cascade="all, delete-orphan")
    action_logs: Mapped[list["KYCActionLog"]]  = relationship(back_populates="kyc_application", cascade="all, delete-orphan")


class KYCDocument(Base):
    __tablename__ = "kyc_documents"
    __table_args__ = (UniqueConstraint("kyc_application_id", "document_type"),)

    id:                 Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:               Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    kyc_application_id: Mapped[int]           = mapped_column(ForeignKey("kyc_applications.id"), nullable=False)
    document_type:      Mapped[str]           = mapped_column(
                                                    Enum("government_id", "publishing_license", "business_registration",
                                                         name="kyc_document_type_enum"),
                                                    nullable=False,
                                                )
    status:             Mapped[str]           = mapped_column(
                                                    Enum("NOT_UPLOADED", "UPLOADED", "PENDING", "APPROVED", "REJECTED",
                                                         name="kyc_document_status_enum"),
                                                    nullable=False, default="NOT_UPLOADED",
                                                )
    file_url:           Mapped[str | None]    = mapped_column(String(500), nullable=True)
    file_name:          Mapped[str | None]    = mapped_column(String(255), nullable=True)
    file_size_mb:       Mapped[float | None]  = mapped_column(nullable=True)
    rejection_reason:   Mapped[str | None]    = mapped_column(Text, nullable=True)
    reviewed_at:        Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_id:     Mapped[int | None]    = mapped_column(ForeignKey("users.id"), nullable=True)
    uploaded_at:        Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:         Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:         Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    kyc_application: Mapped["KYCApplication"] = relationship(back_populates="documents")
    reviewed_by:     Mapped["User | None"]     = relationship(foreign_keys=[reviewed_by_id])


class KYCActionLog(Base):
    __tablename__ = "kyc_action_logs"

    id:                 Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:               Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    kyc_application_id: Mapped[int]           = mapped_column(ForeignKey("kyc_applications.id"), nullable=False)
    action:             Mapped[str]           = mapped_column(
                                                    Enum("SUBMITTED", "APPROVED", "REJECTED",
                                                         "RESUBMISSION_REQUESTED", "RESUBMITTED",
                                                         "DOCUMENT_APPROVED", "DOCUMENT_REJECTED",
                                                         name="kyc_action_enum"),
                                                    nullable=False,
                                                )
    performed_by_id:   Mapped[int | None]    = mapped_column(ForeignKey("users.id"), nullable=True)
    performed_by_type: Mapped[str]           = mapped_column(
                                                    Enum("publisher", "staff", "admin", "superadmin",
                                                         name="kyc_actor_enum"),
                                                    nullable=False,
                                                )
    note:              Mapped[str | None]    = mapped_column(Text, nullable=True)
    metadata_:         Mapped[dict | None]   = mapped_column("metadata", JSONB, nullable=True)
    created_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # no updated_at — immutable log

    kyc_application: Mapped["KYCApplication"] = relationship(back_populates="action_logs")
    performed_by:    Mapped["User | None"]     = relationship(foreign_keys=[performed_by_id])
```

---

## `app/db/models/category.py` — Categories & Tags

```python
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey,
    Integer, String, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Category(Base):
    __tablename__ = "categories"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:        Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name:        Mapped[str]           = mapped_column(String(100), unique=True, nullable=False)
    slug:        Mapped[str]           = mapped_column(String(100), unique=True, nullable=False)
    total_books: Mapped[int]           = mapped_column(Integer, nullable=False, default=0)
    is_active:   Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    deleted_at:  Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:  Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class Tag(Base):
    __tablename__ = "tags"

    id:              Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:            Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name:            Mapped[str]           = mapped_column(String(100), unique=True, nullable=False)
    slug:            Mapped[str]           = mapped_column(String(100), unique=True, nullable=False)
    status:          Mapped[str]           = mapped_column(
                                                Enum("PENDING", "APPROVED", "REJECTED", name="tag_status_enum"),
                                                nullable=False, default="PENDING",
                                            )
    suggested_by_id: Mapped[int | None]    = mapped_column(ForeignKey("publisher_profiles.id"), nullable=True)
    reviewed_by_id:  Mapped[int | None]    = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at:     Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_books:     Mapped[int]           = mapped_column(Integer, nullable=False, default=0)
    is_active:       Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    deleted_at:      Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:      Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    suggested_by: Mapped["PublisherProfile | None"] = relationship(foreign_keys=[suggested_by_id])
    reviewed_by:  Mapped["User | None"]             = relationship(foreign_keys=[reviewed_by_id])
```

---

## `app/db/models/author.py` — Authors

```python
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Author(Base):
    __tablename__ = "authors"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:          Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    first_name:    Mapped[str]           = mapped_column(String(100), nullable=False)
    last_name:     Mapped[str]           = mapped_column(String(100), nullable=False)
    bio:           Mapped[str | None]    = mapped_column(Text, nullable=True)
    avatar:        Mapped[str | None]    = mapped_column(String(500), nullable=True)
    created_by_id: Mapped[int | None]    = mapped_column(ForeignKey("publisher_profiles.id"), nullable=True)
    is_active:     Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    deleted_at:    Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:    Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:    Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    created_by: Mapped["PublisherProfile | None"] = relationship(foreign_keys=[created_by_id])
```

---

## `app/db/models/book.py` — Books & Versions

```python
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey,
    Integer, Numeric, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Book(Base):
    __tablename__ = "books"

    id:                 Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:               Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    number:             Mapped[str]           = mapped_column(String(20), unique=True, nullable=False)     # BK-000001
    publisher_id:       Mapped[int]           = mapped_column(ForeignKey("publisher_profiles.id"), nullable=False)
    category_id:        Mapped[int]           = mapped_column(ForeignKey("categories.id"), nullable=False)
    language_id:        Mapped[int]           = mapped_column(ForeignKey("languages.id"), nullable=False)
    title:              Mapped[str]           = mapped_column(String(500), nullable=False)
    current_version_id: Mapped[int | None]    = mapped_column(ForeignKey("book_versions.id", use_alter=True), nullable=True)
    average_rating:     Mapped[float]         = mapped_column(Numeric(3, 1), nullable=False, default=0.0)
    total_ratings:      Mapped[int]           = mapped_column(Integer, nullable=False, default=0)
    total_downloads:    Mapped[int]           = mapped_column(Integer, nullable=False, default=0)
    is_active:          Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    deleted_at:         Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:         Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:         Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    publisher:       Mapped["PublisherProfile"]       = relationship(back_populates="books", foreign_keys=[publisher_id])
    category:        Mapped["Category"]               = relationship()
    language:        Mapped["Language"]               = relationship()
    current_version: Mapped["BookVersion | None"]     = relationship(foreign_keys=[current_version_id], post_update=True)
    versions:        Mapped[list["BookVersion"]]      = relationship(back_populates="book", foreign_keys="BookVersion.book_id", cascade="all, delete-orphan")
    book_authors:    Mapped[list["BookAuthor"]]        = relationship(back_populates="book", cascade="all, delete-orphan")
    book_tags:       Mapped[list["BookTag"]]           = relationship(back_populates="book", cascade="all, delete-orphan")


class BookVersion(Base):
    __tablename__ = "book_versions"
    __table_args__ = (UniqueConstraint("book_id", "version_number"),)

    id:                  Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:                Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    book_id:             Mapped[int]           = mapped_column(ForeignKey("books.id"), nullable=False)
    version_number:      Mapped[int]           = mapped_column(Integer, nullable=False)                  # system: 1, 2, 3
    version_label:       Mapped[str]           = mapped_column(String(20), nullable=False)               # publisher: "1.0", "2.1"
    title:               Mapped[str]           = mapped_column(String(500), nullable=False)
    description:         Mapped[str]           = mapped_column(Text, nullable=False)
    isbn:                Mapped[str | None]    = mapped_column(String(20), nullable=True)
    page_count:          Mapped[int | None]    = mapped_column(Integer, nullable=True)
    publication_year:    Mapped[int | None]    = mapped_column(Integer, nullable=True)
    thumbnail:           Mapped[str]           = mapped_column(String(500), nullable=False)
    pdf_file:            Mapped[str]           = mapped_column(String(500), nullable=False)
    pdf_file_name:       Mapped[str]           = mapped_column(String(255), nullable=False)
    pdf_file_size_mb:    Mapped[float]         = mapped_column(Numeric(10, 2), nullable=False)
    status:              Mapped[str]           = mapped_column(
                                                     Enum("DRAFT", "PENDING", "APPROVED", "REJECTED", "ARCHIVED",
                                                          name="book_status_enum"),
                                                     nullable=False, default="DRAFT",
                                                 )
    is_current:          Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    rejection_reason:    Mapped[str | None]    = mapped_column(Text, nullable=True)
    is_resubmission:     Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    resubmission_count:  Mapped[int]           = mapped_column(Integer, nullable=False, default=0)
    submitted_at:        Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at:         Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at:         Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at:         Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_id:      Mapped[int | None]    = mapped_column(ForeignKey("users.id"), nullable=True)
    total_downloads:     Mapped[int]           = mapped_column(Integer, nullable=False, default=0)
    search_vector:       Mapped[object | None] = mapped_column(TSVECTOR, nullable=True)                  # managed by DB trigger
    created_at:          Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:          Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    book:        Mapped["Book"]                       = relationship(back_populates="versions", foreign_keys=[book_id])
    reviewed_by: Mapped["User | None"]                = relationship(foreign_keys=[reviewed_by_id])
    action_logs: Mapped[list["BookVersionActionLog"]] = relationship(back_populates="book_version", cascade="all, delete-orphan")


class BookAuthor(Base):
    __tablename__ = "book_authors"
    __table_args__ = (UniqueConstraint("book_id", "author_id"),)

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id:    Mapped[int]      = mapped_column(ForeignKey("books.id"), nullable=False)
    author_id:  Mapped[int]      = mapped_column(ForeignKey("authors.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    book:   Mapped["Book"]   = relationship(back_populates="book_authors")
    author: Mapped["Author"] = relationship()


class BookTag(Base):
    __tablename__ = "book_tags"
    __table_args__ = (UniqueConstraint("book_id", "tag_id"),)

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id:    Mapped[int]      = mapped_column(ForeignKey("books.id"), nullable=False)
    tag_id:     Mapped[int]      = mapped_column(ForeignKey("tags.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    book: Mapped["Book"] = relationship(back_populates="book_tags")
    tag:  Mapped["Tag"]  = relationship()


class BookVersionActionLog(Base):
    __tablename__ = "book_version_action_logs"

    id:                 Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:               Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    book_version_id:    Mapped[int]           = mapped_column(ForeignKey("book_versions.id"), nullable=False)
    action:             Mapped[str]           = mapped_column(
                                                    Enum("CREATED", "SUBMITTED", "APPROVED", "REJECTED",
                                                         "ARCHIVED", "RESUBMITTED",
                                                         name="book_action_enum"),
                                                    nullable=False,
                                                )
    performed_by_id:   Mapped[int | None]    = mapped_column(ForeignKey("users.id"), nullable=True)
    performed_by_type: Mapped[str]           = mapped_column(
                                                    Enum("publisher", "staff", "admin", "superadmin",
                                                         name="book_actor_enum"),
                                                    nullable=False,
                                                )
    note:              Mapped[str | None]    = mapped_column(Text, nullable=True)
    metadata_:         Mapped[dict | None]   = mapped_column("metadata", JSONB, nullable=True)
    created_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # no updated_at — immutable log

    book_version: Mapped["BookVersion"] = relationship(back_populates="action_logs")
    performed_by: Mapped["User | None"] = relationship(foreign_keys=[performed_by_id])
```

---

## `app/db/models/review.py` — Ratings & Reviews

```python
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Enum,
    ForeignKey, Integer, String, Text,
    UniqueConstraint, func,
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

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:       Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    book_id:    Mapped[int]           = mapped_column(ForeignKey("books.id"), nullable=False)
    user_id:    Mapped[int]           = mapped_column(ForeignKey("users.id"), nullable=False)
    score:      Mapped[int]           = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    book:   Mapped["Book"] = relationship()
    user:   Mapped["User"] = relationship()
    review: Mapped["Review | None"] = relationship(back_populates="rating", uselist=False)


class Review(Base):
    """Ratings that also have a comment — shown in the reviews list."""
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("book_id", "user_id"),)

    id:                   Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:                 Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    number:               Mapped[str]           = mapped_column(String(20), unique=True, nullable=False)   # REV-000001
    book_id:              Mapped[int]           = mapped_column(ForeignKey("books.id"), nullable=False)
    user_id:              Mapped[int]           = mapped_column(ForeignKey("users.id"), nullable=False)
    rating_id:            Mapped[int]           = mapped_column(ForeignKey("ratings.id"), nullable=False)
    comment:              Mapped[str]           = mapped_column(Text, nullable=False)
    is_edited:            Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    is_publisher_response:Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    reply_count:          Mapped[int]           = mapped_column(Integer, nullable=False, default=0)
    report_count:         Mapped[int]           = mapped_column(Integer, nullable=False, default=0)
    is_active:            Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    deleted_at:           Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:           Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:           Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    book:    Mapped["Book"]               = relationship()
    user:    Mapped["User"]               = relationship()
    rating:  Mapped["Rating"]             = relationship(back_populates="review")
    replies: Mapped[list["ReviewReply"]]  = relationship(back_populates="review", cascade="all, delete-orphan")
    reports: Mapped[list["ReviewReport"]] = relationship(back_populates="review", cascade="all, delete-orphan")


class ReviewReply(Base):
    __tablename__ = "review_replies"

    id:                    Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:                  Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    review_id:             Mapped[int]           = mapped_column(ForeignKey("reviews.id"), nullable=False)
    user_id:               Mapped[int]           = mapped_column(ForeignKey("users.id"), nullable=False)
    comment:               Mapped[str]           = mapped_column(Text, nullable=False)
    is_publisher_response: Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    is_edited:             Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    is_active:             Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    deleted_at:            Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:            Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:            Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    review:  Mapped["Review"] = relationship(back_populates="replies")
    user:    Mapped["User"]   = relationship()
    reports: Mapped[list["ReviewReport"]] = relationship(back_populates="reply")


class ReviewReport(Base):
    __tablename__ = "review_reports"
    __table_args__ = (
        CheckConstraint(
            "(review_id IS NOT NULL AND reply_id IS NULL) OR (review_id IS NULL AND reply_id IS NOT NULL)",
            name="review_or_reply_check",
        ),
    )

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:           Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    review_id:      Mapped[int | None]    = mapped_column(ForeignKey("reviews.id"), nullable=True)
    reply_id:       Mapped[int | None]    = mapped_column(ForeignKey("review_replies.id"), nullable=True)
    reported_by_id: Mapped[int]           = mapped_column(ForeignKey("users.id"), nullable=False)
    reason:         Mapped[str]           = mapped_column(
                                                Enum("SPAM", "OFFENSIVE", "MISLEADING", "OTHER",
                                                     name="report_reason_enum"),
                                                nullable=False,
                                            )
    note:           Mapped[str | None]    = mapped_column(Text, nullable=True)
    status:         Mapped[str]           = mapped_column(
                                                Enum("PENDING", "REVIEWED", "DISMISSED",
                                                     name="report_status_enum"),
                                                nullable=False, default="PENDING",
                                            )
    reviewed_by_id: Mapped[int | None]    = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at:    Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:     Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    review:      Mapped["Review | None"]      = relationship(back_populates="reports", foreign_keys=[review_id])
    reply:       Mapped["ReviewReply | None"] = relationship(back_populates="reports", foreign_keys=[reply_id])
    reported_by: Mapped["User"]              = relationship(foreign_keys=[reported_by_id])
    reviewed_by: Mapped["User | None"]       = relationship(foreign_keys=[reviewed_by_id])
```

---

## `app/db/models/download.py` — Download Logs

```python
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class DownloadLog(Base):
    __tablename__ = "download_logs"

    id:              Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:            Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    number:          Mapped[str]           = mapped_column(String(20), unique=True, nullable=False)       # DL-000001
    book_id:         Mapped[int]           = mapped_column(ForeignKey("books.id"), nullable=False)
    book_version_id: Mapped[int]           = mapped_column(ForeignKey("book_versions.id"), nullable=False)
    user_id:         Mapped[int]           = mapped_column(ForeignKey("users.id"), nullable=False)
    is_deleted:      Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)       # soft-hide from history
    deleted_at:      Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    downloaded_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # no updated_at — immutable event log

    book:         Mapped["Book"]        = relationship()
    book_version: Mapped["BookVersion"] = relationship()
    user:         Mapped["User"]        = relationship()
```

---

## `app/db/models/notification.py` — Notifications

```python
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:        Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id:     Mapped[int]           = mapped_column(ForeignKey("users.id"), nullable=False)
    type:        Mapped[str]           = mapped_column(String(50), nullable=False)
    title:       Mapped[str]           = mapped_column(String(255), nullable=False)
    message:     Mapped[str]           = mapped_column(Text, nullable=False)
    group_key:   Mapped[str | None]    = mapped_column(String(255), nullable=True)  # e.g. "review_reply:{review_id}"
    group_count: Mapped[int]           = mapped_column(Integer, nullable=False, default=1)
    is_grouped:  Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    is_read:     Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    read_at:     Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    data:        Mapped[dict | None]   = mapped_column(JSONB, nullable=True)        # flexible payload per type
    expires_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False)  # created_at + 7 days
    created_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:  Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user: Mapped["User"] = relationship()
```

---

## `app/db/models/audit.py` — Audit Log & Activity Feed

```python
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AuditLog(Base):
    """Immutable record of every admin/staff action."""
    __tablename__ = "audit_logs"

    id:               Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:             Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    action:           Mapped[str]           = mapped_column(String(50), nullable=False)
    performed_by_id:  Mapped[int]           = mapped_column(ForeignKey("users.id"), nullable=False)
    target_type:      Mapped[str]           = mapped_column(
                                                  Enum("book", "publisher", "user", "review",
                                                       "tag", "category", "author", "utils",
                                                       name="audit_target_type_enum"),
                                                  nullable=False,
                                              )
    target_id:        Mapped[int]           = mapped_column(Integer, nullable=False)
    target_label:     Mapped[str]           = mapped_column(String(255), nullable=False)
    metadata_:        Mapped[dict | None]   = mapped_column("metadata", JSONB, nullable=True)
    note:             Mapped[str | None]    = mapped_column(Text, nullable=True)
    ip_address:       Mapped[str | None]    = mapped_column(String(45), nullable=True)
    performed_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # no updated_at — immutable

    performed_by: Mapped["User"] = relationship(foreign_keys=[performed_by_id])


class ActivityFeed(Base):
    """Curated human-readable stream for the admin operations panel."""
    __tablename__ = "activity_feed"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:       Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    type:       Mapped[str]           = mapped_column(String(50), nullable=False)
    category:   Mapped[str]           = mapped_column(
                                            Enum("actionable", "informational", name="activity_category_enum"),
                                            nullable=False,
                                        )
    title:      Mapped[str]           = mapped_column(String(255), nullable=False)
    message:    Mapped[str]           = mapped_column(Text, nullable=False)
    action_url: Mapped[str | None]    = mapped_column(String(500), nullable=True)
    actor_type: Mapped[str]           = mapped_column(
                                            Enum("publisher", "reader", "staff", "admin", "superadmin",
                                                 name="activity_actor_enum"),
                                            nullable=False,
                                        )
    actor_id:   Mapped[int]           = mapped_column(Integer, nullable=False)
    actor_name: Mapped[str]           = mapped_column(String(255), nullable=False)
    is_read:    Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    read_at:    Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
```

---

## `app/db/models/__init__.py` — Export all models

```python
# Import all models here so Alembic autogenerate detects them
from app.db.models.user import (
    User, ReaderProfile, ReaderPreferredCategory, ReaderPreferredTag
)
from app.db.models.publisher import PublisherProfile, StaffProfile, StaffPermission
from app.db.models.utils import Country, City, Language
from app.db.models.kyc import KYCApplication, KYCDocument, KYCActionLog
from app.db.models.category import Category, Tag
from app.db.models.author import Author
from app.db.models.book import Book, BookVersion, BookAuthor, BookTag, BookVersionActionLog
from app.db.models.review import Rating, Review, ReviewReply, ReviewReport
from app.db.models.download import DownloadLog
from app.db.models.notification import Notification
from app.db.models.audit import AuditLog, ActivityFeed

__all__ = [
    "User", "ReaderProfile", "ReaderPreferredCategory", "ReaderPreferredTag",
    "PublisherProfile", "StaffProfile", "StaffPermission",
    "Country", "City", "Language",
    "KYCApplication", "KYCDocument", "KYCActionLog",
    "Category", "Tag",
    "Author",
    "Book", "BookVersion", "BookAuthor", "BookTag", "BookVersionActionLog",
    "Rating", "Review", "ReviewReply", "ReviewReport",
    "DownloadLog",
    "Notification",
    "AuditLog", "ActivityFeed",
]
```

---

## Notes on running Alembic after adding models

```bash
# 1. Make sure all models are imported in __init__.py (above)
# 2. Point alembic/env.py at Base.metadata
from app.db.base import Base
from app.db.models import *        # ensures all tables are registered
target_metadata = Base.metadata

# 3. Generate the initial migration
alembic revision --autogenerate -m "initial schema"

# 4. Apply it
alembic upgrade head
```
