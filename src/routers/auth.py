from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import secrets
from src.services.auth.dependencies import get_current_user
from src.schemas.movies import UserResponse, UserRegisterRequest, UserLoginRequest
from src.schemas.auth import TokenResponse
from src.database.models import UserModel, RefreshTokenModel
from src.database.session import get_postgresql_db
from src.services.auth.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_postgresql_db),
):
    result = await db.execute(select(UserModel).where(UserModel.email == data.email))
    user_email = result.scalar_one_or_none()
    if user_email:
        raise HTTPException(status_code=400, detail="This email is already registered")

    new_user = UserModel(email=data.email, password=data.password, group_id=1)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLoginRequest, db: AsyncSession = Depends(get_postgresql_db)):
    user_result = await db.execute(
        select(UserModel).where(UserModel.email == data.email)
    )
    user = user_result.scalar_one_or_none()

    if not user or not verify_password(data.password, user._hashed_password):
        raise HTTPException(status_code=401, detail="Wrong credentials")

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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: str,
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
