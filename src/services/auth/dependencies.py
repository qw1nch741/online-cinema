from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.database.models import UserModel, UserGroupEnum
from src.database.session import get_postgresql_db
from src.services.auth.security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    description="JWT Bearer access token obtained from POST /auth/login",
)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_postgresql_db)
):
    """
    FastAPI dependency that resolves the authenticated user from a Bearer JWT.

    Used by protected endpoints (cart, orders, logout, create movie).
    Expects Authorization: Bearer <access_token> header.
    Returns UserModel for the token owner.
    Errors: 401 if token is missing, invalid, expired, or user not found.
    """
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        result = await db.execute(
            select(UserModel)
            .options(joinedload(UserModel.group))
            .where(UserModel.id == decoded.get("user_id"))
        )
        user = result.scalar_one_or_none()
        if user:
            return user
        raise HTTPException(status_code=401, detail="Unauthorized")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")


class RoleChecker:
    """
    FastAPI dependency factory for role-based access control (RBAC).

    **Usage:** `Depends(RoleChecker([UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN]))`

    **Action:** Allows access only if the current user's group is in `allowed_groups`.

    **Errors:** 403 if the user's group is not permitted.
    """

    def __init__(self, allowed_groups: list[UserGroupEnum]):
        self.allowed_groups = allowed_groups

    async def __call__(
        self, current_user: UserModel = Depends(get_current_user)
    ) -> UserModel:
        user_group = current_user.group.name
        if user_group not in self.allowed_groups:
            raise HTTPException(status_code=403, detail="Permission denied")
        return current_user
