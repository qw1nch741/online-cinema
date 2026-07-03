"""Authentication endpoints: registration, activation, login, refresh, logout."""

from datetime import datetime, timedelta, timezone

import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models import ActivationTokenModel, RefreshTokenModel, UserModel, PasswordResetTokenModel
from src.database.session import get_postgresql_db
from src.schemas.auth import (
    ActivationResendRequest,
    MessageResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse, PasswordChangeRequest, ForgotPasswordRequest, PasswordResetConfirm,
)
from src.services.auth.dependencies import get_current_user
from src.services.auth.security import create_access_token, verify_password, hash_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

_REGISTER_DESCRIPTION = (
    "Register a new user account with a unique email address.\n\n"
    "**Action:** Creates an inactive user (`is_active=false`), hashes the password, "
    "and issues a 24-hour activation token.\n\n"
    "**Parameters:**\n"
    "- `email` — unique login email\n"
    "- `password` — minimum 8 characters; must meet complexity rules\n\n"
    "**After registration:** Use the activation link/token via `GET /auth/activate`."
)

_LOGIN_DESCRIPTION = (
    "Authenticate an active user and receive JWT tokens.\n\n"
    "**Action:** Validates credentials, checks `is_active=true`, "
    "returns a short-lived access token and a 7-day refresh token stored in the database.\n\n"
    "**Parameters:**\n"
    "- `email` — registered email\n"
    "- `password` — account password"
)

_LOGOUT_DESCRIPTION = (
    "Revoke a refresh token and end the session.\n\n"
    "**Action:** Deletes the provided refresh token from the database so it cannot be reused.\n\n"
    "**Authorization:** Bearer access token required.\n\n"
    "**Parameters:**\n"
    "- `refresh_token` — the refresh token string to revoke (query parameter)"
)

_ACTIVATE_DESCRIPTION = (
    "Activate a newly registered account using the email activation token.\n\n"
    "**Action:** Validates the token, sets `is_active=true`, and deletes the used token.\n\n"
    "**Parameters:**\n"
    "- `token` — activation token from the registration email (query parameter)"
)

_REFRESH_DESCRIPTION = (
    "Obtain a new access token using a valid refresh token.\n\n"
    "**Action:** Validates the refresh token, issues a new access token, "
    "rotates the refresh token, and stores the new refresh token in the database.\n\n"
    "**Parameters:**\n"
    "- `refresh_token` — refresh token received from login (request body)"
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=_REGISTER_DESCRIPTION,
    responses={
        201: {"description": "User created; activation token issued (account inactive until activated)"},
        409: {"description": "Email is already registered"},
        422: {"description": "Validation error (invalid email or weak password)"},
    },
)
async def register(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_postgresql_db),
):
    result = await db.execute(select(UserModel).where(UserModel.email == data.email))
    user_email = result.scalar_one_or_none()
    if user_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This email is already registered")

    new_user = UserModel(email=data.email, password=data.password, group_id=1)

    db.add(new_user)
    await db.flush()

    activation_token = ActivationTokenModel(
        user_id=new_user.id,
        token=secrets.token_hex(32),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(activation_token)

    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT tokens",
    description=_LOGIN_DESCRIPTION,
    responses={
        200: {"description": "Access and refresh tokens issued"},
        401: {"description": "Invalid credentials or account not activated"},
        422: {"description": "Validation error"},
    },
)
async def login(data: UserLoginRequest, db: AsyncSession = Depends(get_postgresql_db)):
    user_result = await db.execute(
        select(UserModel).where(UserModel.email == data.email)
    )
    user = user_result.scalar_one_or_none()

    if not user or not verify_password(data.password, user._hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong credentials")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not activated. Please verify your email.",
        )

    token = create_access_token(data={"user_id": user.id})

    refresh_token_str = secrets.token_hex(32)

    db_refresh_token = RefreshTokenModel(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(db_refresh_token)
    await db.commit()

    return {
        "access_token": token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke refresh token",
    description=_LOGOUT_DESCRIPTION,
    responses={
        204: {"description": "Refresh token revoked successfully"},
        401: {"description": "Missing or invalid Bearer access token"},
    },
)
async def logout(
    refresh_token: str = Query(
        ...,
        description="Refresh token to revoke. Must belong to the authenticated user.",
        examples=["a1b2c3d4e5f6..."],
    ),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgresql_db),
):
    await db.execute(
        delete(RefreshTokenModel).where(
            RefreshTokenModel.token == refresh_token,
            RefreshTokenModel.user_id == current_user.id,
        )
    )
    await db.commit()


@router.get(
    "/activate",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate account via email token",
    description=_ACTIVATE_DESCRIPTION,
    responses={
        200: {"description": "Account activated or already active"},
        400: {"description": "Activation token has expired"},
        404: {"description": "Activation token not found"},
    },
)
async def activate(
    token: str = Query(
        ...,
        description="Activation token from the registration email link.",
        examples=["f7e8d9c0b1a2..."],
    ),
    db: AsyncSession = Depends(get_postgresql_db),
):
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(ActivationTokenModel)
        .options(joinedload(ActivationTokenModel.user))
        .where(ActivationTokenModel.token == token)
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activation token not found")

    if db_token.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Activation token has expired")

    user = db_token.user
    if user.is_active:
        return {"message": "Account is already active."}

    user.is_active = True

    await db.delete(db_token)

    await db.commit()

    return {"message": "Account activated successfully."}


_RESEND_DESCRIPTION = (
    "Resend the account activation token.\n\n"
    "**Action:** Looks up the user by email. If the account exists and is not yet active, "
    "deletes any previous activation tokens and issues a new token valid for 24 hours.\n\n"
    "**Authorization:** Not required.\n\n"
    "**Parameters (body):**\n"
    "- `email` — registered email address of the inactive account\n\n"
    "**Note:** Returns 400 if the user does not exist or the account is already active."
)


@router.post(
    "/activate/resend",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend activation token",
    description=_RESEND_DESCRIPTION,
    responses={
        200: {"description": "New activation token generated"},
        400: {"description": "User not found or account already active"},
        422: {"description": "Validation error (invalid email format)"},
    },
)
async def activate_resend(data: ActivationResendRequest, db: AsyncSession = Depends(get_postgresql_db)):
    user_result = await db.execute(
        select(UserModel).where(UserModel.email == data.email)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    if user.is_active:
        raise HTTPException(status_code=400, detail="Account is already active")

    delete_old_tokens = delete(ActivationTokenModel).where(ActivationTokenModel.user_id == user.id)
    await db.execute(delete_old_tokens)

    # Змінюємо модель на ActivationTokenModel та виставляємо ліміт у 24 години
    activate_token_str = secrets.token_hex(32)
    db_activate_token = ActivationTokenModel(
        user_id=user.id,
        token=activate_token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(db_activate_token)
    await db.commit()

    return {"message": "A new activation token has been generated."}


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description=_REFRESH_DESCRIPTION,
    responses={
        200: {"description": "New access and refresh tokens issued"},
        401: {"description": "Invalid or expired refresh token"},
        422: {"description": "Validation error"},
    },
)
async def refresh(data: TokenRefreshRequest, db: AsyncSession = Depends(get_postgresql_db)):
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(RefreshTokenModel)
        .options(joinedload(RefreshTokenModel.user))
        .where(RefreshTokenModel.token == data.refresh_token)
    )
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db_token.user

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated.",
        )

    await db.delete(db_token)

    token = create_access_token(data={"user_id": user.id})

    refresh_token_str = secrets.token_hex(32)

    db_refresh_token = RefreshTokenModel(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(db_refresh_token)
    await db.commit()

    return {
        "access_token": token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change account password",
    responses={
        200: {"description": "Password updated successfully"},
        401: {"description": "Invalid old password or unauthorized session"},
    },
)
async def change_password(
    data: PasswordChangeRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgresql_db)
):
    if not verify_password(data.old_password, current_user._hashed_password):
        raise HTTPException(status_code=401, detail="Invalid old password or unauthorized session")

    current_user._hashed_password = hash_password(data.new_password)

    await db.commit()

    return  {"description": "Password updated successfully"}


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset token",
    responses={200: {"description": "Ambiguous success confirmation statement issued"}},
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_postgresql_db)
):
    user_result = await db.execute(
        select(UserModel).where(UserModel.email == data.email)
    )
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        return {"description": "Ambiguous success confirmation statement issued"}

    await db.execute(
        delete(PasswordResetTokenModel).where(PasswordResetTokenModel.user_id == user.id)
    )

    reset_token_str = secrets.token_hex(32)

    db_reset_token = PasswordResetTokenModel(
        user_id=user.id,
        token=reset_token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db.add(db_reset_token)

    await db.commit()

    return {"description": "If that email is registered, a reset link has been sent."}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Complete password reset execution",
    responses={
        200: {"description": "Credentials updated; user can now log in"},
        400: {"description": "Token has expired"},
        404: {"description": "Token string not found"},
    },
)
async def reset_password(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_postgresql_db)
):
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(PasswordResetTokenModel)
        .options(joinedload(PasswordResetTokenModel.user))
        .where(PasswordResetTokenModel.token == data.token)
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token string not found",
        )

    if db_token.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired",
        )

    user = db_token.user

    user._hashed_password = hash_password(data.new_password)

    await db.delete(db_token)

    await db.commit()

    return {"message": "Credentials updated; user can now log in"}



