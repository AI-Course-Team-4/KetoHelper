from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import httpx
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()

# Request/Response 모델들
class GoogleLoginRequest(BaseModel):
    token: str

class GoogleAccessLoginRequest(BaseModel):
    access_token: str

class KakaoLoginRequest(BaseModel):
    token: str

class NaverCallbackRequest(BaseModel):
    code: str
    state: str
    redirect_uri: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    profile_image: Optional[str] = None


# JWT helpers
def create_access_token(claims: Dict[str, Any]) -> str:
    to_encode = claims.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 액세스 토큰입니다.")

@router.post("/google", summary="Google OAuth 로그인")
async def google_login(request: GoogleLoginRequest):
    """
    Google ID 토큰을 검증하고 사용자 정보를 반환합니다.

    - token: Google ID Token (JWT)
    """
    try:
        # Google tokeninfo로 ID 토큰 검증 및 클레임 조회
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            resp = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": request.token},
            )
        if resp.status_code != 200:
            return {
                "success": False,
                "message": "유효하지 않은 Google ID 토큰입니다.",
                "data": None,
            }
        claims = resp.json()
        # claims 예: {"sub": "...", "email": "...", "name": "...", "picture": "..."}
        user = {
            "id": claims.get("sub"),
            "email": claims.get("email"),
            "name": claims.get("name"),
            "profile_image": claims.get("picture"),
        }
        # 기본 구독 설정(없으면 프리미엄 활성 기본값)
        user.setdefault("subscription", {"isActive": True, "plan": "premium", "autoRenewal": True})
        # 서버 발급 JWT 생성 (우리 서비스용 토큰)
        server_token = create_access_token(
            {
                "sub": user["id"],
                "email": user.get("email"),
                "name": user.get("name"),
                "profile_image": user.get("profile_image"),
                "provider": "google",
            }
        )
        return {"success": True, "data": {"accessToken": server_token, "user": user}}
    except Exception as e:
        return {
            "success": False,
            "message": "로그인 처리 중 오류가 발생했습니다.",
            "data": None,
        }

@router.post("/google/access", summary="Google OAuth 로그인 (Access Token)")
async def google_access_login(request: GoogleAccessLoginRequest):
    """
    Google OAuth Access Token으로 사용자 정보를 조회하고 서버 JWT를 발급합니다.

    - access_token: Google OAuth Access Token
    """
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {request.access_token}"},
            )
        if resp.status_code != 200:
            return {
                "success": False,
                "message": "유효하지 않은 Google Access Token입니다.",
                "data": None,
            }
        info = resp.json()
        user = {
            "id": info.get("sub"),
            "email": info.get("email"),
            "name": info.get("name"),
            "profile_image": info.get("picture"),
        }
        # 기본 구독 설정(없으면 프리미엄 활성 기본값)
        user.setdefault("subscription", {"isActive": True, "plan": "premium", "autoRenewal": True})
        server_token = create_access_token(
            {
                "sub": user["id"],
                "email": user.get("email"),
                "name": user.get("name"),
                "profile_image": user.get("profile_image"),
                "provider": "google",
            }
        )
        return {"success": True, "data": {"accessToken": server_token, "user": user}}
    except Exception as e:
        return {
            "success": False,
            "message": ("구글 액세스 로그인 처리 중 오류가 발생했습니다." + (f" 상세: {e}" if settings.DEBUG else "")),
            "data": None,
        }

@router.post("/kakao", summary="Kakao OAuth 로그인")
async def kakao_login(request: KakaoLoginRequest):
    """
    Kakao Access Token을 검증하고 사용자 정보를 반환합니다.

    - token: Kakao Access Token
    """
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            resp = await client.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {request.token}"},
            )
        if resp.status_code != 200:
            return {
                "success": False,
                "message": "유효하지 않은 Kakao 액세스 토큰입니다.",
                "data": None,
            }
        kakao_user = resp.json()
        kakao_account = kakao_user.get("kakao_account", {}) or {}
        profile = kakao_account.get("profile", {}) or kakao_user.get("properties", {}) or {}

        user = {
            "id": str(kakao_user.get("id")),
            "email": kakao_account.get("email"),
            "name": profile.get("nickname"),
            "profile_image": profile.get("profile_image_url")
                or profile.get("thumbnail_image_url")
                or profile.get("profile_image"),
        }
        # 기본 구독 설정(없으면 프리미엄 활성 기본값)
        user.setdefault("subscription", {"isActive": True, "plan": "premium", "autoRenewal": True})
        # 서버 발급 JWT 생성 (우리 서비스용 토큰)
        server_token = create_access_token(
            {
                "sub": user["id"],
                "email": user.get("email"),
                "name": user.get("name"),
                "profile_image": user.get("profile_image"),
                "provider": "kakao",
            }
        )
        return {"success": True, "data": {"accessToken": server_token, "user": user}}
    except Exception:
        return {
            "success": False,
            "message": "카카오 로그인 처리 중 오류가 발생했습니다.",
            "data": None,
        }

@router.post("/naver", summary="Naver OAuth 로그인(코드 교환)")
async def naver_login(request: NaverCallbackRequest):
    """
    Naver Authorization Code를 Access Token으로 교환하고 사용자 정보를 반환합니다.

    - code: Authorization Code
    - state: CSRF 방지용 랜덤 문자열
    - redirect_uri: 프론트에서 사용한 콜백 URI (선택, 권장)
    """
    try:
        client_id = settings.NAVER_CLIENT_ID
        client_secret = settings.NAVER_CLIENT_SECRET
        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="네이버 클라이언트 설정이 누락되었습니다.")

        token_params = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": request.code,
            "state": request.state,
        }
        if request.redirect_uri:
            token_params["redirect_uri"] = request.redirect_uri

        # Naver sometimes requires URL-encoded redirect_uri match; ensure exact encoding
        if token_params.get("redirect_uri"):
            token_params["redirect_uri"] = token_params["redirect_uri"]

        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            token_resp = await client.get("https://nid.naver.com/oauth2.0/token", params=token_params)
        if token_resp.status_code != 200:
            error_text = None
            try:
                error_text = token_resp.text
            except Exception:
                error_text = None
            return {
                "success": False,
                "message": (
                    "네이버 토큰 교환에 실패했습니다." + (f" 상세: {error_text}" if settings.DEBUG and error_text else "")
                ),
                "data": None,
            }
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return {
                "success": False,
                "message": (
                    "네이버 액세스 토큰이 없습니다." + (f" 상세: {token_data}" if settings.DEBUG else "")
                ),
                "data": None,
            }

        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            user_resp = await client.get(
                "https://openapi.naver.com/v1/nid/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if user_resp.status_code != 200:
            user_error = None
            try:
                user_error = user_resp.text
            except Exception:
                user_error = None
            return {
                "success": False,
                "message": (
                    "네이버 사용자 정보 조회에 실패했습니다." + (f" 상세: {user_error}" if settings.DEBUG and user_error else "")
                ),
                "data": None,
            }
        naver_payload = user_resp.json() or {}
        response = naver_payload.get("response", {})
        user = {
            "id": response.get("id"),
            "email": response.get("email"),
            "name": response.get("name") or response.get("nickname"),
            "profile_image": response.get("profile_image"),
        }
        # 기본 구독 설정(없으면 프리미엄 활성 기본값)
        user.setdefault("subscription", {"isActive": True, "plan": "premium", "autoRenewal": True})

        server_token = create_access_token(
            {
                "sub": user.get("id"),
                "email": user.get("email"),
                "name": user.get("name"),
                "profile_image": user.get("profile_image"),
                "provider": "naver",
            }
        )
        return {"success": True, "data": {"accessToken": server_token, "user": user}}
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "message": (
                "네이버 로그인 처리 중 오류가 발생했습니다." + (f" 상세: {e}" if settings.DEBUG else "")
            ),
            "data": None,
        }

@router.post("/logout", summary="로그아웃")
async def logout(token: str = Depends(security)):
    """
    사용자 로그아웃을 처리합니다.
    
    - **Authorization**: Bearer JWT 토큰
    """
    # TODO: 토큰 블랙리스트 처리
    return {"message": "로그아웃되었습니다"}

@router.get("/me", response_model=UserProfile, summary="현재 사용자 정보")
async def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    """
    현재 로그인한 사용자의 정보를 반환합니다.
    
    - **Authorization**: Bearer JWT 토큰
    """
    # 서버 발급 JWT 검증 후 사용자 정보 반환
    claims = decode_access_token(token.credentials)
    return {
        "id": claims.get("sub"),
        "email": claims.get("email"),
        "name": claims.get("name"),
        "profile_image": claims.get("profile_image"),
    }

@router.patch("/profile", response_model=UserProfile, summary="프로필 업데이트")
async def update_profile(
    profile_data: dict,
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """
    사용자 프로필 정보를 업데이트합니다.
    
    - **Authorization**: Bearer JWT 토큰
    - **profile_data**: 업데이트할 프로필 정보
    """
    # 서버 발급 JWT 검증 (DB 저장 로직 추가 시 여기에서 업데이트 반영)
    claims = decode_access_token(token.credentials)
    return {
        "id": claims.get("sub"),
        "email": claims.get("email"),
        "name": profile_data.get("name", claims.get("name")),
        "profile_image": profile_data.get("profile_image", claims.get("profile_image")),
    }
