"""
장소 검색 API 엔드포인트
카카오 로컬 API 통합 및 키토 스코어 계산
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
import math

from app.core.database import get_db, supabase
from app.shared.models.schemas import PlaceSearchRequest, PlaceResponse
from app.tools.meal.keto_score import KetoScoreCalculator
from app.tools.restaurant.restaurant_hybrid_search import restaurant_hybrid_search_tool

router = APIRouter(prefix="/places", tags=["places"])

@router.get("/", response_model=List[PlaceResponse])
async def search_places(
    q: str = Query(..., description="검색 키워드"),
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    radius: int = Query(1000, description="검색 반경(m)"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    user_id: Optional[str] = Query(None, description="사용자 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    하이브리드 키토 친화적인 장소 검색
    
    벡터 검색 + 키워드 검색 + DB 검색을 통합하여
    키토 스코어를 기준으로 정렬된 결과를 반환합니다.
    
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
        print(f"SEARCH: 하이브리드 키워드 검색: '{q}', 위치: ({lat}, {lng}), 반경: {radius}m")
        
        all_places = []
        
        # 1단계: 하이브리드 검색으로 벡터 + 키워드 검색
        print("1단계: 하이브리드 검색 실행...")
        hybrid_results = await restaurant_hybrid_search_tool.hybrid_search(
            query=q,
            location={"lat": lat, "lng": lng},
            max_results=15,
            user_id=user_id
        )
        
        # 하이브리드 검색 결과를 PlaceResponse 형식으로 변환
        for result in hybrid_results:
            # 위치 기반 거리 계산
            if result.get('lat') and result.get('lng'):
                distance_km = 6371 * math.acos(
                    math.cos(math.radians(lat)) * math.cos(math.radians(result['lat'])) * 
                    math.cos(math.radians(result['lng']) - math.radians(lng)) + 
                    math.sin(math.radians(lat)) * math.sin(math.radians(result['lat']))
                )
                
                # 반경 내 식당만 추가
                if distance_km <= (radius / 1000.0):
                    # 카테고리 필터 적용
                    if category and category.strip() and result.get('category') != category:
                        continue
                    
                    # keto_reasons 처리 (딕셔너리일 수 있음)
                    keto_reasons = result.get('keto_reasons', [])
                    if isinstance(keto_reasons, dict):
                        # 딕셔너리인 경우 리스트로 변환
                        tips = ["메뉴 선택 시 주의하세요"]
                    elif isinstance(keto_reasons, list):
                        tips = keto_reasons if keto_reasons else ["메뉴 선택 시 주의하세요"]
                    else:
                        tips = ["메뉴 선택 시 주의하세요"]
                    
                    place_response = PlaceResponse(
                        place_id=str(result.get('restaurant_id', '')),
                        name=result.get('restaurant_name', ''),
                        address=result.get('addr_road', result.get('addr_jibun', '')),
                        category=result.get('category', ''),
                        lat=float(result.get('lat', 0.0)),
                        lng=float(result.get('lng', 0.0)),
                        keto_score=result.get('keto_score', 0),
                        why=[f"하이브리드 검색: {q}"] if result.get('menu_name') else ["키워드 매칭"],
                        tips=tips,
                        source_url=result.get('source_url')
                    )
                    all_places.append(place_response)
                    print(f"  SUCCESS: 식당 추가: {result.get('restaurant_name')} (키토점수: {result.get('keto_score')}, 거리: {distance_km:.2f}km)")
        
        print(f"하이브리드 검색 결과: {len(all_places)}개 식당 발견")
        
        # 2단계: DB에서 키워드 기반 식당 추가 검색 (선택적)
        print("2단계: DB 키워드 기반 검색...")
        try:
            db_places = await get_supabase_places_by_keyword(
                query=q,
                lat=lat,
                lng=lng,
                radius=radius,
                category=category,
                min_score=10,  # 검색에서는 더 관대하게
                max_results=10
            )
            all_places.extend(db_places)
            print(f"DB 검색 결과: {len(db_places)}개 식당 추가")
        except Exception as e:
            print(f"WARNING: DB 검색 건너뜀 - {e}")
            print("INFO: 하이브리드 검색 결과만 사용")
        
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
        
        print(f"최종 검색 결과: {len(result_places)}개 식당")
        return result_places
        
    except Exception as e:
        print(f"ERROR: 하이브리드 장소 검색 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"하이브리드 장소 검색 중 오류 발생: {str(e)}"
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
    user_id: Optional[str] = Query(None, description="사용자 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    주변 키토 친화적인 장소들을 하이브리드 검색으로 찾기
    벡터 검색 + 키워드 검색 + DB 검색을 통합하여 키토 스코어가 높은 장소들만 필터링
    """
    try:
        print(f"SEARCH: 주변 하이브리드 검색: ({lat}, {lng}), 반경: {radius}m")
        
        all_places = []
        
        # 1단계: 키토 친화 키워드로 하이브리드 검색
        keto_keywords = ["구이", "샤브샤브", "샐러드", "스테이크", "회", "삼겹살", "갈비", "포케", "치킨", "전골"]
        print(f"1단계: {len(keto_keywords)}개 키토 키워드로 하이브리드 검색...")
        
        for keyword in keto_keywords[:5]:  # 상위 5개 키워드 사용
            try:
                hybrid_results = await restaurant_hybrid_search_tool.hybrid_search(
                    query=keyword,
                    location={"lat": lat, "lng": lng},
                    max_results=8,
                    user_id=user_id
                )
                
                # 결과를 PlaceResponse 형식으로 변환
                for result in hybrid_results:
                    # 위치 기반 거리 계산
                    if result.get('lat') and result.get('lng'):
                        distance_km = 6371 * math.acos(
                            math.cos(math.radians(lat)) * math.cos(math.radians(result['lat'])) * 
                            math.cos(math.radians(result['lng']) - math.radians(lng)) + 
                            math.sin(math.radians(lat)) * math.sin(math.radians(result['lat']))
                        )
                        
                        # 반경 내 식당만 추가
                        if distance_km <= (radius / 1000.0):
                            # keto_reasons 처리 (딕셔너리일 수 있음)
                            keto_reasons = result.get('keto_reasons', [])
                            if isinstance(keto_reasons, dict):
                                tips = ["메뉴 선택 시 주의하세요"]
                            elif isinstance(keto_reasons, list):
                                tips = keto_reasons if keto_reasons else ["메뉴 선택 시 주의하세요"]
                            else:
                                tips = ["메뉴 선택 시 주의하세요"]
                            
                            place_response = PlaceResponse(
                                place_id=str(result.get('restaurant_id', '')),
                                name=result.get('restaurant_name', ''),
                                address=result.get('addr_road', result.get('addr_jibun', '')),
                                category=result.get('category', ''),
                                lat=float(result.get('lat', 0.0)),
                                lng=float(result.get('lng', 0.0)),
                                keto_score=result.get('keto_score', 0),
                                why=[f"하이브리드 검색: {keyword}"] if result.get('menu_name') else ["키토 친화 식당"],
                                tips=tips,
                                source_url=result.get('source_url')
                            )
                            all_places.append(place_response)
                
            except Exception as e:
                print(f"키워드 '{keyword}' 검색 오류: {e}")
                continue
        
        print(f"하이브리드 검색 결과: {len(all_places)}개 식당 발견")
        
        # 2단계: DB에서 키토 식당 추가 검색
        print("2단계: DB 키토 식당 검색...")
        db_places = await get_supabase_places(lat, lng, radius, min_score, 20)
        all_places.extend(db_places)
        print(f"DB 검색 결과: {len(db_places)}개 식당 추가")
        
        # 중복 제거 (place_id 기준) 및 최고 점수 유지
        unique_places = {}
        for place in all_places:
            if place.place_id not in unique_places:
                unique_places[place.place_id] = place
            elif place.keto_score > unique_places[place.place_id].keto_score:
                unique_places[place.place_id] = place
        
        # 키토 스코어 순으로 정렬
        result_places = list(unique_places.values())
        result_places.sort(key=lambda x: x.keto_score, reverse=True)
        
        # 최소 스코어 필터링
        filtered_places = [p for p in result_places if p.keto_score >= min_score]
        
        return {
            "places": filtered_places[:20],  # 상위 20개만 반환
            "total_found": len(filtered_places),
            "search_radius": radius,
            "min_score": min_score,
            "search_method": "hybrid"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"주변 하이브리드 키토 장소 검색 중 오류 발생: {str(e)}"
        )

@router.get("/high-keto-score")
async def get_high_keto_score_places(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    radius: int = Query(2000, description="검색 반경(m)"),
    min_score: int = Query(30, description="최소 키토 스코어 (기본값: 30)"),
    max_results: int = Query(10, description="최대 결과 수"),
    user_id: Optional[str] = Query(None, description="사용자 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    하이브리드 키토 식당 검색
    벡터 검색 + 키워드 검색 + DB 검색을 통합한 키토 친화 식당 검색
    """
    try:
        print(f"SEARCH: 하이브리드 키토 식당 검색 시작: {lat}, {lng}, 반경 {radius}m")
        
        all_places = []
        
        # 1단계: 키토 친화 키워드로 하이브리드 검색
        keto_keywords = ["구이", "샤브샤브", "샐러드", "스테이크", "회", "삼겹살", "갈비", "포케"]
        print(f"1단계: 하이브리드 검색으로 {len(keto_keywords)}개 키워드 검색 중...")
        
        for keyword in keto_keywords[:4]:  # 상위 4개 키워드만 사용 (API 제한 고려)
            try:
                print(f"  SEARCH: 키워드 '{keyword}' 하이브리드 검색...")
                hybrid_results = await restaurant_hybrid_search_tool.hybrid_search(
                    query=keyword,
                    location={"lat": lat, "lng": lng},
                    max_results=5,
                    user_id=user_id
                )
                
                # 결과를 PlaceResponse 형식으로 변환
                for result in hybrid_results:
                    # 위치 기반 거리 계산
                    if result.get('lat') and result.get('lng'):
                        distance_km = 6371 * math.acos(
                            math.cos(math.radians(lat)) * math.cos(math.radians(result['lat'])) * 
                            math.cos(math.radians(result['lng']) - math.radians(lng)) + 
                            math.sin(math.radians(lat)) * math.sin(math.radians(result['lat']))
                        )
                        
                        # 반경 내 식당만 추가
                        if distance_km <= (radius / 1000.0):
                            # keto_reasons 처리 (딕셔너리일 수 있음)
                            keto_reasons = result.get('keto_reasons', [])
                            if isinstance(keto_reasons, dict):
                                tips = ["메뉴 선택 시 주의하세요"]
                            elif isinstance(keto_reasons, list):
                                tips = keto_reasons if keto_reasons else ["메뉴 선택 시 주의하세요"]
                            else:
                                tips = ["메뉴 선택 시 주의하세요"]
                            
                            place_response = PlaceResponse(
                                place_id=str(result.get('restaurant_id', '')),
                                name=result.get('restaurant_name', ''),
                                address=result.get('addr_road', result.get('addr_jibun', '')),
                                category=result.get('category', ''),
                                lat=float(result.get('lat', 0.0)),
                                lng=float(result.get('lng', 0.0)),
                                keto_score=result.get('keto_score', 0),
                                why=[f"하이브리드 검색: {keyword}"] if result.get('menu_name') else ["키토 친화 식당"],
                                tips=tips,
                                source_url=result.get('source_url')
                            )
                            all_places.append(place_response)
                            print(f"    SUCCESS: 식당 추가: {result.get('restaurant_name')} (키토점수: {result.get('keto_score')}, 거리: {distance_km:.2f}km)")
                
            except Exception as e:
                print(f"    ERROR: 키워드 '{keyword}' 검색 오류: {e}")
                continue
        
        print(f"하이브리드 검색 결과: {len(all_places)}개 식당 발견")
        
        # 2단계: DB에서 대표 메뉴 키토 점수가 있는 식당들 추가 검색
        print("2단계: DB 대표 메뉴 키토 점수 기반 검색...")
        db_places = await get_supabase_places(lat, lng, radius, min_score, max_results)
        all_places.extend(db_places)
        print(f"DB 검색 결과: {len(db_places)}개 식당 추가")
        
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
        hybrid_count = len(all_places) - len(db_places)
        search_method = "hybrid" if hybrid_count > 0 else "database_only"
        
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
            "hybrid_count": hybrid_count,
            "kakao_count": 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"하이브리드 키토 식당 검색 중 오류 발생: {str(e)}"
        )

# 키워드 기반 Supabase 식당 검색 함수
async def get_supabase_places_by_keyword(
    query: str,
    lat: float, 
    lng: float, 
    radius: int, 
    category: Optional[str],
    min_score: int, 
    max_results: int
) -> List[PlaceResponse]:
    """키워드 기반 Supabase 식당 검색"""
    try:
        radius_km = radius / 1000.0
        print(f"SEARCH: 키워드 검색: '{query}', 중심({lat}, {lng}), 반경 {radius_km}km")
        
        if supabase is None or hasattr(supabase, '__class__') and 'DummySupabase' in str(supabase.__class__):
            print("WARNING: Supabase 클라이언트 없음 - 빈 결과 반환")
            return []
        
        try:
            # 키워드가 포함된 식당 검색
            restaurant_query = supabase.table('restaurant').select(
                'id,name,category,lat,lng,addr_road,addr_jibun,representative_menu_name,representative_keto_score,source_url'
            ).not_.is_('representative_keto_score', 'null')
        
            # 키워드로 이름이나 대표 메뉴 검색
            if query.strip():
                # ILIKE를 사용한 부분 문자열 검색 (PostgreSQL)
                restaurant_query = restaurant_query.or_(f"name.ilike.%{query}%,representative_menu_name.ilike.%{query}%")
            
            # 카테고리 필터
            if category and category.strip():
                restaurant_query = restaurant_query.eq('category', category)
            
            restaurant_response = restaurant_query.execute()
            rows = restaurant_response.data if hasattr(restaurant_response, 'data') else []
            print(f"RESULT: 키워드 매칭 식당: {len(rows)}개 발견")
            
        except Exception as e:
            print(f"ERROR: Supabase 키워드 검색 실패: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        # 거리 계산 및 필터링
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
                        tips=tips,
                        source_url=row.get('source_url')
                    )
                    places.append(place_response)
                    print(f"SUCCESS: 식당 추가: {row.get('name')} (대표메뉴: {representative_menu}, {keto_score}점)")
                    
            except Exception as e:
                continue
        
        print(f"RESULT: 최종 키워드 검색 결과: {len(places)}개 식당")
        return places[:max_results]
        
    except Exception as e:
        print(f"ERROR: 키워드 검색 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

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
        print(f"SEARCH: Supabase 검색 시작: 중심({lat}, {lng}), 반경 {radius_km}km, 최소점수 {min_score}")
        
        if supabase is None or hasattr(supabase, '__class__') and 'DummySupabase' in str(supabase.__class__):
            print("WARNING: Supabase 클라이언트 없음 - 빈 결과 반환")
            return []
        
        # 대표 메뉴 키토 점수 기반 검색
        try:
            # 대표 메뉴 키토 점수가 있는 식당만 조회
            restaurant_response = supabase.table('restaurant').select(
                'id,name,category,lat,lng,addr_road,addr_jibun,representative_menu_name,representative_keto_score,source_url'
            ).not_.is_('representative_keto_score', 'null').execute()
            
            rows = restaurant_response.data if hasattr(restaurant_response, 'data') else []
            print(f"RESULT: 대표 메뉴가 있는 식당: {len(rows)}개 발견")
            
        except Exception as e:
            print(f"ERROR: Supabase 검색 실패: {e}")
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
                        tips=tips,
                        source_url=row.get('source_url')
                    )
                    places.append(place_response)
                    print(f"SUCCESS: 식당 추가: {row.get('name')} (대표메뉴: {representative_menu}, {keto_score}점) - 좌표: ({row.get('lat')}, {row.get('lng')})")
                else:
                    print(f"SKIP: 식당 제외: {row.get('name')} (대표메뉴: {representative_menu}, {keto_score}점 < {min_score})")
                    
            except Exception as e:
                continue
        
        print(f"RESULT: 최종 Supabase 결과: {len(places)}개 식당 (키토 점수 {min_score}점 이상)")
        return places[:max_results]  # 최대 결과 수로 제한
        
    except Exception as e:
        print(f"ERROR: Supabase 검색 오류: {e}")
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
        print(f"SEARCH: DB 검색 시작: 중심({lat}, {lng}), 반경 {radius_km}km, 최소점수 {min_score}")
        
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
        print(f"RESULT: DB 검색 결과: {len(rows)}개 식당 발견")
        
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
                print(f"SUCCESS: 식당 추가: {row.name} (키토점수: {keto_score})")
            else:
                print(f"SKIP: 식당 제외: {row.name} (키토점수: {keto_score} < {min_score})")
        
        print(f"RESULT: 최종 DB 결과: {len(places)}개 식당 (키토 점수 {min_score}점 이상)")
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
        print(f"RESULT: DB 검색 결과: {len(rows)}개 식당 발견")
        
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
