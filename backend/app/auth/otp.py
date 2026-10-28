import json
import random

from fastapi import HTTPException, status
from redis.asyncio import Redis

from app.core.config import settings

OTP_LENGTH = 6


async def generate_and_store_otp(
    redis: Redis, email: str, otp_type: str
) -> str:
    """Generate a 6-digit OTP, store in Redis with TTL, and return the code."""
    otp = str(random.randint(0, 10**OTP_LENGTH - 1)).zfill(OTP_LENGTH)
    key = f"otp:{otp_type}:{email}"
    value = json.dumps({"otp": otp, "attempts": 0})
    ttl = settings.OTP_EXPIRE_MINUTES * 60
    await redis.set(key, value, ex=ttl)
    return otp


async def verify_otp(
    redis: Redis, email: str, otp_type: str, submitted_otp: str
) -> bool:
    """
    Verify a submitted OTP against the stored value.

    Raises 400 on expiry/wrong code and 429 on too many attempts.
    Deletes the Redis key on success.
    """
    key = f"otp:{otp_type}:{email}"
    raw = await redis.get(key)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired or not found. Please request a new one.",
        )

    data = json.loads(raw)
    attempts: int = data.get("attempts", 0)

    if attempts >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please request a new OTP.",
        )

    if submitted_otp != data["otp"]:
        data["attempts"] = attempts + 1
        remaining_ttl = await redis.ttl(key)
        await redis.set(key, json.dumps(data), ex=max(remaining_ttl, 1))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP.",
        )

    await redis.delete(key)
    return True
