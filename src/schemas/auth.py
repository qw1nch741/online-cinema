from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from src.services.auth.security import validate_password_strength

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Request body for user registration."""

    email: EmailStr = Field(
        ...,
        description="Unique email address used for login and account identification",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description=(
            "Account password. Minimum 8 characters. "
            "Must include at least one uppercase letter and one digit."
        ),
        examples=["SecurePass1"],
    )


class UserLoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr = Field(
        ...,
        description="Registered email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Account password",
        examples=["SecurePass1"],
    )


class UserResponse(BaseModel):
    """Registered user returned after successful registration."""

    id: int = Field(..., description="Unique user ID", examples=[1])
    email: EmailStr = Field(..., description="User email address")
    is_active: bool = Field(
        ...,
        description="False until the account is activated via email token",
    )
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token pair returned after login or refresh."""

    access_token: str = Field(
        ...,
        description="Short-lived JWT access token. Use in Authorization header as Bearer token.",
    )
    refresh_token: str = Field(
        ...,
        description="Long-lived refresh token stored server-side. Used with POST /auth/refresh.",
    )
    token_type: str = Field(
        ...,
        description="Token type, always 'bearer'",
        examples=["bearer"],
    )


class TokenData(BaseModel):
    """Decoded JWT payload data."""

    user_id: int = Field(..., description="ID of the authenticated user")
    email: Optional[EmailStr] = Field(None, description="Optional email claim")


class TokenRefreshRequest(BaseModel):
    """Request body for refreshing an access token."""

    refresh_token: str = Field(
        ...,
        description="Refresh token received from login; used to obtain a new access token",
        examples=["a1b2c3d4e5f67890..."],
    )


class ActivationResendRequest(BaseModel):
    """Request body for resending an account activation token."""

    email: EmailStr = Field(
        ...,
        description=(
            "Email of the inactive account. "
            "A new 24-hour activation token is generated if the account exists and is not yet active."
        ),
        examples=["user@example.com"],
    )


class MessageResponse(BaseModel):
    """Simple status message returned by activation endpoints."""

    message: str = Field(
        ...,
        description="Human-readable result of the activation action",
        examples=["Account activated successfully."],
    )


class PasswordChangeRequest(BaseModel):
    """Payload for logged-in users updating their credentials."""

    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, v: str) -> str:
        return validate_password_strength(v)


class ForgotPasswordRequest(BaseModel):
    """Payload for anonymous users requesting a reset token link."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Payload for finishing the unauthenticated reset loop."""

    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_reset_password(cls, v: str) -> str:
        return validate_password_strength(v)
