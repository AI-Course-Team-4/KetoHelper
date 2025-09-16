from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
security = HTTPBearer()

class UserPreferences(BaseModel):
    allergies: List[str] = []
    dislikes: List[str] = []
    dietary_restrictions: List[str] = []
    experience_level: str = "beginner"
    target_weight: Optional[float] = None
    target_calories: int = 2000
    macro_ratio: dict = {"carbs": 5, "protein": 20, "fat": 75}

class UserSettings(BaseModel):
    notifications: dict = {
        "meal_reminders": True,
        "recommendations": True,
        "weekly_report": False
    }
    units: str = "metric"

class User(BaseModel):
    id: str
    email: str
    name: str
    profile_image: Optional[str] = None
    preferences: UserPreferences
    settings: UserSettings

@router.get("/me", response_model=User, summary="현재 사용자 정보")
async def get_current_user(token: str = Depends(security)):
    """
    현재 로그인한 사용자의 상세 정보를 조회합니다.
    
    - **Authorization**: Bearer JWT 토큰
    """
    # TODO: JWT 토큰 검증 및 사용자 정보 조회
    
    return {
        "id": "temp_user_id",
        "email": "user@example.com",
        "name": "테스트 사용자",
        "profile_image": None,
        "preferences": {
            "allergies": ["견과류"],
            "dislikes": ["버섯"],
            "dietary_restrictions": [],
            "experience_level": "beginner",
            "target_weight": 70.0,
            "target_calories": 1800,
            "macro_ratio": {"carbs": 5, "protein": 25, "fat": 70}
        },
        "settings": {
            "notifications": {
                "meal_reminders": True,
                "recommendations": True,
                "weekly_report": False
            },
            "units": "metric"
        }
    }

@router.patch("/preferences", response_model=UserPreferences, summary="사용자 선호도 업데이트")
async def update_user_preferences(
    preferences: UserPreferences,
    token: str = Depends(security)
):
    """
    사용자의 식품 선호도 및 목표를 업데이트합니다.
    
    - **Authorization**: Bearer JWT 토큰
    - **preferences**: 업데이트할 선호도 정보
    """
    # TODO: JWT 토큰 검증
    # TODO: 사용자 선호도 업데이트
    # TODO: AI 추천 모델 재학습 트리거
    
    return preferences

@router.patch("/settings", response_model=UserSettings, summary="사용자 설정 업데이트")
async def update_user_settings(
    settings: UserSettings,
    token: str = Depends(security)
):
    """
    사용자의 알림 설정 등을 업데이트합니다.
    
    - **Authorization**: Bearer JWT 토큰
    - **settings**: 업데이트할 설정 정보
    """
    # TODO: JWT 토큰 검증
    # TODO: 사용자 설정 업데이트
    
    return settings

@router.get("/dashboard", summary="사용자 대시보드 데이터")
async def get_user_dashboard(token: str = Depends(security)):
    """
    사용자 대시보드에 표시할 통계 데이터를 조회합니다.
    
    - **Authorization**: Bearer JWT 토큰
    """
    # TODO: JWT 토큰 검증
    # TODO: 사용자 활동 통계 계산
    # TODO: 키토 진행률 계산
    
    return {
        "keto_progress": 75,
        "recipes_tried": 12,
        "restaurants_visited": 8,
        "weekly_summary": {
            "avg_carbs": 22,
            "avg_calories": 1750,
            "days_on_track": 5
        },
        "recent_activities": [
            {
                "type": "recipe_view",
                "title": "아보카도 베이컨 샐러드",
                "date": "2024-12-19"
            },
            {
                "type": "restaurant_visit",
                "title": "키토 스테이크하우스",
                "date": "2024-12-18"
            }
        ]
    }

@router.get("/favorites/recipes", summary="즐겨찾기 레시피 목록")
async def get_favorite_recipes(
    page: int = 1,
    page_size: int = 20,
    token: str = Depends(security)
):
    """
    사용자가 즐겨찾기에 추가한 레시피 목록을 조회합니다.
    
    - **Authorization**: Bearer JWT 토큰
    """
    # TODO: JWT 토큰 검증
    # TODO: 사용자의 즐겨찾기 레시피 조회
    
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
        "total_pages": 0
    }

@router.get("/favorites/restaurants", summary="즐겨찾기 식당 목록")
async def get_favorite_restaurants(
    page: int = 1,
    page_size: int = 20,
    token: str = Depends(security)
):
    """
    사용자가 즐겨찾기에 추가한 식당 목록을 조회합니다.
    
    - **Authorization**: Bearer JWT 토큰
    """
    # TODO: JWT 토큰 검증
    # TODO: 사용자의 즐겨찾기 식당 조회
    
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
        "total_pages": 0
    }

@router.delete("/account", summary="계정 삭제")
async def delete_user_account(token: str = Depends(security)):
    """
    사용자 계정과 모든 관련 데이터를 삭제합니다.
    
    - **Authorization**: Bearer JWT 토큰
    """
    # TODO: JWT 토큰 검증
    # TODO: 사용자 데이터 완전 삭제
    # TODO: 관련 활동 로그 삭제
    
    return {"message": "계정이 성공적으로 삭제되었습니다"}

@router.get("/export", summary="사용자 데이터 내보내기")
async def export_user_data(token: str = Depends(security)):
    """
    사용자의 모든 데이터를 JSON 형식으로 내보냅니다.
    
    - **Authorization**: Bearer JWT 토큰
    """
    # TODO: JWT 토큰 검증
    # TODO: 사용자 데이터 수집 및 익명화
    # TODO: JSON 파일 생성
    
    return {
        "export_url": "https://example.com/exports/user_data.json",
        "expires_at": "2024-12-26T00:00:00Z"
    }
