from fastapi import APIRouter, Query, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
security = HTTPBearer()

# Response 모델들
class NutritionInfo(BaseModel):
    calories: int
    carbs: float
    protein: float
    fat: float
    fiber: float

class Recipe(BaseModel):
    id: str
    title: str
    description: str
    image_url: str
    cooking_time: int
    difficulty: str
    servings: int
    nutrition: NutritionInfo
    tags: List[str]
    rating: float
    review_count: int
    is_keto_friendly: bool

class PaginatedRecipes(BaseModel):
    items: List[Recipe]
    total: int
    page: int
    page_size: int
    total_pages: int

class RecommendationRequest(BaseModel):
    preferences: Optional[dict] = None
    filters: Optional[dict] = None
    context: Optional[str] = None

# 임시 데이터
SAMPLE_RECIPES = [
    {
        "id": "1",
        "title": "아보카도 베이컨 샐러드",
        "description": "신선한 아보카도와 바삭한 베이컨이 만나는 완벽한 키토 샐러드",
        "image_url": "https://via.placeholder.com/300x200",
        "cooking_time": 15,
        "difficulty": "easy",
        "servings": 2,
        "nutrition": {
            "calories": 380,
            "carbs": 8.0,
            "protein": 15.0,
            "fat": 32.0,
            "fiber": 6.0
        },
        "tags": ["키토", "샐러드", "아보카도", "베이컨"],
        "rating": 4.5,
        "review_count": 128,
        "is_keto_friendly": True
    },
    {
        "id": "2",
        "title": "치킨 크림 스프",
        "description": "부드럽고 진한 크림 스프로 포만감을 주는 키토 요리",
        "image_url": "https://via.placeholder.com/300x200",
        "cooking_time": 30,
        "difficulty": "medium",
        "servings": 4,
        "nutrition": {
            "calories": 420,
            "carbs": 6.0,
            "protein": 28.0,
            "fat": 30.0,
            "fiber": 2.0
        },
        "tags": ["키토", "스프", "치킨", "크림"],
        "rating": 4.8,
        "review_count": 89,
        "is_keto_friendly": True
    }
]

@router.get("/", response_model=PaginatedRecipes, summary="레시피 목록 조회")
async def get_recipes(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    meal_type: Optional[str] = Query(None, description="식사 시간"),
    difficulty: Optional[str] = Query(None, description="난이도"),
    cooking_time: Optional[int] = Query(None, description="최대 조리 시간")
):
    """
    레시피 목록을 페이지네이션으로 조회합니다.
    
    - **page**: 페이지 번호 (1부터 시작)
    - **page_size**: 한 페이지당 항목 수
    - **meal_type**: breakfast, lunch, dinner, snack
    - **difficulty**: easy, medium, hard
    - **cooking_time**: 최대 조리 시간(분)
    """
    # TODO: 실제 데이터베이스에서 필터링된 레시피 조회
    
    total = len(SAMPLE_RECIPES)
    start = (page - 1) * page_size
    end = start + page_size
    items = SAMPLE_RECIPES[start:end]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/{recipe_id}", response_model=Recipe, summary="레시피 상세 조회")
async def get_recipe(recipe_id: str):
    """
    특정 레시피의 상세 정보를 조회합니다.
    
    - **recipe_id**: 레시피 ID
    """
    # TODO: 데이터베이스에서 레시피 조회
    
    # 임시로 첫 번째 레시피 반환
    if SAMPLE_RECIPES:
        recipe = SAMPLE_RECIPES[0].copy()
        recipe["id"] = recipe_id
        return recipe
    
    return {"error": "레시피를 찾을 수 없습니다"}

@router.post("/recommendations", summary="AI 기반 레시피 추천")
async def get_recipe_recommendations(
    request: RecommendationRequest,
    token: Optional[str] = Depends(security)
):
    """
    AI를 사용하여 개인화된 레시피를 추천합니다.
    
    - **Authorization**: Bearer JWT 토큰 (선택사항)
    - **preferences**: 사용자 선호도
    - **filters**: 추가 필터 조건
    - **context**: 추천 컨텍스트
    """
    # TODO: RAG 시스템을 사용한 레시피 추천
    # TODO: 사용자 선호도 및 알레르기 정보 고려
    
    return {
        "recommendations": SAMPLE_RECIPES,
        "reasoning": "사용자의 키토 경험 레벨과 선호도를 바탕으로 추천했습니다.",
        "confidence": 0.85
    }

@router.get("/search", response_model=PaginatedRecipes, summary="레시피 검색")
async def search_recipes(
    q: str = Query(..., description="검색 키워드"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    키워드로 레시피를 검색합니다.
    
    - **q**: 검색 키워드
    - **page**: 페이지 번호
    - **page_size**: 페이지 크기
    """
    # TODO: 텍스트 검색 및 벡터 검색 구현
    
    # 임시로 모든 레시피 반환
    return {
        "items": SAMPLE_RECIPES,
        "total": len(SAMPLE_RECIPES),
        "page": page,
        "page_size": page_size,
        "total_pages": 1
    }

@router.get("/popular", response_model=List[Recipe], summary="인기 레시피")
async def get_popular_recipes(limit: int = Query(10, ge=1, le=50)):
    """
    인기 레시피 목록을 조회합니다.
    
    - **limit**: 반환할 레시피 수
    """
    # TODO: 평점과 리뷰 수를 기준으로 인기 레시피 조회
    
    return SAMPLE_RECIPES[:limit]

@router.post("/{recipe_id}/favorite", summary="레시피 즐겨찾기 토글")
async def toggle_recipe_favorite(
    recipe_id: str,
    token: str = Depends(security)
):
    """
    레시피를 즐겨찾기에 추가하거나 제거합니다.
    
    - **recipe_id**: 레시피 ID
    - **Authorization**: Bearer JWT 토큰
    """
    # TODO: JWT 토큰 검증
    # TODO: 사용자의 즐겨찾기 목록 업데이트
    
    return {"is_favorite": True}
