"""
인증/인가 유틸리티 모듈
JWT 토큰 생성/검증, 비밀번호 해시/검증, FastAPI 의존성(Depends)을 제공한다.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

# Bearer 토큰 추출 스키마 (auto_error=False: 토큰 없어도 에러 안 냄)
_bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(plain: str) -> str:
    """평문 비밀번호를 bcrypt 해시로 변환한다."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """평문 비밀번호와 bcrypt 해시를 비교 검증한다."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(admin_id: str, roles: list[str], expires_minutes: Optional[int] = None) -> str:
    """
    JWT 액세스 토큰을 생성한다.
    payload: { sub: admin_id, roles: [...], exp: ... }
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or JWT_EXPIRE_MINUTES)
    payload = {
        "sub": admin_id,
        "roles": roles,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """JWT 토큰을 디코딩하여 payload를 반환한다. 실패 시 None."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    """
    현재 로그인한 관리자 정보를 반환하는 FastAPI 의존성.
    토큰이 없거나 유효하지 않으면 401 에러를 발생시킨다.
    반환값: { "admin_id": str, "roles": list[str] }
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"admin_id": payload["sub"], "roles": payload.get("roles", [])}


def require_super(current_admin: dict = Depends(get_current_admin)) -> dict:
    """
    SUPER 권한을 요구하는 FastAPI 의존성.
    SUPER 권한이 없으면 403 에러를 발생시킨다.
    """
    if "SUPER" not in current_admin.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 등록 권한이 없습니다. (SUPER 권한 필요)",
        )
    return current_admin
