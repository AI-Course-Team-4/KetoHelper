"""
🔌 기본 파서 인터페이스
- 추상 클래스로 파서 표준 정의
- 플러그인 아키텍처 지원
- 에러 처리 및 재시도 로직
"""

import re
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from ..models import Restaurant, Menu, RestaurantCreate, MenuCreate
from ..utils.config_loader import get_config
from ..utils.logger import get_logger, log_parser_error
from ..utils.text_utils import (
    normalize_text, normalize_restaurant_name, normalize_address,
    extract_phone_number, extract_price, extract_coordinates, extract_rating
)
from ..utils.http_client import HttpClient


@dataclass
class ParseResult:
    """파싱 결과"""
    success: bool
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    error: Optional[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResult:
    """검색 결과"""
    restaurants: List[RestaurantCreate]
    total_found: int
    page: int
    has_next_page: bool
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseParser(ABC):
    """기본 파서 추상 클래스"""
    
    def __init__(self, site: str, http_client: Optional[HttpClient] = None):
        self.site = site
        self.config = get_config()
        self.logger = get_logger(f"parser_{site}")
        
        # HTTP 클라이언트
        self.http_client = http_client
        
        # 파서 설정 로드
        try:
            self.parser_config = self.config.get_parser_config(site)
            self.site_config = self.parser_config.get('site', {})
            self.search_config = self.parser_config.get('search', {})
            self.detail_config = self.parser_config.get('restaurant_detail', {})
            self.extraction_config = self.parser_config.get('extraction', {})
            self.validation_config = self.parser_config.get('validation', {})
            
        except Exception as e:
            self.logger.error(f"파서 설정 로드 실패: {e}")
            raise
        
        # 통계
        self.stats = {
            "requests_made": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "restaurants_parsed": 0,
            "menus_parsed": 0,
            "parsing_errors": 0
        }
    
    @abstractmethod
    async def search(self, keyword: str, page: int = 1) -> SearchResult:
        """식당 검색"""
        pass
    
    @abstractmethod
    async def parse_restaurant_detail(self, url: str) -> ParseResult:
        """식당 상세 정보 파싱"""
        pass
    
    @abstractmethod
    def extract_restaurant_data(self, content: str, url: str) -> Dict[str, Any]:
        """HTML에서 식당 데이터 추출"""
        pass
    
    @abstractmethod
    def extract_menu_data(self, content: str, url: str) -> List[Dict[str, Any]]:
        """HTML에서 메뉴 데이터 추출"""
        pass
    
    # 공통 유틸리티 메서드들
    
    def extract_text_by_selector(self, content: str, selectors: Union[str, List[str]], 
                                default: str = "") -> str:
        """CSS 셀렉터로 텍스트 추출"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 여러 셀렉터 시도
        if isinstance(selectors, str):
            selectors = [selectors]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    text = elements[0].get_text(strip=True)
                    if text:
                        return normalize_text(text)
            except Exception as e:
                self.logger.debug(f"셀렉터 실패: {selector} - {e}")
                continue
        
        return default
    
    def extract_attribute_by_selector(self, content: str, selector: str, 
                                     attribute: str, default: str = "") -> str:
        """CSS 셀렉터로 속성값 추출"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(content, 'html.parser')
        
        try:
            elements = soup.select(selector)
            if elements:
                attr_value = elements[0].get(attribute, "")
                if attr_value:
                    return normalize_text(str(attr_value))
        except Exception as e:
            self.logger.debug(f"속성 추출 실패: {selector}[{attribute}] - {e}")
        
        return default
    
    def extract_multiple_by_selector(self, content: str, container_selector: str, 
                                   item_selector: str) -> List[str]:
        """여러 요소 추출 (목록)"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(content, 'html.parser')
        results = []
        
        try:
            containers = soup.select(container_selector)
            for container in containers:
                items = container.select(item_selector)
                for item in items:
                    text = item.get_text(strip=True)
                    if text:
                        results.append(normalize_text(text))
        except Exception as e:
            self.logger.debug(f"다중 추출 실패: {container_selector} > {item_selector} - {e}")
        
        return results
    
    def extract_coordinates_from_content(self, content: str) -> tuple[Optional[float], Optional[float]]:
        """콘텐츠에서 좌표 추출"""
        # 설정에서 좌표 패턴 가져오기
        patterns = self.extraction_config.get('coordinate_patterns', [])
        
        lat, lng = extract_coordinates(content)
        
        # 추가 패턴 시도
        for pattern in patterns:
            if lat and lng:
                break
                
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match)
                    if 'lat' in pattern.lower():
                        lat = value
                    elif 'lng' in pattern.lower() or 'lon' in pattern.lower():
                        lng = value
                except ValueError:
                    continue
        
        return lat, lng
    
    def normalize_restaurant_data(self, raw_data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """식당 데이터 정규화"""
        normalized = {
            'source': self.site,
            'source_url': url,
        }
        
        # 필수 필드 처리
        if 'name' in raw_data:
            normalized['name'] = normalize_restaurant_name(raw_data['name'])
        
        # 주소 정규화
        if 'address_road' in raw_data:
            normalized['address_road'] = normalize_address(raw_data['address_road'])
        
        if 'address_jibun' in raw_data:
            normalized['address_jibun'] = normalize_address(raw_data['address_jibun'])
        
        # 전화번호 정규화
        if 'phone' in raw_data:
            phone = extract_phone_number(raw_data['phone'])
            if phone:
                normalized['phone'] = phone
        
        # 좌표 처리
        if 'lat' in raw_data and 'lng' in raw_data:
            try:
                lat = float(raw_data['lat']) if raw_data['lat'] else None
                lng = float(raw_data['lng']) if raw_data['lng'] else None
                
                if lat and lng and self.config.validation.geo_bounds:
                    bounds = self.config.validation.geo_bounds
                    if (bounds['lat_min'] <= lat <= bounds['lat_max'] and
                        bounds['lng_min'] <= lng <= bounds['lng_max']):
                        normalized['lat'] = lat
                        normalized['lng'] = lng
            except (ValueError, TypeError):
                pass
        
        # 평점 처리
        if 'rating' in raw_data:
            rating = extract_rating(str(raw_data['rating']))
            if rating and 0 <= rating <= 5:
                normalized['rating'] = rating
        
        # 기타 필드 복사
        for field in ['category', 'cuisine_type', 'homepage_url', 'business_hours']:
            if field in raw_data and raw_data[field]:
                normalized[field] = normalize_text(str(raw_data[field]))
        
        # 숫자 필드 처리
        for field in ['review_count']:
            if field in raw_data:
                try:
                    value = int(raw_data[field])
                    if value >= 0:
                        normalized[field] = value
                except (ValueError, TypeError):
                    pass
        
        return normalized
    
    def normalize_menu_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """메뉴 데이터 정규화"""
        normalized = {}
        
        # 필수 필드
        if 'name' in raw_data:
            normalized['name'] = normalize_text(raw_data['name'])
        
        # 가격 처리
        if 'price' in raw_data:
            price = extract_price(str(raw_data['price']))
            if price and self.config.validation.price_bounds:
                bounds = self.config.validation.price_bounds
                if bounds['min'] <= price <= bounds['max']:
                    normalized['price'] = price
        
        # 기타 필드
        for field in ['description', 'category', 'image_url']:
            if field in raw_data and raw_data[field]:
                normalized[field] = normalize_text(str(raw_data[field]))
        
        # 불린 필드
        for field in ['is_signature', 'is_recommended']:
            if field in raw_data:
                normalized[field] = bool(raw_data[field])
        
        return normalized
    
    def validate_restaurant_data(self, data: Dict[str, Any]) -> List[str]:
        """식당 데이터 검증"""
        errors = []
        required_fields = self.validation_config.get('required_fields', {}).get('restaurant', [])
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"필수 필드 누락: {field}")
        
        # 형식 검증
        formats = self.validation_config.get('formats', {})
        
        if 'phone' in data and data['phone'] and 'phone' in formats:
            pattern = formats['phone']
            if not re.match(pattern, data['phone']):
                errors.append(f"전화번호 형식 오류: {data['phone']}")
        
        return errors
    
    def validate_menu_data(self, data: Dict[str, Any]) -> List[str]:
        """메뉴 데이터 검증"""
        errors = []
        required_fields = self.validation_config.get('required_fields', {}).get('menu', [])
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"필수 필드 누락: {field}")
        
        return errors
    
    def detect_blocking(self, content: str, url: str) -> Optional[str]:
        """차단 감지"""
        indicators = self.parser_config.get('blocking_detection', {}).get('indicators', [])
        
        content_lower = content.lower()
        for indicator in indicators:
            if indicator.lower() in content_lower:
                return indicator
        
        return None
    
    def is_empty_page(self, content: str) -> bool:
        """빈 페이지 감지"""
        if len(content.strip()) < 100:
            return True
        
        empty_selectors = self.parser_config.get('blocking_detection', {}).get(
            'empty_page_selectors', []
        )
        
        for selector in empty_selectors:
            if selector in content:
                return True
        
        return False
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """페이지 크롤링"""
        if not self.http_client:
            self.logger.error("HTTP 클라이언트가 설정되지 않았습니다")
            return None
        
        try:
            self.stats["requests_made"] += 1
            
            result = await self.http_client.fetch(
                url, 
                self.site, 
                self.parser_config
            )
            
            content = result.get('content', '')
            
            # 차단 감지
            blocking_indicator = self.detect_blocking(content, url)
            if blocking_indicator:
                self.stats["failed_requests"] += 1
                raise Exception(f"차단 감지: {blocking_indicator}")
            
            # 빈 페이지 감지
            if self.is_empty_page(content):
                self.stats["failed_requests"] += 1
                raise Exception("빈 페이지 감지")
            
            self.stats["successful_requests"] += 1
            return content
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            log_parser_error(self.site, "fetch", url, str(e))
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """파서 통계 반환"""
        success_rate = 0
        if self.stats["requests_made"] > 0:
            success_rate = self.stats["successful_requests"] / self.stats["requests_made"]
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "site": self.site
        }
    
    def reset_stats(self):
        """통계 초기화"""
        self.stats = {k: 0 for k in self.stats.keys()}


if __name__ == "__main__":
    # BaseParser 테스트는 추상 클래스이므로 직접 불가능
    print("BaseParser는 추상 클래스입니다.")
    print("구체적인 파서 구현체(예: SiksinParser)를 통해 테스트하세요.")