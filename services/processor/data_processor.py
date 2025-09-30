"""
크롤링 데이터 처리 및 정규화 서비스
"""

import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import logging

from core.domain.restaurant import Restaurant, Address, BusinessHours, RestaurantSource
from core.domain.menu import Menu, NutritionInfo
from core.domain.enums import SourceType, MenuCategory, PriceRange
from services.processor.geocoding_service import GeocodingService
from services.processor.deduplication_service import DeduplicationService

logger = logging.getLogger(__name__)

class DataProcessor:
    """크롤링 데이터 처리 및 정규화"""

    def __init__(
        self,
        geocoding_service: Optional[GeocodingService] = None,
        deduplication_service: Optional[DeduplicationService] = None
    ):
        self.geocoding_service = geocoding_service
        self.deduplication_service = deduplication_service

    async def process_crawl_result(self, crawl_data: Dict[str, Any]) -> Tuple[Restaurant, List[Menu]]:
        """크롤링 결과 처리"""
        try:
            # 식당 정보 처리
            restaurant = await self.process_restaurant_data(crawl_data['restaurant'])

            # 메뉴 정보 처리
            menus = []
            if 'menus' in crawl_data and crawl_data['menus']:
                for menu_data in crawl_data['menus']:
                    menu = await self.process_menu_data(menu_data, restaurant.id)
                    if menu:
                        menus.append(menu)

            return restaurant, menus

        except Exception as e:
            logger.error(f"Error processing crawl result: {e}")
            raise

    async def process_restaurant_data(self, raw_data: Dict[str, Any]) -> Restaurant:
        """원시 식당 데이터를 Restaurant 객체로 변환"""
        try:
            # 필수 데이터 검증
            if not raw_data.get('name'):
                raise ValueError("Restaurant name is required")

            # 기본 정보 정규화
            name = self._clean_restaurant_name(raw_data['name'])
            phone = self._normalize_phone(raw_data.get('phone'))

            # 주소 처리
            address = None
            if raw_data.get('address'):
                address = await self._process_address(raw_data['address'])

            # 영업시간 처리
            business_hours = None
            if raw_data.get('business_hours'):
                business_hours = self._process_business_hours(raw_data['business_hours'])

            # 요리 종류 정규화
            cuisine_types = []
            if raw_data.get('cuisine_types'):
                cuisine_types = [
                    self._normalize_text(ct) for ct in raw_data['cuisine_types']
                    if ct and len(ct.strip()) > 1
                ]

            # 가격대 정규화
            price_range = None
            if raw_data.get('price_range'):
                price_range = self._normalize_price_range(raw_data['price_range'])

            # 평점 정보
            rating_avg = None
            if raw_data.get('rating'):
                try:
                    rating = float(raw_data['rating'])
                    if 0 <= rating <= 5:
                        rating_avg = Decimal(str(rating))
                except (ValueError, TypeError):
                    pass

            review_count = raw_data.get('review_count', 0)
            if not isinstance(review_count, int) or review_count < 0:
                review_count = 0

            # Restaurant 객체 생성
            restaurant = Restaurant(
                name=name,
                source=raw_data.get('source', 'diningcode'),
                source_url=raw_data.get('source_url', ''),
                phone=phone,
                address=address,
                category=cuisine_types[0] if cuisine_types else None,
                price_range=price_range
            )

            # 소스 정보 추가
            if raw_data.get('source_url') and raw_data.get('source_name'):
                source = RestaurantSource(
                    source_name=SourceType(raw_data['source_name']),
                    source_url=raw_data['source_url'],
                    name_raw=raw_data.get('name', ''),
                    addr_raw=raw_data.get('address', ''),
                    phone_raw=raw_data.get('phone', ''),
                    data_raw=raw_data,
                    is_primary=True
                )
                restaurant.add_source(source)

            return restaurant

        except Exception as e:
            logger.error(f"Error processing restaurant data: {e}")
            raise

    async def process_menu_data(self, raw_data: Dict[str, Any], restaurant_id) -> Optional[Menu]:
        """원시 메뉴 데이터를 Menu 객체로 변환"""
        try:
            # 필수 데이터 검증
            if not raw_data.get('name'):
                logger.debug("Menu name is required, skipping")
                return None

            # 기본 정보 정규화
            name = self._clean_menu_name(raw_data['name'])
            
            # 정제된 메뉴명이 비어있으면 건너뛰기
            if not name or len(name.strip()) == 0:
                logger.debug(f"Menu name is empty after cleaning: '{raw_data['name']}', skipping")
                return None
            
            description = None
            if raw_data.get('description'):
                description = self._normalize_text(raw_data['description'])

            # 가격 정규화
            price = None
            if raw_data.get('price'):
                price = self._normalize_price(raw_data['price'])

            # 카테고리 추론
            category = self._infer_menu_category(name, description)

            # Menu 객체 생성
            menu = Menu(
                restaurant_id=restaurant_id,
                name=name,
                description=description,
                price=price,
                category=category
            )

            return menu

        except Exception as e:
            logger.error(f"Error processing menu data: {e}")
            return None

    async def process_batch(self, crawl_results: List[Dict[str, Any]]) -> List[Tuple[Restaurant, List[Menu]]]:
        """크롤링 결과 일괄 처리"""
        processed_results = []

        for crawl_data in crawl_results:
            try:
                restaurant, menus = await self.process_crawl_result(crawl_data)
                processed_results.append((restaurant, menus))
            except Exception as e:
                logger.error(f"Error processing crawl data: {e}")
                continue

        return processed_results

    async def deduplicate_restaurants(self, restaurants: List[Restaurant]) -> List[Restaurant]:
        """식당 중복 제거"""
        if not self.deduplication_service:
            logger.warning("Deduplication service not available")
            return restaurants

        return await self.deduplication_service.deduplicate_restaurants(restaurants)

    async def _process_address(self, address_text: str) -> Optional[Address]:
        """주소 처리 및 지오코딩"""
        try:
            # 주소 정규화
            normalized_addr = self._normalize_address(address_text)

            # 지오코딩 시도
            geocoded = None
            if self.geocoding_service:
                geocoded = await self.geocoding_service.geocode(normalized_addr)

            if geocoded:
                return Address(
                    addr_road=geocoded.get('road_address') or geocoded.get('formatted_address'),
                    addr_jibun=geocoded.get('jibun_address'),
                    latitude=float(geocoded['lat']) if geocoded.get('lat') else None,
                    longitude=float(geocoded['lng']) if geocoded.get('lng') else None
                )
            else:
                return Address(addr_road=address_text)

        except Exception as e:
            logger.error(f"Error processing address '{address_text}': {e}")
            return Address(addr_road=address_text)

    def _process_business_hours(self, hours_text: str) -> Optional[BusinessHours]:
        """영업시간 텍스트 파싱"""
        try:
            # 간단한 파싱 - 나중에 개선 가능
            return BusinessHours(
                monday=hours_text,
                tuesday=hours_text,
                wednesday=hours_text,
                thursday=hours_text,
                friday=hours_text,
                saturday=hours_text,
                sunday=hours_text
            )
        except Exception as e:
            logger.debug(f"Error parsing business hours: {e}")
            return None

    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        if not text:
            return ""

        # 공백 정리
        text = re.sub(r'\s+', ' ', text.strip())

        # 특수문자 제거 (일부)
        text = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ\-\(\)\[\]]', '', text)

        return text.strip()

    def _clean_menu_name(self, menu_name: str) -> str:
        """메뉴명 정제 (길이 제한 25자, 노이즈 제거)"""
        if not menu_name:
            return ""

        # 1. 특정 패턴 추출 (맛집 설명에서 실제 메뉴명 추출)
        # "강남역 회전초밥 맛집 갓덴스시 강남점 메뉴 및 가격 녹색접시" → "녹색접시"
        if '맛집' in menu_name and '메뉴' in menu_name and '가격' in menu_name:
            # 가격 뒤의 마지막 단어를 메뉴명으로 추출
            parts = menu_name.split()
            if len(parts) > 0:
                menu_name = parts[-1]

        # 2. 길이 제한 (25자 초과시 설명이 포함된 것으로 판단)
        if len(menu_name) > 25:
            # 문장 부호로 분리하여 첫 번째 부분만 사용
            parts = re.split(r'[.!?]', menu_name)
            menu_name = parts[0].strip()
            
            # 여전히 길면 첫 25자만 사용
            if len(menu_name) > 25:
                menu_name = menu_name[:25]
        
        # 3. 노이즈 제거
        noise_patterns = [
            r'먼저.*꿀팁.*',  # 설명 텍스트
            r'^시그니처 아메리카노$',  # 공통 메뉴 제거 (정확히 일치)
            r'.*시간.*매일.*라스트오더.*',  # 영업시간 정보
        ]
        
        for pattern in noise_patterns:
            menu_name = re.sub(pattern, '', menu_name)

        # 4. 공백 정리
        menu_name = re.sub(r'\s+', ' ', menu_name).strip()

        # 5. 특수문자 정리
        menu_name = re.sub(r'[^\w가-힣\s]', '', menu_name)

        return menu_name.strip()

    def _clean_restaurant_name(self, restaurant_name: str) -> str:
        """식당명 정제"""
        if not restaurant_name:
            return ""

        # 1. 지점명 제거
        restaurant_name = re.sub(r'\s+(강남점|역삼점|강남역점|본점|본진)$', '', restaurant_name)

        # 2. 주소 정보 제거
        restaurant_name = re.sub(r'\s+서울.*$', '', restaurant_name)

        # 3. 영업시간 정보 제거
        restaurant_name = re.sub(r'\s+⏰.*$', '', restaurant_name)

        # 4. 전화번호 제거
        restaurant_name = re.sub(r'\s+0\d{2,3}-\d{3,4}-\d{4}', '', restaurant_name)

        # 5. 기타 노이즈 제거
        restaurant_name = re.sub(r'\s+지번.*$', '', restaurant_name)
        restaurant_name = re.sub(r'\s+\d+층.*$', '', restaurant_name)

        return restaurant_name.strip()

    def _normalize_phone(self, phone: str) -> Optional[str]:
        """전화번호 정규화"""
        if not phone:
            return None

        # 숫자와 하이픈만 추출
        phone_clean = re.sub(r'[^\d\-]', '', phone)

        # 전화번호 패턴 체크
        phone_patterns = [
            r'^0\d{1,2}-\d{3,4}-\d{4}$',  # 지역번호-중간번호-끝번호
            r'^0\d{9,10}$',               # 하이픈 없는 형태
            r'^01\d-\d{3,4}-\d{4}$'       # 휴대폰
        ]

        # 하이픈 추가 시도
        if re.match(r'^0\d{9,10}$', phone_clean):
            if len(phone_clean) == 10:
                phone_clean = f"{phone_clean[:3]}-{phone_clean[3:6]}-{phone_clean[6:]}"
            elif len(phone_clean) == 11:
                if phone_clean.startswith('02'):
                    phone_clean = f"{phone_clean[:2]}-{phone_clean[2:6]}-{phone_clean[6:]}"
                else:
                    phone_clean = f"{phone_clean[:3]}-{phone_clean[3:7]}-{phone_clean[7:]}"

        # 패턴 검증
        for pattern in phone_patterns:
            if re.match(pattern, phone_clean):
                return phone_clean

        # 원래 텍스트가 합리적이면 반환
        if 8 <= len(phone_clean.replace('-', '')) <= 11:
            return phone_clean

        return None

    def _normalize_address(self, address: str) -> str:
        """주소 정규화"""
        if not address:
            return ""

        # 기본 정리
        address = self._normalize_text(address)

        # 주소 관련 정리
        address = re.sub(r'(\d+)층', r'\1층', address)  # 층수 정리
        address = re.sub(r'(\d+)번지', r'\1번지', address)  # 번지 정리

        return address

    def _normalize_price(self, price_data: Any) -> Optional[int]:
        """가격 정규화"""
        if price_data is None:
            return None

        try:
            if isinstance(price_data, int):
                return price_data if price_data > 0 else None

            if isinstance(price_data, str):
                # 숫자만 추출
                price_clean = re.sub(r'[^\d]', '', price_data)
                if price_clean:
                    price_int = int(price_clean)
                    # 합리적인 범위 체크
                    return price_int if 100 <= price_int <= 1000000 else None

            return None
        except (ValueError, TypeError):
            return None

    def _normalize_price_range(self, price_range: str) -> Optional[PriceRange]:
        """가격대 정규화"""
        if not price_range:
            return None

        price_range_lower = price_range.lower()

        if price_range_lower in ['low', '저렴', '경제적']:
            return PriceRange.LOW
        elif price_range_lower in ['medium', '보통', '적당']:
            return PriceRange.MEDIUM
        elif price_range_lower in ['high', '비싼', '고급']:
            return PriceRange.HIGH
        elif price_range_lower in ['premium', '프리미엄', '최고급']:
            return PriceRange.PREMIUM

        return None

    def _infer_menu_category(self, name: str, description: str = None) -> MenuCategory:
        """메뉴 카테고리 추론"""
        text = (name + ' ' + (description or '')).lower()

        # 음료 키워드
        if any(keyword in text for keyword in ['음료', '차', '커피', '주스', '물', '맥주', '소주', '와인', '칵테일']):
            return MenuCategory.DRINK

        # 디저트 키워드
        if any(keyword in text for keyword in ['디저트', '케이크', '아이스크림', '과일', '달콤']):
            return MenuCategory.DESSERT

        # 사이드 키워드
        if any(keyword in text for keyword in ['사이드', '반찬', '김치', '무', '소스', '추가']):
            return MenuCategory.SIDE

        # 세트 키워드
        if any(keyword in text for keyword in ['세트', '정식', '코스', '모둠', '플래터']):
            return MenuCategory.SET

        # 기본은 메인
        return MenuCategory.MAIN