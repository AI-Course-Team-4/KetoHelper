from fastapi import APIRouter, Depends, HTTPException
from fastapi import Body
from fastapi import Response, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
import json
import os
import jwt
from app.core.jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    ACCESS_TOKEN_EXP_MINUTES,
    REFRESH_TOKEN_EXP_DAYS,
)
from app.core.database import supabase_admin
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleAccessRequest(BaseModel):
    access_token: str


class KakaoAccessRequest(BaseModel):
    access_token: str


class NaverCodeRequest(BaseModel):
    code: str
    state: str
    redirect_uri: str


async def _upsert_user(profile: dict) -> dict:
    # 공급자 ID로 UUIDv5 생성 (DB가 uuid 타입일 때 안전)
    raw_id = str(profile.get("id") or profile.get("sub") or profile.get("email") or "")
    provider = profile.get("provider") or profile.get("source") or "oauth"
    print(f"provider: {provider}")
    try:
        fixed_id = str(uuid.UUID(raw_id))
    except Exception:
        fixed_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{provider}:{raw_id}"))

    # 먼저 기존 사용자 확인 (id 기준)
    try:
        existing_resp = supabase_admin.table("users").select("*").eq("id", fixed_id).execute()
        existing_user = getattr(existing_resp, "data", None)
        existing_user = existing_user[0] if existing_user else None
    except Exception:
        existing_user = None

    # 기존 사용자가 있다면 nickname 보존, 없다면 소셜 로그인 정보 사용
    if existing_user:
        user_data = {
            "id": fixed_id,
            "email": profile.get("email", ""),
            "nickname": existing_user.get("nickname") or profile.get("name") or profile.get("nickname") or "",
            "social_nickname": existing_user.get("social_nickname") or profile.get("name") or profile.get("nickname") or "",
            "profile_image_url": profile.get("picture") or profile.get("profile_image") or "",
            "provider": provider,
        }
    else:
        user_data = {
            "id": fixed_id,
            "email": profile.get("email", ""),
            "nickname": profile.get("name") or profile.get("nickname") or "",
            "social_nickname": profile.get("name") or profile.get("nickname") or "",
            "profile_image_url": profile.get("picture") or profile.get("profile_image") or "",
            "provider": provider,
        }

    print('[DEBUG] fixed_id', fixed_id, 'raw_id', raw_id, 'provider', provider)
    print('[DEBUG] upsert payload', user_data)
    try:
        # supabase-py v2에서는 upsert 체인에 select가 없을 수 있음 → upsert 후 별도 select 수행
        resp = (
            supabase_admin
                .table("users")
                .upsert([user_data], on_conflict="id")
                .execute()
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        print('[DEBUG] upsert payload on error =', user_data)
        raise HTTPException(status_code=500, detail={"message": "supabase upsert failed", "error": str(e)})

    # upsert 결과 대신, 항상 id로 최신 레코드 재조회 (클라이언트/버전 차이 안전성 확보)
    try:
        sel = (
            supabase_admin
                .table("users")
                .select("*")
                .eq("id", user_data["id"]) 
                .limit(1)
                .execute()
        )
        data = getattr(sel, "data", None) or []
    except Exception as e:
        import traceback; traceback.print_exc()
        print('[DEBUG] select after upsert failed:', str(e))
        data = []

    row = (data[0] if data else {}) or {}
    return {
        "id": row.get("id", fixed_id),
        "email": row.get("email", user_data.get("email","")),
        "name": row.get("nickname", user_data.get("nickname","")),
        "profile_image": row.get("profile_image_url", user_data.get("profile_image_url","")),
        "provider": row.get("provider", user_data.get("provider","")),
    }


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    samesite = os.getenv("COOKIE_SAMESITE", "lax")  # "lax" | "none" | "strict"
    domain = os.getenv("COOKIE_DOMAIN") or None
    # Align cookie lifetimes with JWT lifetimes (approx.)
    access_max_age = ACCESS_TOKEN_EXP_MINUTES * 60
    refresh_max_age = REFRESH_TOKEN_EXP_DAYS * 24 * 60 * 60

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=access_max_age,
        domain=domain,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=refresh_max_age,
        domain=domain,
        path="/",
    )


@router.post("/google")
async def google_login(payload: GoogleAccessRequest, response: Response):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {payload.access_token}"},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Google access token")
        profile = r.json()

    # 구글 userinfo는 보통 sub가 안정적인 id
    profile["provider"] = "google"
    profile["id"] = profile.get("sub") or profile.get("id")
    user = await _upsert_user(profile)
    print('[DEBUG] user for token', user)

    try:
        access = create_access_token(user["id"], {"email": user["email"], "name": user["name"]})
        refresh = create_refresh_token(user["id"])
        print('[DEBUG] tokens created')
        _set_auth_cookies(response, access, refresh)
        print('[DEBUG] cookies set')
    except Exception as e:
        import traceback; traceback.print_exc()
        print('[DEBUG] token/cookie error:', str(e))
        raise
    access = create_access_token(user["id"], {"email": user["email"], "name": user["name"]})
    refresh = create_refresh_token(user["id"])
    _set_auth_cookies(response, access, refresh)
    # 응답 본문으로도 계속 반환 (프론트 호환성 유지)
    return {"accessToken": access, "refreshToken": refresh, "user": user}


@router.post("/kakao")
async def kakao_login(payload: KakaoAccessRequest, response: Response):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {payload.access_token}"},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Kakao access token")
        data = r.json()
        kakao_account = data.get("kakao_account", {})
        profile = {
            "id": str(data.get("id")),
            "email": kakao_account.get("email", ""),
            "name": kakao_account.get("profile", {}).get("nickname", ""),
            "picture": kakao_account.get("profile", {}).get("profile_image_url", ""),
            "provider": "kakao",
        }

    user = await _upsert_user(profile)
    print('[DEBUG] user for token', user)
    try:
        access = create_access_token(user["id"], {"email": user["email"], "name": user["name"]})
        refresh = create_refresh_token(user["id"])
        print('[DEBUG] tokens created')
        _set_auth_cookies(response, access, refresh)
        print('[DEBUG] cookies set')
    except Exception as e:
        import traceback; traceback.print_exc()
        print('[DEBUG] token/cookie error:', str(e))
        raise
    # 카카오는 JSON을 반환 (프론트가 setAuth 처리)
    return {"accessToken": access, "refreshToken": refresh, "user": user}


@router.get("/naver/callback")
async def naver_callback(code: str, state: str, request: Request, response: Response):
    client_id = os.getenv("NAVER_CLIENT_ID") or os.getenv("VITE_NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET") or os.getenv("VITE_NAVER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Naver OAuth not configured")

    # 토큰 교환
    async with httpx.AsyncClient(timeout=10) as client:
        token_res = await client.post(
            "https://nid.naver.com/oauth2.0/token",
            params={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "state": state,
                "redirect_uri": str(request.url)
            },
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail={"message": "Invalid Naver code/state", "naver": token_data})

        # 프로필 조회
        profile_res = await client.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp = profile_res.json().get("response", {})
        profile = {
            "id": resp.get("id"),
            "email": resp.get("email", ""),
            "name": resp.get("name") or resp.get("nickname") or "",
            "picture": resp.get("profile_image", ""),
            "provider": "naver",
        }

    # 사용자 upsert 및 토큰/쿠키
    user = await _upsert_user(profile)
    access = create_access_token(user["id"], {"email": user["email"], "name": user["name"]})
    refresh = create_refresh_token(user["id"])
    _set_auth_cookies(response, access, refresh)

    # 브릿지 HTML: 메인 창에 알리고 닫기
    target_origin = os.getenv("FRONTEND_DOMAIN", "").rstrip("/") or "*"
    payload = {"source": "naver_oauth", "type": "success"}
    html = f"""
<!doctype html><meta charset=\"utf-8\"><title>Naver Login</title>
<script>
(function() {{
  try {{
    var target = {json.dumps(target_origin)};
    var payload = {json.dumps(payload)};
    if (window.opener && window.opener !== window) {{
      window.opener.postMessage(payload, target === '' ? '*' : target);
    }}
  }} catch(e) {{}}
  // try {{ window.close(); }} catch(e) {{}}  // 디버깅용 주석 처리
}})();
</script>
"""
    return HTMLResponse(content=html, media_type="text/html")


@router.post("/naver")
async def naver_login(payload: NaverCodeRequest, response: Response):
    # Support both backend and Vite-style env names
    client_id = os.getenv("NAVER_CLIENT_ID") or os.getenv("VITE_NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET") or os.getenv("VITE_NAVER_CLIENT_SECRET", "")
    print(f"client_id: {client_id}")
    print(f"client_secret: {client_secret}")
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Naver OAuth not configured")

    async with httpx.AsyncClient(timeout=10) as client:
        # 1) 토큰 교환
        token_res = await client.post(
            "https://nid.naver.com/oauth2.0/token",
            params={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": payload.code,
                "state": payload.state,
                "redirect_uri": payload.redirect_uri,
            },
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            # Bubble up naver error for easier debugging
            raise HTTPException(status_code=400, detail={"message": "Invalid Naver code/state", "naver": token_data})

        # 2) 사용자 정보
        print('[DEBUG] step=token_ok')
        profile_res = await client.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        try:
            print('[DEBUG] step=profile_status', profile_res.status_code)
            print('[DEBUG] step=profile_body', await profile_res.aread())
            profile_json = profile_res.json()
        except Exception:
            raise HTTPException(status_code=502, detail="Failed to parse Naver profile response")
        resp = profile_json.get("response", {})
        profile = {
            "id": resp.get("id"),
            "email": resp.get("email", ""),
            "name": resp.get("name") or resp.get("nickname") or "",
            "picture": resp.get("profile_image", ""),
            "provider": "naver",
        }

    user = await _upsert_user(profile)
    print('[DEBUG] user for token', user)
    try:
        access = create_access_token(user["id"], {"email": user["email"], "name": user["name"]})
        refresh = create_refresh_token(user["id"])
        print('[DEBUG] tokens created')
        _set_auth_cookies(response, access, refresh)
        print('[DEBUG] cookies set')
    except Exception as e:
        import traceback; traceback.print_exc()
        print('[DEBUG] token/cookie error:', str(e))
        raise
    return {"accessToken": access, "refreshToken": refresh, "user": user}


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


@router.post("/refresh")
async def refresh_token(payload: RefreshRequest, request: Request, response: Response):
    try:
        token = payload.refresh_token or request.cookies.get("refresh_token")
        if not token:
            raise HTTPException(status_code=401, detail="Missing refresh token")
        
        # 토큰 디코딩 및 검증
        data = decode_token(token)
        if data.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        
        user_id = data.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token payload")
        
        # 사용자 정보 조회 (토큰에 포함할 claims 준비)
        user_response = supabase_admin.table("users").select("email, nickname").eq("id", user_id).execute()
        user_claims = {}
        if user_response.data:
            user_data = user_response.data[0]
            user_claims = {
                "email": user_data.get("email"),
                "name": user_data.get("nickname") or user_data.get("email", "").split("@")[0]
            }
        
        # 새로운 토큰들 생성
        access = create_access_token(user_id, user_claims)
        refresh = create_refresh_token(user_id)
        
        # 쿠키에 새로운 토큰들 설정
        _set_auth_cookies(response, access, refresh)
        
        # 응답 본문으로도 반환 (프론트엔드 호환성)
        return {"accessToken": access, "refreshToken": refresh}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception as e:
        print(f"Refresh token error: {e}")
        raise HTTPException(status_code=401, detail="Token refresh failed")


@router.post("/test-token")
async def test_token(request: Request):
    """토큰 상태 테스트용 엔드포인트"""
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    auth_header = request.headers.get("Authorization")
    
    result = {
        "cookies": {
            "access_token": bool(access_token),
            "refresh_token": bool(refresh_token),
            "access_length": len(access_token) if access_token else 0,
            "refresh_length": len(refresh_token) if refresh_token else 0
        },
        "headers": {
            "authorization": bool(auth_header),
            "auth_length": len(auth_header) if auth_header else 0
        }
    }
    
    # 토큰 디코딩 시도
    try:
        if refresh_token:
            refresh_data = decode_token(refresh_token)
            result["refresh_valid"] = True
            result["refresh_exp"] = refresh_data.get("exp")
            result["refresh_type"] = refresh_data.get("type")
            result["refresh_user_id"] = refresh_data.get("sub")
        else:
            result["refresh_valid"] = False
    except Exception as e:
        result["refresh_valid"] = False
        result["refresh_error"] = str(e)
    
    try:
        if access_token:
            access_data = decode_token(access_token)
            result["access_valid"] = True
            result["access_exp"] = access_data.get("exp")
            result["access_type"] = access_data.get("type")
            result["access_user_id"] = access_data.get("sub")
        else:
            result["access_valid"] = False
    except Exception as e:
        result["access_valid"] = False
        result["access_error"] = str(e)
    
    return result

@router.post("/logout")
async def logout(response: Response):
    # 쿠키 삭제 (도메인/설정 일치 필요)
    domain = os.getenv("COOKIE_DOMAIN") or None
    response.delete_cookie(key="access_token", domain=domain, path="/")
    response.delete_cookie(key="refresh_token", domain=domain, path="/")
    return {"ok": True}

