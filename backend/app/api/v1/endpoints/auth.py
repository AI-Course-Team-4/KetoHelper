from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
security = HTTPBearer()

# Request/Response 모델들
class GoogleLoginRequest(BaseModel):
    token: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    profile_image: Optional[str] = None

@router.post("/google", response_model=LoginResponse, summary="Google OAuth 로그인")
async def google_login(request: GoogleLoginRequest):
    """
    Google OAuth 토큰을 사용하여 로그인합니다.
    
    - **token**: Google OAuth 액세스 토큰
    """
    # TODO: Google OAuth 토큰 검증 및 사용자 정보 추출
    # TODO: JWT 토큰 생성
    # TODO: 사용자 정보 저장/업데이트
    
    # 임시 응답
    return {
        "access_token": "temporary_jwt_token",
        "token_type": "bearer",
        "user": {
            "id": "temp_user_id",
            "email": "user@example.com",
            "name": "테스트 사용자",
            "profile_image": None
        }
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
async def get_current_user(token: str = Depends(security)):
    """
    현재 로그인한 사용자의 정보를 반환합니다.
    
    - **Authorization**: Bearer JWT 토큰
    """
    # TODO: JWT 토큰 검증 및 사용자 정보 조회
    
    # 임시 응답
    return {
        "id": "temp_user_id",
        "email": "user@example.com",
        "name": "테스트 사용자",
        "profile_image": None
    }

@router.patch("/profile", response_model=UserProfile, summary="프로필 업데이트")
async def update_profile(
    profile_data: dict,
    token: str = Depends(security)
):
    """
    사용자 프로필 정보를 업데이트합니다.
    
    - **Authorization**: Bearer JWT 토큰
    - **profile_data**: 업데이트할 프로필 정보
    """
    # TODO: JWT 토큰 검증
    # TODO: 프로필 정보 업데이트
    
    return {
        "id": "temp_user_id",
        "email": "user@example.com",
        "name": profile_data.get("name", "테스트 사용자"),
        "profile_image": profile_data.get("profile_image")
    }
