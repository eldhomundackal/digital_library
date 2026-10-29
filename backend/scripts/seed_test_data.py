"""
Seed realistic test data for API testing.

Creates:
  - 3 readers
  - 2 publishers (KYC approved, ready to use)
  - 1 staff member
  - 5 categories
  - 8 tags (approved)
  - 4 authors
  - 6 books (approved, with versions) across publishers
  - 10 ratings + reviews across books/readers
"""

import asyncio
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, "/app")

from sqlalchemy import select

from app.auth.password import hash_password
from app.db.models.author import Author
from app.db.models.book import Book, BookAuthor, BookTag, BookVersion, BookVersionActionLog
from app.db.models.category import Category, Tag
from app.db.models.kyc import KYCApplication
from app.db.models.publisher import PublisherProfile, StaffProfile
from app.db.models.review import Rating, Review
from app.db.models.user import ReaderProfile, User
from app.db.models.utils import Language
from app.db.session import AsyncSessionLocal

# ---------------------------------------------------------------------------
# Test credentials — printed at the end for easy reference
# ---------------------------------------------------------------------------
READERS = [
    {"email": "alice@example.com", "password": "Test1234!", "first_name": "Alice", "last_name": "Walker"},
    {"email": "bob@example.com", "password": "Test1234!", "first_name": "Bob", "last_name": "Smith"},
    {"email": "carol@example.com", "password": "Test1234!", "first_name": "Carol", "last_name": "Jones"},
]

PUBLISHERS = [
    {"email": "penguin@example.com", "password": "Test1234!", "display_name": "Penguin Books"},
    {"email": "oreilly@example.com", "password": "Test1234!", "display_name": "O'Reilly Media"},
]

STAFF = {"email": "staff@example.com", "password": "Test1234!", "first_name": "Sam", "last_name": "Staff"}

CATEGORIES = [
    {"name": "Fiction", "slug": "fiction"},
    {"name": "Science & Technology", "slug": "science-technology"},
    {"name": "History", "slug": "history"},
    {"name": "Self Help", "slug": "self-help"},
    {"name": "Philosophy", "slug": "philosophy"},
]

TAGS = [
    "Python", "Machine Learning", "Novel", "Classic",
    "Biography", "Adventure", "Mystery", "Data Science",
]

AUTHORS = [
    {"first_name": "George", "last_name": "Orwell", "bio": "English novelist and essayist."},
    {"first_name": "Guido", "last_name": "van Rossum", "bio": "Creator of the Python programming language."},
    {"first_name": "Jane", "last_name": "Austen", "bio": "English novelist known for Pride and Prejudice."},
    {"first_name": "Andrew", "last_name": "Ng", "bio": "AI researcher and educator."},
]

BOOKS = [
    {
        "title": "Nineteen Eighty-Four",
        "description": "A dystopian social science fiction novel set in a totalitarian society.",
        "isbn": "978-0451524935",
        "page_count": 328,
        "publication_year": 1949,
        "category_slug": "fiction",
        "author_names": ["George Orwell"],
        "tag_names": ["Novel", "Classic"],
        "publisher_index": 0,
    },
    {
        "title": "Learning Python",
        "description": "Comprehensive introduction to Python programming for beginners and experts.",
        "isbn": "978-1449355739",
        "page_count": 1540,
        "publication_year": 2013,
        "category_slug": "science-technology",
        "author_names": ["Guido van Rossum"],
        "tag_names": ["Python"],
        "publisher_index": 0,
    },
    {
        "title": "Pride and Prejudice",
        "description": "A romantic novel of manners set in rural England in the early 19th century.",
        "isbn": "978-0141439518",
        "page_count": 432,
        "publication_year": 1813,
        "category_slug": "fiction",
        "author_names": ["Jane Austen"],
        "tag_names": ["Novel", "Classic"],
        "publisher_index": 1,
    },
    {
        "title": "Machine Learning Yearning",
        "description": "Practical guide to structuring machine learning projects.",
        "isbn": None,
        "page_count": 118,
        "publication_year": 2018,
        "category_slug": "science-technology",
        "author_names": ["Andrew Ng"],
        "tag_names": ["Machine Learning", "Data Science"],
        "publisher_index": 1,
    },
    {
        "title": "Animal Farm",
        "description": "An allegorical novella reflecting events leading up to the Russian Revolution.",
        "isbn": "978-0451526342",
        "page_count": 112,
        "publication_year": 1945,
        "category_slug": "fiction",
        "author_names": ["George Orwell"],
        "tag_names": ["Novel", "Classic"],
        "publisher_index": 0,
    },
    {
        "title": "Deep Learning for Coders",
        "description": "A practical deep learning course for programmers with no math background required.",
        "isbn": "978-1492045526",
        "page_count": 624,
        "publication_year": 2020,
        "category_slug": "science-technology",
        "author_names": ["Andrew Ng"],
        "tag_names": ["Machine Learning", "Python", "Data Science"],
        "publisher_index": 1,
    },
]

REVIEWS = [
    {"book_title": "Nineteen Eighty-Four", "reader_email": "alice@example.com", "score": 5, "comment": "A timeless masterpiece. Every page is gripping."},
    {"book_title": "Nineteen Eighty-Four", "reader_email": "bob@example.com", "score": 4, "comment": "Brilliant but very dark. Essential reading."},
    {"book_title": "Learning Python", "reader_email": "alice@example.com", "score": 5, "comment": "Best Python book I have ever read. Very thorough."},
    {"book_title": "Learning Python", "reader_email": "carol@example.com", "score": 4, "comment": "Great for beginners, a bit verbose for experts."},
    {"book_title": "Pride and Prejudice", "reader_email": "bob@example.com", "score": 4, "comment": "Witty and charming. Austen at her best."},
    {"book_title": "Pride and Prejudice", "reader_email": "carol@example.com", "score": 5, "comment": "Absolutely loved it. A perfect romance."},
    {"book_title": "Machine Learning Yearning", "reader_email": "alice@example.com", "score": 5, "comment": "Andrew Ng distills years of ML wisdom into a short read."},
    {"book_title": "Animal Farm", "reader_email": "bob@example.com", "score": 5, "comment": "Short, sharp, and devastating. A perfect allegory."},
    {"book_title": "Animal Farm", "reader_email": "carol@example.com", "score": 4, "comment": "Clever and thought-provoking."},
    {"book_title": "Deep Learning for Coders", "reader_email": "alice@example.com", "score": 5, "comment": "Hands-on and practical. Makes deep learning accessible."},
]


async def get_or_skip(db, model, **filters):
    """Return existing row or None if not found."""
    result = await db.execute(select(model).filter_by(**filters))
    return result.scalar_one_or_none()


async def seed():
    """Run the full test data seed."""
    async with AsyncSessionLocal() as db:

        # ------------------------------------------------------------------ #
        # Language — pick English (seeded by seed_languages.py)
        # ------------------------------------------------------------------ #
        result = await db.execute(select(Language).where(Language.name == "English"))
        english = result.scalar_one_or_none()
        if not english:
            print("ERROR: English language not found. Run seed_languages.py first.")
            return
        print(f"Using language: {english.name} (id={english.id})")

        # ------------------------------------------------------------------ #
        # Categories
        # ------------------------------------------------------------------ #
        category_map: dict[str, Category] = {}
        for cat_data in CATEGORIES:
            existing = await get_or_skip(db, Category, slug=cat_data["slug"])
            if existing:
                category_map[cat_data["slug"]] = existing
                print(f"  Category already exists: {cat_data['name']}")
            else:
                cat = Category(name=cat_data["name"], slug=cat_data["slug"])
                db.add(cat)
                await db.flush()
                category_map[cat_data["slug"]] = cat
                print(f"  Created category: {cat_data['name']}")

        # ------------------------------------------------------------------ #
        # Tags
        # ------------------------------------------------------------------ #
        tag_map: dict[str, Tag] = {}
        for tag_name in TAGS:
            slug = tag_name.lower().replace(" ", "-").replace("&", "and")
            existing = await get_or_skip(db, Tag, slug=slug)
            if existing:
                tag_map[tag_name] = existing
                print(f"  Tag already exists: {tag_name}")
            else:
                tag = Tag(name=tag_name, slug=slug, status="APPROVED")
                db.add(tag)
                await db.flush()
                tag_map[tag_name] = tag
                print(f"  Created tag: {tag_name}")

        # ------------------------------------------------------------------ #
        # Authors
        # ------------------------------------------------------------------ #
        author_map: dict[str, Author] = {}
        for aut_data in AUTHORS:
            full_name = f"{aut_data['first_name']} {aut_data['last_name']}"
            existing = await get_or_skip(
                db, Author,
                first_name=aut_data["first_name"],
                last_name=aut_data["last_name"],
            )
            if existing:
                author_map[full_name] = existing
                print(f"  Author already exists: {full_name}")
            else:
                author = Author(
                    first_name=aut_data["first_name"],
                    last_name=aut_data["last_name"],
                    bio=aut_data["bio"],
                )
                db.add(author)
                await db.flush()
                author_map[full_name] = author
                print(f"  Created author: {full_name}")

        # ------------------------------------------------------------------ #
        # Readers
        # ------------------------------------------------------------------ #
        reader_map: dict[str, User] = {}
        counter_start = 100  # avoid colliding with real USR- counters
        for i, r in enumerate(READERS):
            existing = await get_or_skip(db, User, email=r["email"])
            if existing:
                reader_map[r["email"]] = existing
                print(f"  Reader already exists: {r['email']}")
            else:
                user = User(
                    uuid=str(uuid.uuid4()),
                    number=f"USR-{counter_start + i:06d}",
                    email=r["email"],
                    hashed_password=hash_password(r["password"]),
                    role="reader",
                    auth_provider="local",
                    is_email_verified=True,
                    is_active=True,
                    is_first_login=False,
                )
                db.add(user)
                await db.flush()
                profile = ReaderProfile(
                    user_id=user.id,
                    first_name=r["first_name"],
                    last_name=r["last_name"],
                )
                db.add(profile)
                await db.flush()
                reader_map[r["email"]] = user
                print(f"  Created reader: {r['email']}")

        # ------------------------------------------------------------------ #
        # Publishers  (KYC auto-approved for testing)
        # ------------------------------------------------------------------ #
        publisher_users: list[User] = []
        publisher_profiles: list[PublisherProfile] = []
        pub_counter_start = 200
        for i, p in enumerate(PUBLISHERS):
            existing = await get_or_skip(db, User, email=p["email"])
            if existing:
                result = await db.execute(
                    select(PublisherProfile).where(PublisherProfile.user_id == existing.id)
                )
                pub_profile = result.scalar_one_or_none()
                publisher_users.append(existing)
                publisher_profiles.append(pub_profile)
                print(f"  Publisher already exists: {p['email']}")
            else:
                user = User(
                    uuid=str(uuid.uuid4()),
                    number=f"USR-{pub_counter_start + i:06d}",
                    email=p["email"],
                    hashed_password=hash_password(p["password"]),
                    role="publisher",
                    auth_provider="local",
                    is_email_verified=True,
                    is_active=True,
                    is_first_login=False,
                )
                db.add(user)
                await db.flush()

                pub_profile = PublisherProfile(
                    uuid=str(uuid.uuid4()),
                    number=f"PUB-{pub_counter_start + i:06d}",
                    user_id=user.id,
                    display_name=p["display_name"],
                    bio=f"Test publisher account for {p['display_name']}.",
                    kyc_status="APPROVED",
                    is_verified=True,
                )
                db.add(pub_profile)
                await db.flush()

                kyc = KYCApplication(
                    uuid=str(uuid.uuid4()),
                    number=f"KYC-{pub_counter_start + i:06d}",
                    publisher_id=pub_profile.id,
                    overall_status="APPROVED",
                    reviewed_at=datetime.now(timezone.utc),
                )
                db.add(kyc)
                await db.flush()

                publisher_users.append(user)
                publisher_profiles.append(pub_profile)
                print(f"  Created publisher: {p['email']} (KYC approved)")

        # ------------------------------------------------------------------ #
        # Staff member
        # ------------------------------------------------------------------ #
        existing_staff = await get_or_skip(db, User, email=STAFF["email"])
        if existing_staff:
            print(f"  Staff already exists: {STAFF['email']}")
        else:
            staff_user = User(
                uuid=str(uuid.uuid4()),
                number="USR-000300",
                email=STAFF["email"],
                hashed_password=hash_password(STAFF["password"]),
                role="staff",
                auth_provider="local",
                is_email_verified=True,
                is_active=True,
                is_first_login=False,
            )
            db.add(staff_user)
            await db.flush()
            staff_profile = StaffProfile(
                uuid=str(uuid.uuid4()),
                user_id=staff_user.id,
                first_name=STAFF["first_name"],
                last_name=STAFF["last_name"],
            )
            db.add(staff_profile)
            await db.flush()
            print(f"  Created staff: {STAFF['email']}")

        # ------------------------------------------------------------------ #
        # Books + BookVersions (APPROVED, with placeholder file paths)
        # ------------------------------------------------------------------ #
        book_map: dict[str, Book] = {}
        bk_counter_start = 100
        for i, bk_data in enumerate(BOOKS):
            existing = await get_or_skip(db, Book, title=bk_data["title"])
            if existing:
                book_map[bk_data["title"]] = existing
                print(f"  Book already exists: {bk_data['title']}")
                continue

            pub_profile = publisher_profiles[bk_data["publisher_index"]]
            category = category_map[bk_data["category_slug"]]

            book = Book(
                uuid=str(uuid.uuid4()),
                number=f"BK-{bk_counter_start + i:06d}",
                publisher_id=pub_profile.id,
                category_id=category.id,
                language_id=english.id,
                title=bk_data["title"],
            )
            db.add(book)
            await db.flush()

            version = BookVersion(
                uuid=str(uuid.uuid4()),
                book_id=book.id,
                version_number=1,
                version_label="1.0",
                title=bk_data["title"],
                description=bk_data["description"],
                isbn=bk_data["isbn"],
                page_count=bk_data["page_count"],
                publication_year=bk_data["publication_year"],
                thumbnail="placeholder/thumbnail.png",
                pdf_file="placeholder/book.pdf",
                pdf_file_name="book.pdf",
                pdf_file_size_mb=2.5,
                status="APPROVED",
                is_current=True,
                submitted_at=datetime.now(timezone.utc),
                approved_at=datetime.now(timezone.utc),
            )
            db.add(version)
            await db.flush()

            # Point book at its current version
            book.current_version_id = version.id

            # Action log
            action_log = BookVersionActionLog(
                uuid=str(uuid.uuid4()),
                book_version_id=version.id,
                action="APPROVED",
                performed_by_type="admin",
                note="Seeded test data.",
            )
            db.add(action_log)

            # Authors
            for author_name in bk_data["author_names"]:
                author = author_map[author_name]
                db.add(BookAuthor(book_id=book.id, author_id=author.id))

            # Tags
            for tag_name in bk_data["tag_names"]:
                tag = tag_map[tag_name]
                db.add(BookTag(book_id=book.id, tag_id=tag.id))

            await db.flush()
            book_map[bk_data["title"]] = book
            print(f"  Created book: {bk_data['title']}")

        # ------------------------------------------------------------------ #
        # Ratings + Reviews
        # ------------------------------------------------------------------ #
        rev_counter_start = 100
        for i, rev_data in enumerate(REVIEWS):
            book = book_map.get(rev_data["book_title"])
            reader = reader_map.get(rev_data["reader_email"])
            if not book or not reader:
                print(f"  Skipping review — book or reader not found: {rev_data}")
                continue

            existing_rating = await get_or_skip(
                db, Rating, book_id=book.id, user_id=reader.id
            )
            if existing_rating:
                print(f"  Rating already exists: {rev_data['reader_email']} on {rev_data['book_title']}")
                continue

            rating = Rating(
                uuid=str(uuid.uuid4()),
                book_id=book.id,
                user_id=reader.id,
                score=rev_data["score"],
            )
            db.add(rating)
            await db.flush()

            review = Review(
                uuid=str(uuid.uuid4()),
                number=f"REV-{rev_counter_start + i:06d}",
                book_id=book.id,
                user_id=reader.id,
                rating_id=rating.id,
                comment=rev_data["comment"],
            )
            db.add(review)
            await db.flush()
            print(f"  Created review by {rev_data['reader_email']} on \"{rev_data['book_title']}\"")

        await db.commit()
        print("\n✓ Test data seeded successfully.\n")

    # ---------------------------------------------------------------------- #
    # Print credentials summary
    # ---------------------------------------------------------------------- #
    print("=" * 60)
    print("TEST CREDENTIALS")
    print("=" * 60)
    print("\nReaders:")
    for r in READERS:
        print(f"  {r['email']}  /  {r['password']}")
    print("\nPublishers (KYC approved):")
    for p in PUBLISHERS:
        print(f"  {p['email']}  /  {p['password']}")
    print("\nStaff:")
    print(f"  {STAFF['email']}  /  {STAFF['password']}")
    print("\nSuperadmin:")
    print("  superadmin@example.com  /  SuperAdmin123!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
