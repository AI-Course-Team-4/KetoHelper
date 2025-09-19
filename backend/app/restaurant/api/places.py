"""
장소 검색 API 엔드포인트
카카오 로컬 API 통합 및 키토 스코어 계산
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.shared.models.schemas import PlaceSearchRequest, PlaceResponse
from app.restaurant.tools.place_search import PlaceSearchTool
from app.meal.tools.keto_score import KetoScoreCalculator

router = APIRouter(prefix="/places", tags=["places"])

@router.get("/", response_model=List[PlaceResponse])
async def search_places(
    q: str = Query(..., description="검색 키워드"),
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    radius: int = Query(1000, description="검색 반경(m)"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    db: AsyncSession = Depends(get_db)
):
    """
    키토 친화적인 장소 검색
    
    카카오 로컬 API를 통해 주변 식당을 검색하고,
    키토 스코어를 계산하여 정렬된 결과를 반환합니다.
    
    Args:
        q: 검색 키워드 (예: "구이", "샤브샤브", "샐러드")
        lat: 위도
        lng: 경도  
        radius: 검색 반경(미터)
        category: 카테고리 필터 (선택)
    
    Returns:
        키토 스코어 순으로 정렬된 장소 목록
    """
    try:
        # 장소 검색 도구 실행
        search_tool = PlaceSearchTool()
        places = await search_tool.search(
            query=q,
            lat=lat,
            lng=lng,
            radius=radius,
            category=category
        )
        
        # 키토 스코어 계산 및 정렬
        score_calculator = KetoScoreCalculator()
        scored_places = []
        
        for place in places:
            score_result = score_calculator.calculate_score(
                name=place.get("name", ""),
                category=place.get("category", ""),
                address=place.get("address", "")
            )
            
            scored_places.append(PlaceResponse(
                place_id=place.get("id", ""),
                name=place.get("name", ""),
                address=place.get("address", ""),
                category=place.get("category", ""),
                lat=place.get("lat", 0.0),
                lng=place.get("lng", 0.0),
                keto_score=score_result["score"],
                why=score_result["reasons"],
                tips=score_result["tips"]
            ))
        
        # 키토 스코어 순으로 정렬 (높은 순)
        scored_places.sort(key=lambda x: x.keto_score, reverse=True)
        
        return scored_places
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"장소 검색 중 오류 발생: {str(e)}"
        )

@router.get("/categories")
async def get_categories():
    """
    지원하는 카테고리 목록 반환
    키토 친화적인 음식 카테고리들
    """
    return {
        "categories": [
            {"code": "meat", "name": "고기구이", "description": "삼겹살, 갈비, 스테이크 등"},
            {"code": "shabu", "name": "샤브샤브", "description": "무제한 채소와 고기"},
            {"code": "salad", "name": "샐러드", "description": "신선한 채소 위주"},
            {"code": "seafood", "name": "해산물", "description": "회, 조개구이, 생선구이"},
            {"code": "chicken", "name": "닭요리", "description": "치킨, 닭갈비 등"},
            {"code": "hotpot", "name": "전골", "description": "부대찌개, 김치찌개 등"},
            {"code": "western", "name": "양식", "description": "스테이크, 치즈 요리"},
        ]
    }

@router.get("/nearby")
async def get_nearby_keto_places(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    radius: int = Query(1000, description="검색 반경(m)"),
    min_score: int = Query(70, description="최소 키토 스코어"),
    db: AsyncSession = Depends(get_db)
):
    """
    주변 키토 친화적인 장소들을 자동으로 검색
    키토 스코어가 높은 장소들만 필터링하여 반환
    """
    try:
        search_tool = PlaceSearchTool()
        
        # 키토 친화적인 키워드들로 검색
        keto_keywords = ["구이", "샤브샤브", "샐러드", "스테이크", "회"]
        all_places = []
        
        for keyword in keto_keywords:
            places = await search_tool.search(
                query=keyword,
                lat=lat,
                lng=lng,
                radius=radius
            )
            
            # 키토 스코어 계산
            score_calculator = KetoScoreCalculator()
            for place in places:
                score_result = score_calculator.calculate_score(
                    name=place.get("name", ""),
                    category=place.get("category", ""),
                    address=place.get("address", "")
                )
                
                # 최소 스코어 이상인 경우만 추가
                if score_result["score"] >= min_score:
                    place_response = PlaceResponse(
                        place_id=place.get("id", ""),
                        name=place.get("name", ""),
                        address=place.get("address", ""),
                        category=place.get("category", ""),
                        lat=place.get("lat", 0.0),
                        lng=place.get("lng", 0.0),
                        keto_score=score_result["score"],
                        why=score_result["reasons"],
                        tips=score_result["tips"]
                    )
                    all_places.append(place_response)
        
        # 중복 제거 (place_id 기준)
        unique_places = {}
        for place in all_places:
            if place.place_id not in unique_places:
                unique_places[place.place_id] = place
            elif place.keto_score > unique_places[place.place_id].keto_score:
                unique_places[place.place_id] = place
        
        # 키토 스코어 순으로 정렬
        result_places = list(unique_places.values())
        result_places.sort(key=lambda x: x.keto_score, reverse=True)
        
        return {
            "places": result_places[:20],  # 상위 20개만 반환
            "total_found": len(result_places),
            "search_radius": radius,
            "min_score": min_score
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"주변 키토 장소 검색 중 오류 발생: {str(e)}"
        )