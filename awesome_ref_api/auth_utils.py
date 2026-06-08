import os
import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from models import User

SECRET_KEY = os.getenv("AWESOMEREF_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "AWESOMEREF_SECRET_KEY environment variable is required. "
        "Copy .env.example to .env and set a secure random value."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 3  # 3 days


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    # Legacy SHA-256 format — migrate to bcrypt on next login
    try:
        salt, h = hashed_password.split("$", 1)
        return hashlib.sha256((salt + plain_password).encode()).hexdigest() == h
    except Exception:
        return False


def needs_password_upgrade(hashed_password: str) -> bool:
    return not (hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"))


def create_access_token(data: dict, token_version: int = 0) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "tv": token_version})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, password: str) -> User:
    user = User(username=username, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def init_default_user(db: Session):
    admin_user = os.getenv("AWESOMEREF_ADMIN_USER", "")
    admin_pass = os.getenv("AWESOMEREF_ADMIN_PASS", "")
    if admin_user and admin_pass and not get_user_by_username(db, admin_user):
        create_user(db, admin_user, admin_pass)
