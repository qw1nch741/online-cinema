import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

# In production, these must come from your configuration settings or environment variables!
SECRET_KEY = "UCEbmHgVH5DWTohtWXiR5E2vnUL6sWakHSjcxlVQyJh"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    result = hashed.decode('utf-8')
    return result

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

