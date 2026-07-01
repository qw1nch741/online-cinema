from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from sqlalchemy import select

from src.database.models import UserModel
from src.database.session import get_postgresql_db
from src.services.auth.security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_postgresql_db)
):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        result = await db.execute(
            select(UserModel).where(UserModel.id == decoded.get("user_id"))
        )
        user = result.scalar_one_or_none()
        if user:
            return user
        raise HTTPException(status_code=401, detail="Unauthorized")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
