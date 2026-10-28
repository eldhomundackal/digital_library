from fastapi import APIRouter, Depends, Request, Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.base import BaseAuthProvider
from app.core.dependencies import get_current_user, get_db, get_provider, get_redis
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    SendOTPRequest,
    VerifyEmailRequest,
    VerifyEmailResponse,
    VerifyResetOTPRequest,
    VerifyResetOTPResponse,
)
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService

router = APIRouter(tags=["Auth"])


def _service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    auth_provider: BaseAuthProvider = Depends(get_provider),
) -> AuthService:
    """Dependency that constructs the AuthService."""
    return AuthService(db=db, redis=redis, auth_provider=auth_provider)


@router.post("/register", response_model=SuccessResponse[RegisterResponse])
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(_service),
) -> SuccessResponse[RegisterResponse]:
    """Register a new reader or publisher account."""
    data = await service.register(payload)
    return SuccessResponse(
        message="Account created. Please verify your email.", data=data
    )


@router.post("/verify-email/send", response_model=SuccessResponse)
async def send_verify_email_otp(
    payload: SendOTPRequest,
    service: AuthService = Depends(_service),
) -> SuccessResponse:
    """Send an email verification OTP."""
    await service.send_email_otp(payload.email, "email_verify")
    return SuccessResponse(message="Verification email sent.")


@router.post(
    "/verify-email/confirm", response_model=SuccessResponse[VerifyEmailResponse]
)
async def confirm_email(
    payload: VerifyEmailRequest,
    service: AuthService = Depends(_service),
) -> SuccessResponse[VerifyEmailResponse]:
    """Confirm email using the OTP sent to the user's inbox."""
    data = await service.verify_email(payload.email, payload.otp)
    return SuccessResponse(message="Email verified.", data=data)


@router.post("/login", response_model=SuccessResponse[LoginResponse])
async def login(
    payload: LoginRequest,
    response: Response,
    service: AuthService = Depends(_service),
) -> SuccessResponse[LoginResponse]:
    """Authenticate and return tokens. Refresh token set as HttpOnly cookie."""
    data = await service.login(payload.email, payload.password, response)
    return SuccessResponse(message="Login successful.", data=data)


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(_service),
) -> SuccessResponse:
    """Logout and revoke the refresh token."""
    refresh_token = request.cookies.get("refresh_token", "")
    await service.logout(refresh_token, response)
    return SuccessResponse(message="Logged out.")


@router.post("/refresh", response_model=SuccessResponse[RefreshResponse])
async def refresh(
    request: Request,
    service: AuthService = Depends(_service),
) -> SuccessResponse[RefreshResponse]:
    """Issue a new access token using the HttpOnly refresh cookie."""
    refresh_token = request.cookies.get("refresh_token", "")
    data = await service.refresh_access_token(refresh_token)
    return SuccessResponse(data=data)


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(_service),
) -> SuccessResponse:
    """Send a password reset OTP (always returns success for enumeration safety)."""
    try:
        await service.send_email_otp(payload.email, "password_reset")
    except Exception:  # noqa: BLE001 — intentional enumeration-safe suppression
        pass
    return SuccessResponse(
        message="If an account exists with this email, a reset code has been sent."
    )


@router.post(
    "/forgot-password/verify",
    response_model=SuccessResponse[VerifyResetOTPResponse],
)
async def verify_reset_otp(
    payload: VerifyResetOTPRequest,
    service: AuthService = Depends(_service),
) -> SuccessResponse[VerifyResetOTPResponse]:
    """Verify the password reset OTP and receive a session token."""
    data = await service.verify_reset_otp(payload.email, payload.otp)
    return SuccessResponse(data=data)


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(_service),
) -> SuccessResponse:
    """Reset password using the session token from the verify step."""
    await service.reset_password(
        payload.reset_session_token, payload.password
    )
    return SuccessResponse(message="Password reset successfully.")


@router.get("/external/login")
async def external_login(
    service: AuthService = Depends(_service),
):
    """Redirect to IDP authorization URL. Returns 404 for local auth provider."""
    from fastapi.responses import RedirectResponse

    url = await service.get_authorization_url()
    return RedirectResponse(url=url)


@router.get(
    "/external/callback", response_model=SuccessResponse[LoginResponse]
)
async def external_callback(
    code: str,
    state: str,
    response: Response,
    service: AuthService = Depends(_service),
) -> SuccessResponse[LoginResponse]:
    """Handle IDP callback, create/find user, and return tokens."""
    data = await service.handle_external_callback(code, state, response)
    return SuccessResponse(data=data)


@router.post("/external/logout", response_model=SuccessResponse)
async def external_logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(_service),
) -> SuccessResponse:
    """Logout from the external IDP."""
    refresh_token = request.cookies.get("refresh_token", "")
    await service.logout(refresh_token, response)
    return SuccessResponse(message="Logged out from external provider.")
