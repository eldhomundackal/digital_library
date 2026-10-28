"""
One-time script to create the superadmin account.
Run once on first deployment:
    python scripts/seed_superadmin.py

Reads credentials from .env file via pydantic-settings.
Refuses to run if a superadmin already exists.
"""
import asyncio
import sys

from sqlalchemy import select

from app.auth.password import hash_password
from app.core.config import settings
from app.db.models.publisher import StaffProfile
from app.db.models.user import User
from app.db.session import AsyncSessionLocal


async def seed_superadmin() -> None:
    """Create the first superadmin account if none exists."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.role == "superadmin")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Superadmin already exists: {existing.email}")
            sys.exit(0)

        from app.db.session import engine
        from app.utils.number_generator import sync_from_db

        import redis.asyncio as aioredis

        redis_client = await aioredis.from_url(
            settings.REDIS_URL, decode_responses=True
        )
        number = await sync_from_db("user", db, redis_client)

        from app.utils.number_generator import generate

        user_number = await generate("user", redis_client)
        await redis_client.aclose()

        user = User(
            number=user_number,
            email=settings.SUPERADMIN_EMAIL,
            hashed_password=hash_password(settings.SUPERADMIN_PASSWORD),
            role="superadmin",
            auth_provider="local",
            is_super=True,
            is_email_verified=True,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        staff_profile = StaffProfile(
            user_id=user.id,
            first_name=settings.SUPERADMIN_FIRST_NAME,
            last_name=settings.SUPERADMIN_LAST_NAME,
        )
        db.add(staff_profile)
        await db.commit()

        print(f"Superadmin created: {settings.SUPERADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(seed_superadmin())
