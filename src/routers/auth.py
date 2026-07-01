from src.schemas.movies import (
    UserResponse,
    UserRegisterRequest,
    TokenResponse,
    UserLoginRequest,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import AsyncSession
from sqlalchemy import select

from src.database.models import UserModel
from src.database.session import get_postgresql_db
from src.schemas.auth import TokenResponse
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

    new_user = UserModel(email=data.email, password=data.password)

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

    return {
        "access_token": token,
        "refresh_token": "refresh_token",
        "token_type": "bearer",
    }
