from fastapi import APIRouter, Query, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
security = HTTPBearer()

class MenuItem(BaseModel):
    name: str
    description: str
    price: int
    carbs: float
    is_keto_friendly: bool
    keto_modifications: List[str] = []

class Restaurant(BaseModel):
    id: str
    name: str
    address: str
    phone: str
    category: str
    price_range: int
    rating: float
    review_count: int
    keto_score: int
    distance: Optional[float] = None
    menu: List[MenuItem]
    images: List[str]

class PaginatedRestaurants(BaseModel):
    items: List[Restaurant]
    total: int
    page: int
    page_size: int
    total_pages: int

# 임시 데이터
SAMPLE_RESTAURANTS = [
    {
        "id": "1",
        "name": "키토 스테이크하우스",
        "address": "서울시 강남구 테헤란로 123",
        "phone": "02-1234-5678",
        "category": "스테이크",
        "price_range": 3,
        "rating": 4.5,
        "review_count": 128,
        "keto_score": 95,
        "distance": 0.8,
        "menu": [
            {
                "name": "립아이 스테이크",
                "description": "프리미엄 립아이 스테이크",
                "price": 45000,
                "carbs": 2.0,
                "is_keto_friendly": True,
                "keto_modifications": []
            },
            {
                "name": "연어 그릴",
                "description": "신선한 연어 그릴",
                "price": 32000,
                "carbs": 1.0,
                "is_keto_friendly": True,
                "keto_modifications": []
            }
        ],
        "images": ["https://via.placeholder.com/300x200"]
    },
    {
        "id": "2",
        "name": "아보카도 카페",
        "address": "서울시 강남구 신사동 456",
        "phone": "02-2345-6789",
        "category": "카페",
        "price_range": 2,
        "rating": 4.3,
        "review_count": 89,
        "keto_score": 88,
        "distance": 1.2,
        "menu": [
            {
                "name": "아보카도 샐러드",
                "description": "신선한 아보카도 샐러드",
                "price": 15000,
                "carbs": 8.0,
                "is_keto_friendly": True,
                "keto_modifications": ["드레싱 제외"]
            }
        ],
        "images": ["https://via.placeholder.com/300x200"]
    }
]

@router.get("/", response_model=PaginatedRestaurants, summary="식당 목록 조회")
async def get_restaurants(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    lat: Optional[float] = Query(None, description="위도"),
    lng: Optional[float] = Query(None, description="경도"),
    radius: Optional[float] = Query(5, description="검색 반경(km)"),
    category: Optional[str] = Query(None, description="음식 카테고리"),
    min_keto_score: Optional[int] = Query(None, description="최소 키토 점수")
):
    """
    식당 목록을 조회합니다.
    
    - **page**: 페이지 번호
    - **page_size**: 페이지 크기
    - **lat**: 위도 (위치 기반 검색)
    - **lng**: 경도 (위치 기반 검색)
    - **radius**: 검색 반경(km)
    - **category**: 음식 카테고리
    - **min_keto_score**: 최소 키토 점수
    """
    # TODO: 위치 기반 검색 구현
    # TODO: 카테고리 및 키토 점수 필터링
    
    total = len(SAMPLE_RESTAURANTS)
    start = (page - 1) * page_size
    end = start + page_size
    items = SAMPLE_RESTAURANTS[start:end]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/{restaurant_id}", response_model=Restaurant, summary="식당 상세 조회")
async def get_restaurant(restaurant_id: str):
    """
    특정 식당의 상세 정보를 조회합니다.
    
    - **restaurant_id**: 식당 ID
    """
    # TODO: 데이터베이스에서 식당 조회
    
    if SAMPLE_RESTAURANTS:
        restaurant = SAMPLE_RESTAURANTS[0].copy()
        restaurant["id"] = restaurant_id
        return restaurant
    
    return {"error": "식당을 찾을 수 없습니다"}

@router.get("/nearby", response_model=List[Restaurant], summary="근처 식당 조회")
async def get_nearby_restaurants(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    radius: float = Query(5, description="검색 반경(km)"),
    limit: int = Query(20, ge=1, le=100, description="최대 결과 수")
):
    """
    현재 위치 근처의 키토 친화적인 식당을 조회합니다.
    
    - **lat**: 위도
    - **lng**: 경도
    - **radius**: 검색 반경(km)
    - **limit**: 최대 결과 수
    """
    # TODO: 지리적 검색 쿼리 구현
    # TODO: 거리 계산 및 정렬
    
    return SAMPLE_RESTAURANTS[:limit]

@router.get("/search", response_model=PaginatedRestaurants, summary="식당 검색")
async def search_restaurants(
    q: str = Query(..., description="검색 키워드"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    lat: Optional[float] = Query(None, description="위도"),
    lng: Optional[float] = Query(None, description="경도"),
    radius: Optional[float] = Query(5, description="검색 반경(km)")
):
    """
    키워드로 식당을 검색합니다.
    
    - **q**: 검색 키워드 (식당명, 주소, 음식 종류 등)
    - **lat**: 위도 (위치 기반 검색)
    - **lng**: 경도 (위치 기반 검색)
    - **radius**: 검색 반경(km)
    """
    # TODO: 텍스트 검색 구현
    # TODO: 위치 기반 필터링
    
    return {
        "items": SAMPLE_RESTAURANTS,
        "total": len(SAMPLE_RESTAURANTS),
        "page": page,
        "page_size": page_size,
        "total_pages": 1
    }

@router.get("/keto-friendly", response_model=PaginatedRestaurants, summary="키토 친화적 식당")
async def get_keto_friendly_restaurants(
    min_score: int = Query(70, ge=0, le=100, description="최소 키토 점수"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    lat: Optional[float] = Query(None, description="위도"),
    lng: Optional[float] = Query(None, description="경도"),
    radius: Optional[float] = Query(5, description="검색 반경(km)")
):
    """
    키토 점수가 높은 식당들을 조회합니다.
    
    - **min_score**: 최소 키토 점수 (0-100)
    - **lat**: 위도
    - **lng**: 경도
    - **radius**: 검색 반경(km)
    """
    # TODO: 키토 점수 필터링
    # TODO: 위치 기반 검색
    
    filtered_restaurants = [r for r in SAMPLE_RESTAURANTS if r["keto_score"] >= min_score]
    
    return {
        "items": filtered_restaurants,
        "total": len(filtered_restaurants),
        "page": page,
        "page_size": page_size,
        "total_pages": 1
    }

@router.post("/{restaurant_id}/favorite", summary="식당 즐겨찾기 토글")
async def toggle_restaurant_favorite(
    restaurant_id: str,
    token: str = Depends(security)
):
    """
    식당을 즐겨찾기에 추가하거나 제거합니다.
    
    - **restaurant_id**: 식당 ID
    - **Authorization**: Bearer JWT 토큰
    """
    # TODO: JWT 토큰 검증
    # TODO: 사용자의 즐겨찾기 목록 업데이트
    
    return {"is_favorite": True}

@router.post("/analyze-menu", summary="메뉴 키토 적합성 분석")
async def analyze_menu(
    image_url: str,
    token: Optional[str] = Depends(security)
):
    """
    메뉴 이미지를 분석하여 키토 적합성을 평가합니다.
    
    - **image_url**: 메뉴 이미지 URL
    - **Authorization**: Bearer JWT 토큰 (선택사항)
    """
    # TODO: 이미지 분석 AI 모델 연동
    # TODO: 키토 적합성 점수 계산
    # TODO: 개선 제안 생성
    
    return {
        "keto_score": 85,
        "suggestions": [
            "밥을 제외하고 주문하세요",
            "드레싱을 따로 요청하세요",
            "추가 야채를 요청하세요"
        ]
    }

@router.get("/categories", response_model=List[str], summary="식당 카테고리 목록")
async def get_restaurant_categories():
    """
    사용 가능한 식당 카테고리 목록을 조회합니다.
    """
    return [
        "한식",
        "양식",
        "일식",
        "중식",
        "카페",
        "스테이크",
        "해산물",
        "샐러드",
        "이탈리안",
        "멕시칸"
    ]
