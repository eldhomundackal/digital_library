from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register."""

    email: EmailStr
    password: str
    confirm_password: str
    first_name: str
    last_name: str
    role: str  # "reader" | "publisher" only

    @field_validator("role")
    @classmethod
    def role_must_be_public(cls, value: str) -> str:
        """Only reader and publisher roles can self-register."""
        if value not in ("reader", "publisher"):
            raise ValueError("Role must be 'reader' or 'publisher'")
        return value

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        """confirm_password must match password."""
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Passwords do not match")
        return value


class RegisterResponse(BaseModel):
    """Response body for POST /auth/register."""

    user_id: str  # uuid
    email: str
    role: str
    is_email_verified: bool


class LoginRequest(BaseModel):
    """Request body for POST /auth/login."""

    email: EmailStr
    password: str


class TokenData(BaseModel):
    """Access token data."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserSummary(BaseModel):
    """Minimal user info embedded in login response and notifications."""

    user_id: str
    email: str
    role: str
    is_first_login: bool
    profile_completion: int | None = None  # readers only
    kyc_status: str | None = None  # publishers only


class LoginResponse(BaseModel):
    """Response body for POST /auth/login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary
    # refresh_token set as HttpOnly cookie by router, not in body


class RefreshResponse(BaseModel):
    """Response body for POST /auth/refresh."""

    access_token: str
    expires_in: int


class SendOTPRequest(BaseModel):
    """Request body for OTP send endpoints."""

    email: EmailStr


class VerifyEmailRequest(BaseModel):
    """Request body for POST /auth/verify-email/confirm."""

    email: EmailStr
    otp: str  # 6-digit string


class VerifyEmailResponse(BaseModel):
    """Response body for POST /auth/verify-email/confirm."""

    user_id: str
    role: str
    next_step: str  # "kyc_required" | "login"


class ForgotPasswordRequest(BaseModel):
    """Request body for POST /auth/forgot-password."""

    email: EmailStr


class VerifyResetOTPRequest(BaseModel):
    """Request body for POST /auth/forgot-password/verify."""

    email: EmailStr
    otp: str


class VerifyResetOTPResponse(BaseModel):
    """Response body for POST /auth/forgot-password/verify."""

    reset_session_token: str
    expires_in: int


class ResetPasswordRequest(BaseModel):
    """Request body for POST /auth/reset-password."""

    reset_session_token: str
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        """confirm_password must match password."""
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Passwords do not match")
        return value


class OIDCCallbackRequest(BaseModel):
    """Query params for GET /auth/external/callback."""

    code: str
    state: str
