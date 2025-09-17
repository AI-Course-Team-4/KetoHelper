from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import os
import jwt


JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXP_MINUTES = int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "30"))
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


