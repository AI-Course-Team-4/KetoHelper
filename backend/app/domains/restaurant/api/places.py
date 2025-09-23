"""
장소 검색 API 엔드포인트
카카오 로컬 API 통합 및 키토 스코어 계산
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
import math
import asyncio

from app.core.database import get_db, supabase
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
    min_score: int = Query(30, description="최소 키토 스코어"),
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
    min_score: int = Query(30, description="최소 키토 스코어 (기본값: 30)"),
    max_results: int = Query(10, description="최대 결과 수"),
    db: AsyncSession = Depends(get_db)
):
    """
    하이브리드 키토 식당 검색: DB 우선, 부족하면 카카오 API 보완
    1. 먼저 DB에서 키토 점수 30점 이상 식당 검색
    2. 결과가 10개 미만이면 카카오 API로 추가 검색
    """
    try:
        search_tool = PlaceSearchTool()
        score_calculator = KetoScoreCalculator()
        all_places = []
        
        print(f"🔍 하이브리드 검색 시작: {lat}, {lng}, 반경 {radius}m")
        
        # 1단계: DB에서 키토 식당 검색
        print("1단계: DB에서 키토 식당 검색 중...")
        db_places = await get_supabase_places(lat, lng, radius, min_score, max_results)
        all_places.extend(db_places)
        
        print(f"DB 검색 결과: {len(db_places)}개 식당 발견")
        
        # 2단계: DB 결과가 부족하면 카카오 API로 보완
        if len(all_places) < max_results:
            needed_count = max_results - len(all_places)
            print(f"2단계: {needed_count}개 부족, 카카오 API로 보완 검색 중...")
            
            # 카카오 API 키워드 (API 호출 제한을 위해 최소화)
            search_keywords = [
                "포케","샐러드" ,"구이", "삼겹살", "갈비", "스테이크", "회",
                "샤브샤브"
            ]
            
            kakao_places = []
            
            # 각 키워드로 검색 (API 제한 방지를 위해 지연 추가)
            for i, keyword in enumerate(search_keywords):
                if len(kakao_places) >= needed_count:
                    break
                    
                try:
                    # API 호출 사이에 3초 지연 (429 에러 방지)
                    if i > 0:
                        await asyncio.sleep(3)
                    
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
                            kakao_places.append(place_response)
                            
                            if len(kakao_places) >= needed_count:
                                break
                                
                except Exception as keyword_error:
                    print(f"키워드 '{keyword}' 검색 중 오류: {keyword_error}")
                    # 429 에러인 경우 Retry-After 시간 확인
                    if "429" in str(keyword_error) or "Too Many Requests" in str(keyword_error):
                        # 에러 메시지에서 대기 시간 추출
                        error_str = str(keyword_error)
                        if "Retry after" in error_str:
                            try:
                                # "Retry after 60 seconds" 형태에서 숫자 추출
                                import re
                                match = re.search(r'Retry after (\d+) seconds', error_str)
                                if match:
                                    wait_seconds = int(match.group(1))
                                    print(f"Retry-After 헤더 감지됨. {wait_seconds}초 대기 후 계속...")
                                    await asyncio.sleep(wait_seconds)
                                else:
                                    print("Retry-After 시간을 파싱할 수 없음. 120초 대기...")
                                    await asyncio.sleep(120)
                            except:
                                print("Retry-After 파싱 오류. 120초 대기...")
                                await asyncio.sleep(120)
                        else:
                            print("카카오 API 특성상 Retry-After 정보 없음. 120초 대기...")
                            await asyncio.sleep(120)
                    continue
            
            # 기존 DB 식당과 중복되지 않는 카카오 API 결과만 추가
            existing_ids = {place.place_id for place in all_places}
            for place in kakao_places:
                if place.place_id not in existing_ids:
                    all_places.append(place)
                    if len(all_places) >= max_results:
                        break
            
            print(f"카카오 API 보완 결과: {len(kakao_places)}개 중 {len(all_places) - len(db_places)}개 추가")
        
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
        
        # 검색 방법 표시
        search_method = "database_only" if len(db_places) >= max_results else "hybrid"
        
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
            },
            "search_method": search_method,
            "db_count": len(db_places),
            "kakao_count": len(all_places) - len(db_places)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"하이브리드 키토 식당 검색 중 오류 발생: {str(e)}"
        )

# Supabase 클라이언트를 사용한 식당 검색 함수
async def get_supabase_places(
    lat: float, 
    lng: float, 
    radius: int, 
    min_score: int, 
    max_results: int
) -> List[PlaceResponse]:
    """Supabase 클라이언트를 사용한 식당 검색"""
    try:
        radius_km = radius / 1000.0
        print(f"🔍 Supabase 검색 시작: 중심({lat}, {lng}), 반경 {radius_km}km, 최소점수 {min_score}")
        
        if supabase is None or hasattr(supabase, '__class__') and 'DummySupabase' in str(supabase.__class__):
            print("⚠️ Supabase 클라이언트 없음 - 빈 결과 반환")
            return []
        
        # 대표 메뉴 키토 점수 기반 검색
        try:
            # 대표 메뉴 키토 점수가 있는 식당만 조회
            restaurant_response = supabase.table('restaurant').select(
                'id,name,category,lat,lng,addr_road,addr_jibun,representative_menu_name,representative_keto_score'
            ).not_.is_('representative_keto_score', 'null').execute()
            
            rows = restaurant_response.data if hasattr(restaurant_response, 'data') else []
            print(f"📋 대표 메뉴가 있는 식당: {len(rows)}개 발견")
            
        except Exception as e:
            print(f"❌ Supabase 검색 실패: {e}")
            return []
        
        # 대표 메뉴 키토 점수로 식당 필터링
        places = []
        
        for row in rows:
            try:
                # 거리 계산
                if not row.get('lat') or not row.get('lng'):
                    continue
                    
                distance_km = 6371 * math.acos(
                    math.cos(math.radians(lat)) * math.cos(math.radians(row['lat'])) * 
                    math.cos(math.radians(row['lng']) - math.radians(lng)) + 
                    math.sin(math.radians(lat)) * math.sin(math.radians(row['lat']))
                )
                
                # 반경 내 식당만 처리
                if distance_km > radius_km:
                    continue
                
                # 대표 메뉴 키토 점수 사용
                keto_score = row.get('representative_keto_score', 0)
                representative_menu = row.get('representative_menu_name', '')
                
                # 최소 점수 이상인 식당만 추가
                if keto_score >= min_score:
                    # 이유와 팁 생성
                    reasons = [f"대표 메뉴: {representative_menu} ({keto_score}점)"]
                    tips = ["대표 메뉴 선택 시 키토 친화적", "추가 메뉴 확인 권장"]
                    
                    place_response = PlaceResponse(
                        place_id=str(row.get('id') or ''),
                        name=row.get('name') or '',
                        address=(row.get('addr_road') or row.get('addr_jibun')) or '',
                        category=row.get('category') or '',
                        lat=float(row.get('lat') or 0.0),
                        lng=float(row.get('lng') or 0.0),
                        keto_score=keto_score,
                        why=reasons,
                        tips=tips
                    )
                    places.append(place_response)
                    print(f"✅ 식당 추가: {row.get('name')} (대표메뉴: {representative_menu}, {keto_score}점) - 좌표: ({row.get('lat')}, {row.get('lng')})")
                else:
                    print(f"❌ 식당 제외: {row.get('name')} (대표메뉴: {representative_menu}, {keto_score}점 < {min_score})")
                    
            except Exception as e:
                continue
        
        print(f"🎯 최종 Supabase 결과: {len(places)}개 식당 (키토 점수 {min_score}점 이상)")
        return places[:max_results]  # 최대 결과 수로 제한
        
    except Exception as e:
        print(f"❌ Supabase 검색 오류: {e}")
        return []

# DB에서 식당 검색하는 헬퍼 함수 (기존 함수 유지)
async def get_database_places(
    db: AsyncSession, 
    lat: float, 
    lng: float, 
    radius: int, 
    min_score: int, 
    max_results: int
) -> List[PlaceResponse]:
    """DB에서 키토 점수 기반 식당 검색"""
    try:
        # 반경을 킬로미터로 변환
        radius_km = radius / 1000.0
        print(f"🔍 DB 검색 시작: 중심({lat}, {lng}), 반경 {radius_km}km, 최소점수 {min_score}")
        
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
            -- HAVING 조건 제거: 모든 식당 검색
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
        print(f"📋 DB 검색 결과: {len(rows)}개 식당 발견")
        
        # 결과를 PlaceResponse 형식으로 변환하고 키토 점수 필터링
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
            
            # 키토 점수 필터링 (애플리케이션 레벨)
            if keto_score >= min_score:
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
                print(f"✅ 식당 추가: {row.name} (키토점수: {keto_score})")
            else:
                print(f"❌ 식당 제외: {row.name} (키토점수: {keto_score} < {min_score})")
        
        print(f"🎯 최종 DB 결과: {len(places)}개 식당 (키토 점수 {min_score}점 이상)")
        return places
        
    except Exception as e:
        print(f"DB 검색 오류: {e}")
        return []  # DB 오류 시 빈 리스트 반환

@router.get("/database-search")
async def get_keto_places_from_database(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    radius: int = Query(2000, description="검색 반경(m)"),
    min_score: int = Query(30, description="최소 키토 스코어"),
    max_results: int = Query(10, description="최대 결과 수"),
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
            -- HAVING 조건 제거: 모든 식당 검색
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
        print(f"📋 DB 검색 결과: {len(rows)}개 식당 발견")
        
        # 결과를 PlaceResponse 형식으로 변환하고 키토 점수 필터링
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
