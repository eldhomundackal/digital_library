from datetime import datetime, timezone

from fastapi import HTTPException, Response, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.base import BaseAuthProvider
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    create_reset_session_token,
    decode_token,
)
from app.auth.otp import generate_and_store_otp, verify_otp
from app.auth.password import hash_password, verify_password
from app.core.config import settings
from app.db.models.kyc import KYCApplication
from app.db.models.publisher import PublisherProfile
from app.db.models.user import ReaderProfile, User
from app.schemas.auth import (
    LoginResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    UserSummary,
    VerifyEmailResponse,
    VerifyResetOTPResponse,
)
from app.utils.number_generator import generate

REFRESH_COOKIE_KEY = "refresh_token"
RESET_SESSION_TTL = 600  # 10 minutes


class AuthService:
    """Handles all authentication flows: registration, login, OTP, JWT, reset."""

    def __init__(
        self,
        db: AsyncSession,
        redis: Redis,
        auth_provider: BaseAuthProvider,
    ) -> None:
        """Initialise with injected DB session, Redis client, and auth provider."""
        self.db = db
        self.redis = redis
        self.auth_provider = auth_provider

    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        """
        Register a new reader or publisher.
        Fires send_otp_email Celery task after creating the user.
        """
        result = await self.db.execute(
            select(User).where(User.email == payload.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )

        hashed = hash_password(payload.password)
        number = await generate("user", self.redis)

        user = User(
            number=number,
            email=payload.email,
            hashed_password=hashed,
            role=payload.role,
            auth_provider="local",
            is_email_verified=False,
        )
        self.db.add(user)
        await self.db.flush()  # get user.id before creating profiles

        if payload.role == "reader":
            profile = ReaderProfile(
                user_id=user.id,
                first_name=payload.first_name,
                last_name=payload.last_name,
            )
            self.db.add(profile)

        elif payload.role == "publisher":
            pub_number = await generate("publisher", self.redis)
            publisher_profile = PublisherProfile(
                user_id=user.id,
                number=pub_number,
                display_name=f"{payload.first_name} {payload.last_name}",
            )
            self.db.add(publisher_profile)
            await self.db.flush()

            kyc_number = await generate("kyc", self.redis)
            kyc_app = KYCApplication(
                publisher_id=publisher_profile.id,
                number=kyc_number,
                overall_status="INCOMPLETE",
            )
            self.db.add(kyc_app)

        await self.db.commit()

        from app.tasks.email_tasks import send_otp_email

        otp = await generate_and_store_otp(self.redis, payload.email, "email_verify")
        send_otp_email.delay(payload.email, otp, "email_verify")

        return RegisterResponse(
            user_id=user.uuid,
            email=user.email,
            role=user.role,
            is_email_verified=user.is_email_verified,
        )

    async def send_email_otp(self, email: str, otp_type: str) -> None:
        """Generate and send an OTP to the given email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email.",
            )

        from app.tasks.email_tasks import send_otp_email

        otp = await generate_and_store_otp(self.redis, email, otp_type)
        send_otp_email.delay(email, otp, otp_type)

    async def verify_email(self, email: str, otp: str) -> VerifyEmailResponse:
        """Verify the email OTP; mark user as verified and fire welcome email."""
        await verify_otp(self.redis, email, "email_verify", otp)

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        user.is_email_verified = True
        await self.db.commit()

        from app.tasks.email_tasks import send_welcome_email

        send_welcome_email.delay(user.id)

        next_step = "kyc_required" if user.role == "publisher" else "login"
        return VerifyEmailResponse(
            user_id=user.uuid,
            role=user.role,
            next_step=next_step,
        )

    async def login(
        self, email: str, password: str, response: Response
    ) -> LoginResponse:
        """Authenticate user; return access token and set HttpOnly refresh cookie."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated.",
            )

        if not user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in.",
            )

        if not user.hashed_password or not verify_password(
            password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        is_first = user.is_first_login
        user.last_login_at = datetime.now(timezone.utc)
        user.is_first_login = False
        await self.db.commit()

        access_token = create_access_token(user.uuid, user.role)
        refresh_token = create_refresh_token(user.uuid)

        refresh_ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.set(
            f"refresh:{user.uuid}:{refresh_token[-8:]}",
            refresh_token,
            ex=refresh_ttl,
        )

        response.set_cookie(
            key=REFRESH_COOKIE_KEY,
            value=refresh_token,
            httponly=True,
            max_age=refresh_ttl,
            path="/api/v1/auth/refresh",
            samesite="lax",
        )

        profile_completion: int | None = None
        kyc_status: str | None = None
        if user.role == "reader":
            await self.db.refresh(user, ["reader_profile"])
            if user.reader_profile:
                profile_completion = user.reader_profile.profile_completion
        elif user.role == "publisher":
            await self.db.refresh(user, ["publisher_profile"])
            if user.publisher_profile:
                kyc_status = user.publisher_profile.kyc_status

        return LoginResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserSummary(
                user_id=user.uuid,
                email=user.email,
                role=user.role,
                is_first_login=is_first,
                profile_completion=profile_completion,
                kyc_status=kyc_status,
            ),
        )

    async def logout(self, refresh_token: str, response: Response) -> None:
        """Blacklist the refresh token in Redis and clear the cookie."""
        try:
            payload = decode_token(refresh_token)
            user_uuid = payload.get("sub", "unknown")
        except HTTPException:
            user_uuid = "unknown"

        remaining = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.set(
            f"blacklist:{refresh_token[-16:]}",
            user_uuid,
            ex=remaining,
        )
        response.delete_cookie(
            key=REFRESH_COOKIE_KEY, path="/api/v1/auth/refresh"
        )

    async def refresh_access_token(self, refresh_token: str) -> RefreshResponse:
        """Validate refresh token and issue a new access token."""
        blacklisted = await self.redis.get(f"blacklist:{refresh_token[-16:]}")
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked.",
            )

        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
            )

        user_uuid = payload.get("sub")
        result = await self.db.execute(
            select(User).where(User.uuid == user_uuid)
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or deactivated.",
            )

        access_token = create_access_token(user.uuid, user.role)
        return RefreshResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def verify_reset_otp(
        self, email: str, otp: str
    ) -> VerifyResetOTPResponse:
        """Verify the password-reset OTP and return a short-lived session token."""
        await verify_otp(self.redis, email, "password_reset", otp)

        reset_session_token = create_reset_session_token()
        await self.redis.set(
            f"reset_session:{reset_session_token}", email, ex=RESET_SESSION_TTL
        )

        return VerifyResetOTPResponse(
            reset_session_token=reset_session_token,
            expires_in=RESET_SESSION_TTL,
        )

    async def reset_password(
        self, reset_session_token: str, new_password: str
    ) -> None:
        """Apply a new password using the session token from verify_reset_otp."""
        email = await self.redis.get(f"reset_session:{reset_session_token}")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset session expired or invalid.",
            )

        if isinstance(email, bytes):
            email = email.decode()

        await self.redis.delete(f"reset_session:{reset_session_token}")

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        user.hashed_password = hash_password(new_password)
        await self.db.commit()

    async def get_authorization_url(self) -> str:
        """Return the external IDP authorization URL."""
        return await self.auth_provider.get_authorization_url()

    async def handle_external_callback(
        self, code: str, state: str, response: Response
    ) -> LoginResponse:
        """Handle IDP callback, create/find local user, issue JWT tokens."""
        token_data = await self.auth_provider.handle_callback(code, state)
        user_info = await self.auth_provider.get_user_info(
            token_data.get("access_token", "")
        )

        idp_sub = user_info.get("sub")
        email = user_info.get("email")

        result = await self.db.execute(
            select(User).where(
                User.idp_sub == idp_sub,
                User.auth_provider == settings.AUTH_PROVIDER,
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            number = await generate("user", self.redis)
            user = User(
                number=number,
                email=email,
                role="reader",
                auth_provider=settings.AUTH_PROVIDER,
                idp_sub=idp_sub,
                is_email_verified=user_info.get("email_verified", False),
            )
            self.db.add(user)
            await self.db.flush()

            profile = ReaderProfile(
                user_id=user.id,
                first_name=user_info.get("given_name", ""),
                last_name=user_info.get("family_name", ""),
            )
            self.db.add(profile)
            await self.db.commit()

            from app.tasks.email_tasks import send_welcome_email

            send_welcome_email.delay(user.id)

        user.last_login_at = datetime.now(timezone.utc)
        user.is_first_login = False
        await self.db.commit()

        access_token = create_access_token(user.uuid, user.role)
        refresh_token = create_refresh_token(user.uuid)
        refresh_ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

        response.set_cookie(
            key=REFRESH_COOKIE_KEY,
            value=refresh_token,
            httponly=True,
            max_age=refresh_ttl,
            path="/api/v1/auth/refresh",
            samesite="lax",
        )

        return LoginResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserSummary(
                user_id=user.uuid,
                email=user.email,
                role=user.role,
                is_first_login=False,
            ),
        )
