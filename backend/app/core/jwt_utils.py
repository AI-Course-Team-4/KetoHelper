from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import os
import jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer


JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXP_MINUTES = int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "1"))  # 개발용: 1분
REFRESH_TOKEN_EXP_DAYS = int(os.getenv("REFRESH_TOKEN_EXP_DAYS", "30"))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(subject: str, claims: Optional[Dict[str, Any]] = None) -> str:
    payload: Dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": int(_now_utc().timestamp()),
        "exp": int((_now_utc() + timedelta(minutes=ACCESS_TOKEN_EXP_MINUTES)).timestamp()),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(subject: str, claims: Optional[Dict[str, Any]] = None) -> str:
    payload: Dict[str, Any] = {
        "sub": subject,
        "type": "refresh",
        "iat": int(_now_utc().timestamp()),
        "exp": int((_now_utc() + timedelta(days=REFRESH_TOKEN_EXP_DAYS)).timestamp()),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# FastAPI security scheme
security = HTTPBearer()


def get_current_user(request: Request) -> Dict[str, Any]:
    """
    JWT 토큰에서 현재 사용자 정보를 추출합니다.
    쿠키 또는 Authorization 헤더에서 토큰을 읽습니다.
    """
    token = None
    
    # 1. 쿠키에서 access_token 확인
    token = request.cookies.get("access_token")
    
    # 2. Authorization 헤더에서 토큰 확인
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="인증 토큰이 없습니다"
        )
    
    try:
        payload = decode_token(token)
        
        # 토큰 타입 확인
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="잘못된 토큰 타입입니다"
            )
        
        # 토큰 만료 확인
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < _now_utc():
            raise HTTPException(
                status_code=401,
                detail="토큰이 만료되었습니다"
            )
        
        # 사용자 정보 반환
        return {
            "id": payload.get("sub"),
            "email": payload.get("email", ""),
            "name": payload.get("name", "")
        }
        
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 토큰입니다"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"토큰 검증 실패: {str(e)}"
        )

