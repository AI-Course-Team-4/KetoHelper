"""
장소 검색 도구
카카오 로컬 API를 통한 키토 친화적 식당 검색
"""

import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.database_models import PlaceCache

class PlaceSearchTool:
    """카카오 로컬 API 장소 검색 도구"""
    
    def __init__(self):
        self.api_key = settings.kakao_rest_key
        self.base_url = "https://dapi.kakao.com/v2/local"
        self.cache_hours = 24  # 캐시 유지 시간
    
    async def search(
        self,
        query: str,
        lat: float,
        lng: float,
        radius: int = 1000,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        카카오 로컬 API를 통한 장소 검색
        
        Args:
            query: 검색 키워드
            lat: 위도
            lng: 경도
            radius: 검색 반경(미터)
            category: 카테고리 필터
        
        Returns:
            장소 정보 리스트
        """
        try:
            # 캐시 확인
            cached_results = await self._get_cached_results(query, lat, lng, radius)
            if cached_results:
                return cached_results
            
            # API 호출
            headers = {
                "Authorization": f"KakaoAK {self.api_key}"
            }
            
            params = {
                "query": query,
                "x": lng,
                "y": lat,
                "radius": radius,
                "size": 15,
                "sort": "distance"
            }
            
            if category:
                params["category_group_code"] = self._get_category_code(category)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/search/keyword.json",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                places = self._parse_kakao_response(data)
                
                # 결과 캐싱
                await self._cache_results(places, query, lat, lng, radius)
                
                return places
        
        except httpx.HTTPError as e:
            print(f"카카오 API 에러: {e}")
            return []
        except Exception as e:
            print(f"장소 검색 에러: {e}")
            return []
    
    def _parse_kakao_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """카카오 API 응답 파싱"""
        
        places = []
        documents = data.get("documents", [])
        
        for doc in documents:
            place = {
                "id": doc.get("id", ""),
                "name": doc.get("place_name", ""),
                "category": doc.get("category_name", ""),
                "address": doc.get("road_address_name") or doc.get("address_name", ""),
                "lat": float(doc.get("y", 0)),
                "lng": float(doc.get("x", 0)),
                "phone": doc.get("phone", ""),
                "place_url": doc.get("place_url", ""),
                "distance": int(doc.get("distance", 0))
            }
            places.append(place)
        
        return places
    
    def _get_category_code(self, category: str) -> str:
        """카테고리명을 카카오 카테고리 코드로 변환"""
        
        category_map = {
            "meat": "FD6",     # 고기요리
            "salad": "FD6",    # 음식점 (일반)
            "seafood": "FD6",  # 음식점 (일반)
            "chicken": "FD6",  # 음식점 (일반)
            "western": "FD6",  # 음식점 (일반)
            "cafe": "CE7"      # 카페
        }
        
        return category_map.get(category, "FD6")
    
    async def _get_cached_results(
        self,
        query: str,
        lat: float,
        lng: float,
        radius: int
    ) -> Optional[List[Dict[str, Any]]]:
        """캐시된 검색 결과 조회"""
        
        try:
            # 캐시 키 생성 (간단화된 형태)
            cache_key = f"{query}_{lat:.3f}_{lng:.3f}_{radius}"
            cutoff_time = datetime.now() - timedelta(hours=self.cache_hours)
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(PlaceCache)
                    .where(
                        PlaceCache.place_id.like(f"{cache_key}%")
                    )
                    .where(PlaceCache.last_seen_at > cutoff_time)
                )
                
                cached_places = result.scalars().all()
                
                if cached_places:
                    return [
                        {
                            "id": place.place_id.split("_")[-1],  # 원본 ID 추출
                            "name": place.name,
                            "category": place.category,
                            "address": place.address,
                            "lat": place.lat,
                            "lng": place.lng,
                            "keto_score": place.keto_score
                        }
                        for place in cached_places
                    ]
                
        except Exception as e:
            print(f"캐시 조회 에러: {e}")
        
        return None
    
    async def _cache_results(
        self,
        places: List[Dict[str, Any]],
        query: str,
        lat: float,
        lng: float,
        radius: int
    ) -> None:
        """검색 결과 캐싱"""
        
        try:
            cache_key_prefix = f"{query}_{lat:.3f}_{lng:.3f}_{radius}"
            
            async with AsyncSessionLocal() as db:
                # 기존 캐시 삭제
                await db.execute(
                    select(PlaceCache)
                    .where(PlaceCache.place_id.like(f"{cache_key_prefix}%"))
                    .delete()
                )
                
                # 새 캐시 저장
                cache_objects = []
                for place in places:
                    cache_place = PlaceCache(
                        place_id=f"{cache_key_prefix}_{place['id']}",
                        name=place["name"],
                        address=place["address"],
                        category=place["category"],
                        lat=place["lat"],
                        lng=place["lng"],
                        keto_score=place.get("keto_score", 0),
                        last_seen_at=datetime.now()
                    )
                    cache_objects.append(cache_place)
                
                db.add_all(cache_objects)
                await db.commit()
                
        except Exception as e:
            print(f"캐시 저장 에러: {e}")
    
    async def search_by_category(
        self,
        category: str,
        lat: float,
        lng: float,
        radius: int = 1000
    ) -> List[Dict[str, Any]]:
        """카테고리별 키토 친화적 장소 검색"""
        
        # 카테고리별 검색 키워드 매핑
        category_keywords = {
            "meat": ["구이", "삼겹살", "갈비", "스테이크"],
            "shabu": ["샤브샤브", "전골", "무한리필"],
            "salad": ["샐러드", "샐러드바", "헬시"],
            "seafood": ["회", "횟집", "생선구이", "조개구이"],
            "chicken": ["치킨", "닭갈비", "닭요리"],
            "western": ["스테이크", "파스타", "양식", "이탈리안"]
        }
        
        keywords = category_keywords.get(category, [category])
        all_places = []
        
        # 각 키워드로 검색
        for keyword in keywords:
            places = await self.search(keyword, lat, lng, radius)
            all_places.extend(places)
        
        # 중복 제거
        unique_places = {}
        for place in all_places:
            place_id = place.get("id")
            if place_id not in unique_places:
                unique_places[place_id] = place
        
        return list(unique_places.values())
    
    async def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """특정 장소의 상세 정보 조회"""
        
        try:
            headers = {
                "Authorization": f"KakaoAK {self.api_key}"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/search/keyword.json",
                    headers=headers,
                    params={"query": place_id, "size": 1}
                )
                response.raise_for_status()
                
                data = response.json()
                documents = data.get("documents", [])
                
                if documents:
                    return self._parse_kakao_response(data)[0]
                
        except Exception as e:
            print(f"장소 상세 정보 조회 에러: {e}")
        
        return None
    
    async def search_nearby_keto_friendly(
        self,
        lat: float,
        lng: float,
        radius: int = 1000
    ) -> List[Dict[str, Any]]:
        """주변 키토 친화적 장소 자동 검색"""
        
        keto_keywords = [
            "구이", "샤브샤브", "샐러드", "스테이크", "회",
            "치킨", "갈비", "삼겹살", "양식", "무한리필"
        ]
        
        all_places = []
        
        # 각 키워드로 병렬 검색
        tasks = []
        for keyword in keto_keywords:
            task = self.search(keyword, lat, lng, radius)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 병합 및 중복 제거
        unique_places = {}
        for result in results:
            if isinstance(result, list):
                for place in result:
                    place_id = place.get("id")
                    if place_id and place_id not in unique_places:
                        unique_places[place_id] = place
        
        return list(unique_places.values())
