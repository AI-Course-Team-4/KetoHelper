"""
장소 검색 API 엔드포인트
카카오 로컬 API 통합 및 키토 스코어 계산
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
import math

from app.core.database import get_db
from app.shared.models.schemas import PlaceSearchRequest, PlaceResponse
from app.tools.restaurant.place_search import PlaceSearchTool
from app.tools.meal.keto_score import KetoScoreCalculator

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

@router.get("/high-keto-score")
async def get_high_keto_score_places(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    radius: int = Query(2000, description="검색 반경(m)"),
    min_score: int = Query(10, description="최소 키토 스코어 (기본값: 10)"),
    max_results: int = Query(50, description="최대 결과 수"),
    db: AsyncSession = Depends(get_db)
):
    """
    키토 점수 10점 이상인 주변 식당들을 검색
    내 위치 중심으로 반경 내의 키토 친화적인 식당들을 반환
    """
    try:
        search_tool = PlaceSearchTool()
        score_calculator = KetoScoreCalculator()
        
        # 다양한 키워드로 포괄적인 검색
        search_keywords = [
            "구이", "삼겹살", "갈비", "스테이크", "회", "해산물",
            "샤브샤브", "샐러드", "치킨", "닭갈비", "전골",
            "양식", "한식", "일식", "중식", "치즈", "버터"
        ]
        
        all_places = []
        
        # 각 키워드로 검색
        for keyword in search_keywords:
            try:
                places = await search_tool.search(
                    query=keyword,
                    lat=lat,
                    lng=lng,
                    radius=radius
                )
                
                # 키토 스코어 계산 및 필터링
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
                        
            except Exception as keyword_error:
                print(f"키워드 '{keyword}' 검색 중 오류: {keyword_error}")
                continue
        
        # 중복 제거 (place_id 기준) 및 최고 점수 유지
        unique_places = {}
        for place in all_places:
            if place.place_id not in unique_places:
                unique_places[place.place_id] = place
            elif place.keto_score > unique_places[place.place_id].keto_score:
                unique_places[place.place_id] = place
        
        # 키토 스코어 순으로 정렬 (높은 순)
        result_places = list(unique_places.values())
        result_places.sort(key=lambda x: x.keto_score, reverse=True)
        
        # 결과 제한
        limited_results = result_places[:max_results]
        
        return {
            "places": limited_results,
            "total_found": len(result_places),
            "search_radius": radius,
            "min_score": min_score,
            "user_location": {
                "lat": lat,
                "lng": lng
            },
            "score_distribution": {
                "excellent": len([p for p in result_places if p.keto_score >= 80]),
                "good": len([p for p in result_places if 60 <= p.keto_score < 80]),
                "fair": len([p for p in result_places if 40 <= p.keto_score < 60]),
                "poor": len([p for p in result_places if 10 <= p.keto_score < 40])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"키토 점수 기반 장소 검색 중 오류 발생: {str(e)}"
        )

@router.get("/database-search")
async def get_keto_places_from_database(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    radius: int = Query(2000, description="검색 반경(m)"),
    min_score: int = Query(10, description="최소 키토 스코어"),
    max_results: int = Query(50, description="최대 결과 수"),
    db: AsyncSession = Depends(get_db)
):
    """
    데이터베이스에서 직접 키토 점수 기반 식당 검색
    Supabase RPC 함수를 활용한 효율적인 위치 기반 검색
    """
    try:
        # 반경을 킬로미터로 변환
        radius_km = radius / 1000.0
        
        # Supabase RPC 함수 호출을 위한 SQL 쿼리
        query = text("""
            SELECT 
                r.id,
                r.name,
                COALESCE(r.addr_road, r.addr_jibun, '') as address,
                r.category,
                r.lat,
                r.lng,
                r.phone,
                COALESCE(AVG(ks.score), 0)::INTEGER as avg_keto_score,
                (6371 * acos(
                    cos(radians(:center_lat)) * cos(radians(r.lat)) * 
                    cos(radians(r.lng) - radians(:center_lng)) + 
                    sin(radians(:center_lat)) * sin(radians(r.lat))
                ))::DOUBLE PRECISION as distance_km
            FROM restaurant r
            LEFT JOIN menu m ON r.id = m.restaurant_id
            LEFT JOIN keto_scores ks ON m.id = ks.menu_id
            WHERE (6371 * acos(
                cos(radians(:center_lat)) * cos(radians(r.lat)) * 
                cos(radians(r.lng) - radians(:center_lng)) + 
                sin(radians(:center_lat)) * sin(radians(r.lat))
            )) <= :radius_km
            GROUP BY r.id, r.name, r.addr_road, r.addr_jibun, r.category, r.lat, r.lng, r.phone
            HAVING COALESCE(AVG(ks.score), 0) >= :min_score
            ORDER BY avg_keto_score DESC, distance_km ASC
            LIMIT :max_results
        """)
        
        result = await db.execute(query, {
            "center_lat": lat,
            "center_lng": lng,
            "radius_km": radius_km,
            "min_score": min_score,
            "max_results": max_results
        })
        
        rows = result.fetchall()
        
        # 결과를 PlaceResponse 형식으로 변환
        places = []
        for row in rows:
            # 키토 스코어 계산 (데이터베이스에 없는 경우)
            if row.avg_keto_score == 0:
                score_calculator = KetoScoreCalculator()
                score_result = score_calculator.calculate_score(
                    name=row.name,
                    category=row.category or "",
                    address=row.address
                )
                keto_score = score_result["score"]
                reasons = score_result["reasons"]
                tips = score_result["tips"]
            else:
                keto_score = row.avg_keto_score
                reasons = [f"평균 키토 점수: {keto_score}점"]
                tips = ["메뉴 선택 시 주의하세요"]
            
            place_response = PlaceResponse(
                place_id=str(row.id),
                name=row.name,
                address=row.address,
                category=row.category or "",
                lat=float(row.lat) if row.lat else 0.0,
                lng=float(row.lng) if row.lng else 0.0,
                keto_score=keto_score,
                why=reasons,
                tips=tips
            )
            places.append(place_response)
        
        # 점수 분포 계산
        score_distribution = {
            "excellent": len([p for p in places if p.keto_score >= 80]),
            "good": len([p for p in places if 60 <= p.keto_score < 80]),
            "fair": len([p for p in places if 40 <= p.keto_score < 60]),
            "poor": len([p for p in places if 10 <= p.keto_score < 40])
        }
        
        return {
            "places": places,
            "total_found": len(places),
            "search_radius": radius,
            "min_score": min_score,
            "user_location": {
                "lat": lat,
                "lng": lng
            },
            "score_distribution": score_distribution,
            "search_method": "database"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"데이터베이스 기반 키토 장소 검색 중 오류 발생: {str(e)}"
        )

@router.get("/location-info")
async def get_location_info(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    db: AsyncSession = Depends(get_db)
):
    """
    주어진 좌표의 위치 정보 및 주변 키토 식당 통계 반환
    """
    try:
        # 위치 정보를 위한 기본 쿼리
        query = text("""
            SELECT 
                COUNT(*) as total_restaurants,
                COUNT(CASE WHEN COALESCE(ks.score, 0) >= 80 THEN 1 END) as excellent_count,
                COUNT(CASE WHEN COALESCE(ks.score, 0) >= 60 AND COALESCE(ks.score, 0) < 80 THEN 1 END) as good_count,
                COUNT(CASE WHEN COALESCE(ks.score, 0) >= 40 AND COALESCE(ks.score, 0) < 60 THEN 1 END) as fair_count,
                COUNT(CASE WHEN COALESCE(ks.score, 0) >= 10 AND COALESCE(ks.score, 0) < 40 THEN 1 END) as poor_count,
                AVG(COALESCE(ks.score, 0))::DOUBLE PRECISION as avg_score
            FROM restaurant r
            LEFT JOIN menu m ON r.id = m.restaurant_id
            LEFT JOIN keto_scores ks ON m.id = ks.menu_id
            WHERE (6371 * acos(
                cos(radians(:center_lat)) * cos(radians(r.lat)) * 
                cos(radians(r.lng) - radians(:center_lng)) + 
                sin(radians(:center_lat)) * sin(radians(r.lat))
            )) <= 5.0
        """)
        
        result = await db.execute(query, {
            "center_lat": lat,
            "center_lng": lng
        })
        
        row = result.fetchone()
        
        return {
            "location": {
                "lat": lat,
                "lng": lng
            },
            "statistics": {
                "total_restaurants": row.total_restaurants if row else 0,
                "keto_score_distribution": {
                    "excellent": row.excellent_count if row else 0,
                    "good": row.good_count if row else 0,
                    "fair": row.fair_count if row else 0,
                    "poor": row.poor_count if row else 0
                },
                "average_keto_score": round(row.avg_score, 1) if row and row.avg_score else 0.0
            },
            "recommendations": {
                "search_radius_1km": f"1km 반경 내에서 {row.excellent_count if row else 0}개의 우수한 키토 식당 발견",
                "search_radius_2km": f"2km 반경으로 확대하면 더 많은 선택지가 있습니다"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"위치 정보 조회 중 오류 발생: {str(e)}"
        )