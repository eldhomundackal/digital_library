"""
Seeds predefined languages list.
Edit LANGUAGES list below to add/remove supported languages.
Idempotent: skips existing records matched by iso_code.
Run: python scripts/seed_languages.py
"""

import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.utils import Language

LANGUAGES = [
    {"name": "English", "iso_code": "en"},
    {"name": "Arabic", "iso_code": "ar"},
    {"name": "French", "iso_code": "fr"},
    {"name": "Spanish", "iso_code": "es"},
    {"name": "German", "iso_code": "de"},
    {"name": "Hindi", "iso_code": "hi"},
    {"name": "Malayalam", "iso_code": "ml"},
    {"name": "Tamil", "iso_code": "ta"},
    {"name": "Mandarin", "iso_code": "zh"},
    {"name": "Portuguese", "iso_code": "pt"},
    {"name": "Japanese", "iso_code": "ja"},
    {"name": "Russian", "iso_code": "ru"},
]


async def seed() -> None:
    """Seed languages from the LANGUAGES list."""
    seeded = 0
    async with AsyncSessionLocal() as db:
        for lang in LANGUAGES:
            existing = await db.execute(
                select(Language).where(Language.iso_code == lang["iso_code"])
            )
            if not existing.scalar_one_or_none():
                db.add(Language(name=lang["name"], iso_code=lang["iso_code"]))
                seeded += 1
        await db.commit()
    print(f"Seeded {seeded} languages (skipped existing).")


asyncio.run(seed())
