import re
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request, Depends, status, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from auth_utils import verify_password, hash_password, create_access_token, get_user_by_username, create_user, needs_password_upgrade
from deps import get_current_user

router = APIRouter()

# Simple in-memory rate limiter: 5 attempts per IP per minute
_rate_attempts = defaultdict(list)
_RATE_LIMIT = 5
_RATE_WINDOW = 60


def _check_rate(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    _rate_attempts[ip] = [t for t in _rate_attempts[ip] if now - t < _RATE_WINDOW]
    if len(_rate_attempts[ip]) >= _RATE_LIMIT:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="操作过于频繁，请稍后再试")
    _rate_attempts[ip].append(now)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    confirmPassword: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    _check_rate(request)
    username = req.username.strip()
    if not username or not req.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名和密码不能为空")
    user = get_user_by_username(db, username)
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if needs_password_upgrade(user.hashed_password):
        user.hashed_password = hash_password(req.password)
        db.commit()
    token = create_access_token({"sub": user.username})
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 3,  # 3 days
    )
    return TokenResponse(access_token=token, username=user.username)


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    _check_rate(request)
    username = req.username.strip()
    password = req.password
    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名和密码不能为空")
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名仅支持英文字母开头，只包含英文、数字和下划线")
    if len(username) < 2 or len(username) > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名长度2-50个字符")
    if len(password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码至少6位")
    if password != req.confirmPassword:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="两次密码输入不一致")
    existing = get_user_by_username(db, username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user = create_user(db, username, password)
    token = create_access_token({"sub": user.username})
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 3,
    )
    return TokenResponse(access_token=token, username=user.username)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not req.old_password or not req.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码不能为空")
    if not verify_password(req.old_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原密码错误")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密码至少6位")
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="两次新密码输入不一致")
    user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"message": "密码修改成功"}


@router.get("/me")
def get_me(user=Depends(get_current_user)):
    return {"username": user.username}
