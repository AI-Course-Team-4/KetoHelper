from fastapi import APIRouter, Depends, HTTPException
from fastapi import Body
from pydantic import BaseModel
import httpx
import os
from app.core.jwt_utils import create_access_token, create_refresh_token, decode_token

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
    # TODO: 실제 DB와 연동하여 사용자 upsert
    # 여기서는 데모용으로 profile 그대로 반환
    return {
        "id": profile.get("id") or profile.get("sub") or profile.get("email") or "demo-user",
        "email": profile.get("email", ""),
        "name": profile.get("name") or profile.get("nickname") or "",
        "profile_image": profile.get("picture") or profile.get("profile_image") or "",
    }


@router.post("/google")
async def google_login(payload: GoogleAccessRequest):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {payload.access_token}"},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Google access token")
        profile = r.json()

    user = await _upsert_user(profile)
    access = create_access_token(user["id"], {"email": user["email"], "name": user["name"]})
    refresh = create_refresh_token(user["id"])
    return {"accessToken": access, "refreshToken": refresh, "user": user}


@router.post("/kakao")
async def kakao_login(payload: KakaoAccessRequest):
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
        }

    user = await _upsert_user(profile)
    access = create_access_token(user["id"], {"email": user["email"], "name": user["name"]})
    refresh = create_refresh_token(user["id"])
    return {"accessToken": access, "refreshToken": refresh, "user": user}


@router.post("/naver")
async def naver_login(payload: NaverCodeRequest):
    # Support both backend and Vite-style env names
    client_id = os.getenv("NAVER_CLIENT_ID") or os.getenv("VITE_NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET") or os.getenv("VITE_NAVER_CLIENT_SECRET", "")
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
        profile_res = await client.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        try:
            profile_json = profile_res.json()
        except Exception:
            raise HTTPException(status_code=502, detail="Failed to parse Naver profile response")
        resp = profile_json.get("response", {})
        profile = {
            "id": resp.get("id"),
            "email": resp.get("email", ""),
            "name": resp.get("name") or resp.get("nickname") or "",
            "picture": resp.get("profile_image", ""),
        }

    user = await _upsert_user(profile)
    access = create_access_token(user["id"], {"email": user["email"], "name": user["name"]})
    refresh = create_refresh_token(user["id"])
    return {"accessToken": access, "refreshToken": refresh, "user": user}


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
async def refresh_token(payload: RefreshRequest):
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        user_id = data.get("sub")
        access = create_access_token(user_id)
        return {"accessToken": access}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
async def logout():
    # 클라이언트 토큰 삭제는 프론트에서 처리.
    return {"ok": True}


