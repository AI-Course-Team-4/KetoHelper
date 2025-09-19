"""
지오코딩 서비스
"""

import asyncio
import httpx
from typing import Dict, Any, Optional
import logging

from config.settings import settings
from services.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class GeocodingService:
    """지오코딩 서비스 (카카오 API 사용)"""

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.api_key = settings.external_apis.kakao_rest_api_key
        self.cache_manager = cache_manager
        self.base_url = "https://dapi.kakao.com/v2/local/search/address.json"

        if not self.api_key:
            logger.warning("Kakao API key not configured - geocoding will be disabled")

    async def geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """주소를 좌표로 변환"""
        if not self.api_key:
            return None

        if not address or not address.strip():
            return None

        address = address.strip()

        # 캐시 확인
        if self.cache_manager:
            cached_result = await self.cache_manager.get_geocoding_result(address)
            if cached_result:
                logger.debug(f"Using cached geocoding result for: {address}")
                return cached_result

        try:
            result = await self._call_kakao_api(address)

            # 캐시 저장
            if result and self.cache_manager:
                await self.cache_manager.store_geocoding_result(address, result)

            return result

        except Exception as e:
            logger.error(f"Geocoding failed for address '{address}': {e}")
            return None

    async def _call_kakao_api(self, address: str) -> Optional[Dict[str, Any]]:
        """카카오 지오코딩 API 호출"""
        headers = {
            'Authorization': f'KakaoAK {self.api_key}',
            'Content-Type': 'application/json'
        }

        params = {
            'query': address,
            'analyze_type': 'similar'  # 유사한 주소도 검색
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.base_url,
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_kakao_response(data, address)
            elif response.status_code == 401:
                logger.error("Kakao API authentication failed - check API key")
            elif response.status_code == 429:
                logger.warning("Kakao API rate limit exceeded")
            else:
                logger.error(f"Kakao API error: {response.status_code}")

            return None

    def _parse_kakao_response(self, data: Dict[str, Any], original_address: str) -> Optional[Dict[str, Any]]:
        """카카오 API 응답 파싱"""
        documents = data.get('documents', [])

        if not documents:
            logger.debug(f"No geocoding results found for: {original_address}")
            return None

        # 첫 번째 결과 사용
        doc = documents[0]

        try:
            result = {
                'original_address': original_address,
                'formatted_address': doc.get('address_name', ''),
                'lat': float(doc.get('y', 0)),
                'lng': float(doc.get('x', 0)),
                'address_type': doc.get('address_type', ''),
                'provider': 'kakao'
            }

            # 도로명주소 정보 추가 (있는 경우)
            if 'road_address' in doc and doc['road_address']:
                road_addr = doc['road_address']
                result['road_address'] = road_addr.get('address_name', '')
                result['building_name'] = road_addr.get('building_name', '')

            # 지번주소 정보 추가 (있는 경우)
            if 'address' in doc and doc['address']:
                jibun_addr = doc['address']
                result['jibun_address'] = jibun_addr.get('address_name', '')

            return result

        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing geocoding response: {e}")
            return None

class MockGeocodingService(GeocodingService):
    """테스트용 Mock 지오코딩 서비스"""

    def __init__(self):
        super().__init__()
        self.api_key = "mock_api_key"

    async def _call_kakao_api(self, address: str) -> Optional[Dict[str, Any]]:
        """Mock API 호출"""
        # 서울 강남구 좌표 반환
        await asyncio.sleep(0.1)  # API 호출 시뮬레이션

        return {
            'original_address': address,
            'formatted_address': f"서울 강남구 {address}",
            'lat': 37.4979 + (hash(address) % 100) * 0.0001,
            'lng': 127.0276 + (hash(address) % 100) * 0.0001,
            'address_type': 'ROAD_ADDR',
            'provider': 'mock'
        }