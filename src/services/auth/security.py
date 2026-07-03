"""
JWT and password security utilities.

- Passwords are hashed with bcrypt before storage.
- Access tokens are short-lived JWTs signed with HS256.
- Refresh tokens are opaque strings stored in the database (not JWT).
"""

import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

# In production, these must come from your configuration settings or environment variables!
SECRET_KEY = "UCEbmHgVH5DWTohtWXiR5E2vnUL6sWakHSjcxlVQyJh"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15


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
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
