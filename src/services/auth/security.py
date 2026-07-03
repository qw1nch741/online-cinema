"""
JWT and password security utilities.

- Passwords are hashed with bcrypt before storage.
- Access tokens are short-lived JWTs signed with HS256.
- Refresh tokens are opaque strings stored in the database (not JWT).
"""

import bcrypt
import re
import jwt
from datetime import datetime, timedelta, timezone

from src.config.settings import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    result = hashed.decode("utf-8")
    return result


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored bcrypt hash."""
    plain_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_bytes, hashed_bytes)


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload dict (must include `user_id`).

    Returns:
        Encoded JWT string with `exp` claim set to ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY_ACCESS, algorithm=settings.ALGORITHM)
    return encoded_jwt


def validate_password_strength(password: str) -> str:
    """Ensure password has at least 8 chars, 1 uppercase, and 1 digit."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    return password
