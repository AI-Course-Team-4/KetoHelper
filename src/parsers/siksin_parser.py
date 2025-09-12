"""
🍽️ 식신(Siksin) 파서 구현
- BaseParser 구현체
- 식신 사이트 전용 파싱 로직
- 검색 및 상세 정보 추출
"""

import re
import urllib.parse
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from .base_parser import BaseParser, ParseResult, SearchResult
from ..models import RestaurantCreate, MenuCreate
from ..utils.text_utils import normalize_text, extract_price


class SiksinParser(BaseParser):
    """식신 파서"""
    
    def __init__(self, http_client=None):
        super().__init__("siksin", http_client)
        self.base_url = self.site_config.get('base_url', 'https://www.siksin.com')
    
    async def search(self, keyword: str, page: int = 1) -> SearchResult:
        """식당 검색"""
        try:
            # 검색 URL 생성
            search_url = self._build_search_url(keyword, page)
            self.logger.info(f"식신 검색: {keyword} (페이지 {page})")
            
            # 페이지 크롤링
            content = await self.fetch_page(search_url)
            if not content:
                return SearchResult(
                    restaurants=[],
                    total_found=0,
                    page=page,
                    has_next_page=False,
                    metadata={'error': '페이지 로딩 실패'}
                )
            
            # 검색 결과 파싱
            return self._parse_search_results(content, keyword, page)
            
        except Exception as e:
            self.logger.error(f"검색 실패: {keyword} - {e}")
            return SearchResult(
                restaurants=[],
                total_found=0,
                page=page,
                has_next_page=False,
                metadata={'error': str(e)}
            )
    
    def _build_search_url(self, keyword: str, page: int = 1) -> str:
        """검색 URL 생성"""
        # URL 인코딩
        encoded_keyword = urllib.parse.quote(keyword)
        
        # 검색 URL 패턴에서 생성
        url_pattern = self.search_config.get('url_pattern')
        if url_pattern:
            return url_pattern.format(keyword=encoded_keyword, page=page)
        else:
            # 기본 패턴
            return f"{self.base_url}/search?query={encoded_keyword}&page={page}"
    
    def _parse_search_results(self, content: str, keyword: str, page: int) -> SearchResult:
        """검색 결과 파싱"""
        soup = BeautifulSoup(content, 'html.parser')
        restaurants = []
        
        try:
            # 식당 목록 컨테이너
            list_selector = self.search_config.get('selectors', {}).get('restaurant_list', '.restaurant-item')
            restaurant_elements = soup.select(list_selector)
            
            self.logger.debug(f"검색 결과 {len(restaurant_elements)}개 발견")
            
            for element in restaurant_elements:
                try:
                    restaurant_data = self._extract_search_item_data(element)
                    if restaurant_data and restaurant_data.get('name'):
                        
                        # 정규화
                        normalized_data = self.normalize_restaurant_data(restaurant_data, restaurant_data.get('source_url', ''))
                        
                        # 검증
                        errors = self.validate_restaurant_data(normalized_data)
                        if not errors:
                            restaurant = RestaurantCreate(**normalized_data)
                            restaurants.append(restaurant)
                            self.stats["restaurants_parsed"] += 1
                        else:
                            self.logger.warning(f"검증 실패: {errors}")
                            
                except Exception as e:
                    self.logger.warning(f"개별 식당 파싱 실패: {e}")
                    self.stats["parsing_errors"] += 1
                    continue
            
            # 다음 페이지 여부 확인
            has_next = self._has_next_page(soup)
            
            # 전체 결과 수 추정
            total_found = len(restaurants) + (page - 1) * 20  # 페이지당 20개 가정
            if has_next:
                total_found += 20  # 최소 다음 페이지 존재
            
            return SearchResult(
                restaurants=restaurants,
                total_found=total_found,
                page=page,
                has_next_page=has_next,
                metadata={
                    'keyword': keyword,
                    'found_count': len(restaurants),
                    'parsing_errors': self.stats["parsing_errors"]
                }
            )
            
        except Exception as e:
            self.logger.error(f"검색 결과 파싱 실패: {e}")
            return SearchResult(
                restaurants=[],
                total_found=0,
                page=page,
                has_next_page=False,
                metadata={'error': str(e)}
            )
    
    def _extract_search_item_data(self, element) -> Dict[str, Any]:
        """검색 결과 개별 항목 데이터 추출"""
        selectors = self.search_config.get('selectors', {})
        
        # 기본 정보 추출
        name = self._extract_text_from_element(element, selectors.get('restaurant_name', '.restaurant-name'))
        
        # URL 추출
        url_element = element.select_one(selectors.get('restaurant_url', 'a'))
        detail_url = ''
        if url_element:
            href = url_element.get('href', '')
            if href:
                if href.startswith('/'):
                    detail_url = self.base_url + href
                elif href.startswith('http'):
                    detail_url = href
                else:
                    detail_url = f"{self.base_url}/{href}"
        
        # 기타 정보
        address = self._extract_text_from_element(element, selectors.get('restaurant_address', '.address'))
        category = self._extract_text_from_element(element, selectors.get('restaurant_category', '.category'))
        rating_text = self._extract_text_from_element(element, selectors.get('restaurant_rating', '.rating'))
        
        # 평점 추출
        rating = None
        if rating_text:
            rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                    if rating > 5:  # 10점 만점을 5점 만점으로 변환
                        rating = rating / 2
                except ValueError:
                    pass
        
        return {
            'name': name,
            'source_url': detail_url,
            'address_road': address,
            'category': category,
            'rating': rating,
        }
    
    def _extract_text_from_element(self, element, selector: str) -> str:
        """요소에서 텍스트 추출"""
        try:
            if selector:
                sub_element = element.select_one(selector)
                if sub_element:
                    return normalize_text(sub_element.get_text(strip=True))
        except Exception:
            pass
        return ""
    
    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """다음 페이지 존재 여부"""
        try:
            next_selector = self.search_config.get('selectors', {}).get('next_page', '.pagination .next')
            next_element = soup.select_one(next_selector)
            
            # 다음 버튼이 있고 비활성화되지 않았다면
            if next_element and not next_element.get('class', []):
                return 'disabled' not in next_element.get('class', [])
            
            # 페이지 번호로 확인
            page_selector = self.search_config.get('selectors', {}).get('page_numbers', '.pagination .page-num')
            page_elements = soup.select(page_selector)
            
            return len(page_elements) > 0
            
        except Exception:
            return False
    
    async def parse_restaurant_detail(self, url: str) -> ParseResult:
        """식당 상세 정보 파싱"""
        try:
            self.logger.info(f"식당 상세 파싱: {url}")
            
            # 페이지 크롤링
            content = await self.fetch_page(url)
            if not content:
                return ParseResult(
                    success=False,
                    error="페이지 로딩 실패"
                )
            
            # 데이터 추출
            restaurant_data = self.extract_restaurant_data(content, url)
            menu_data = self.extract_menu_data(content, url)
            
            return ParseResult(
                success=True,
                data={
                    'restaurant': restaurant_data,
                    'menus': menu_data
                },
                metadata={
                    'url': url,
                    'menu_count': len(menu_data)
                }
            )
            
        except Exception as e:
            self.logger.error(f"상세 정보 파싱 실패: {url} - {e}")
            return ParseResult(
                success=False,
                error=str(e),
                metadata={'url': url}
            )
    
    def extract_restaurant_data(self, content: str, url: str) -> Dict[str, Any]:
        """식당 데이터 추출"""
        selectors = self.detail_config.get('selectors', {})
        
        # 기본 정보
        name = self.extract_text_by_selector(content, selectors.get('name', 'h1'))
        address_road = self.extract_text_by_selector(content, selectors.get('address', '.address'))
        address_jibun = self.extract_text_by_selector(content, selectors.get('address_jibun', '.jibun-address'))
        phone = self.extract_text_by_selector(content, selectors.get('phone', '.phone'))
        category = self.extract_text_by_selector(content, selectors.get('category', '.category'))
        rating_text = self.extract_text_by_selector(content, selectors.get('rating', '.rating'))
        hours = self.extract_text_by_selector(content, selectors.get('hours', '.hours'))
        
        # 평점 추출
        rating = None
        if rating_text:
            rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                    if rating > 5:  # 10점 만점을 5점 만점으로 변환
                        rating = rating / 2
                except ValueError:
                    pass
        
        # 좌표 추출
        lat, lng = self.extract_coordinates_from_content(content)
        
        # 리뷰 수 추출
        review_count = 0
        review_text = self.extract_text_by_selector(content, selectors.get('review_count', '.review-count'))
        if review_text:
            review_match = re.search(r'(\d+)', review_text)
            if review_match:
                try:
                    review_count = int(review_match.group(1))
                except ValueError:
                    pass
        
        return {
            'name': name,
            'address_road': address_road,
            'address_jibun': address_jibun,
            'lat': lat,
            'lng': lng,
            'phone': phone,
            'category': category,
            'rating': rating,
            'review_count': review_count,
            'business_hours': hours,
            'source_url': url,
        }
    
    def extract_menu_data(self, content: str, url: str) -> List[Dict[str, Any]]:
        """메뉴 데이터 추출"""
        selectors = self.detail_config.get('selectors', {})
        menus = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 메뉴 섹션 찾기
            menu_section_selector = selectors.get('menu_section', '.menu-section')
            menu_sections = soup.select(menu_section_selector)
            
            for section in menu_sections:
                # 메뉴 항목들
                menu_item_selector = selectors.get('menu_items', '.menu-item')
                menu_items = section.select(menu_item_selector)
                
                for item in menu_items:
                    try:
                        # 메뉴명
                        name_selector = selectors.get('menu_name', '.menu-name')
                        name_element = item.select_one(name_selector)
                        if not name_element:
                            continue
                        
                        name = normalize_text(name_element.get_text(strip=True))
                        if not name:
                            continue
                        
                        # 가격
                        price = None
                        price_selector = selectors.get('menu_price', '.menu-price')
                        price_element = item.select_one(price_selector)
                        if price_element:
                            price_text = price_element.get_text(strip=True)
                            price = extract_price(price_text)
                        
                        # 설명
                        description = ""
                        desc_selector = selectors.get('menu_description', '.menu-description')
                        desc_element = item.select_one(desc_selector)
                        if desc_element:
                            description = normalize_text(desc_element.get_text(strip=True))
                        
                        # 이미지
                        image_url = ""
                        img_element = item.select_one('img')
                        if img_element:
                            src = img_element.get('src', '') or img_element.get('data-src', '')
                            if src:
                                if src.startswith('/'):
                                    image_url = self.base_url + src
                                elif src.startswith('http'):
                                    image_url = src
                        
                        # 대표 메뉴 여부 (예: 추천, 인기, 시그니처 키워드)
                        is_signature = self._is_signature_menu(name, description, item)
                        
                        menu_data = {
                            'name': name,
                            'price': price,
                            'description': description,
                            'image_url': image_url,
                            'is_signature': is_signature,
                            'currency': 'KRW'
                        }
                        
                        # 검증
                        menu_errors = self.validate_menu_data(menu_data)
                        if not menu_errors:
                            menus.append(menu_data)
                            self.stats["menus_parsed"] += 1
                        
                    except Exception as e:
                        self.logger.warning(f"개별 메뉴 파싱 실패: {e}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"메뉴 섹션 파싱 실패: {e}")
        
        return menus
    
    def _is_signature_menu(self, name: str, description: str, element) -> bool:
        """대표 메뉴 여부 판단"""
        # 키워드 기반 판단
        signature_keywords = ['추천', '인기', '시그니처', '대표', '베스트', '특선']
        text = f"{name} {description}".lower()
        
        for keyword in signature_keywords:
            if keyword in text:
                return True
        
        # 특별한 스타일이나 배지가 있는지 확인
        try:
            # 추천 배지나 아이콘
            if element.select('.recommend, .popular, .signature, .best'):
                return True
            
            # 특별한 클래스명
            classes = element.get('class', [])
            for cls in classes:
                if any(keyword in cls.lower() for keyword in ['recommend', 'popular', 'signature', 'best']):
                    return True
                    
        except Exception:
            pass
        
        return False
    
    def get_site_info(self) -> Dict[str, Any]:
        """사이트 정보 반환"""
        return {
            'name': self.site_config.get('display_name', '식신'),
            'base_url': self.base_url,
            'trust_rank': self.site_config.get('trust_rank', 1),
            'supported_features': [
                'restaurant_search',
                'restaurant_detail',
                'menu_extraction',
                'rating_extraction',
                'coordinate_extraction'
            ]
        }


# 테스트 및 디버그용 함수들
def create_test_parser():
    """테스트용 파서 생성"""
    return SiksinParser()


async def test_search(keyword: str = "강남 맛집", page: int = 1):
    """검색 테스트"""
    parser = create_test_parser()
    result = await parser.search(keyword, page)
    
    print(f"=== 검색 테스트: {keyword} ===")
    print(f"발견된 식당: {len(result.restaurants)}개")
    print(f"전체 추정: {result.total_found}개")
    print(f"다음 페이지: {result.has_next_page}")
    
    for i, restaurant in enumerate(result.restaurants[:3]):  # 처음 3개만
        print(f"\n{i+1}. {restaurant.name}")
        print(f"   주소: {restaurant.address_road}")
        print(f"   카테고리: {restaurant.category}")
        print(f"   평점: {restaurant.rating}")
        print(f"   URL: {restaurant.source_url}")
    
    return result


async def test_detail_parsing(url: str):
    """상세 정보 파싱 테스트"""
    parser = create_test_parser()
    result = await parser.parse_restaurant_detail(url)
    
    print(f"=== 상세 파싱 테스트: {url} ===")
    print(f"성공 여부: {result.success}")
    
    if result.success and result.data:
        restaurant = result.data.get('restaurant', {})
        menus = result.data.get('menus', [])
        
        print(f"\n식당 정보:")
        print(f"  이름: {restaurant.get('name')}")
        print(f"  주소: {restaurant.get('address_road')}")
        print(f"  전화: {restaurant.get('phone')}")
        print(f"  좌표: {restaurant.get('lat')}, {restaurant.get('lng')}")
        print(f"  평점: {restaurant.get('rating')}")
        
        print(f"\n메뉴 ({len(menus)}개):")
        for menu in menus[:5]:  # 처음 5개만
            print(f"  - {menu['name']}: {menu.get('price', '가격미표시')}원")
            if menu.get('is_signature'):
                print(f"    (대표 메뉴)")
    
    else:
        print(f"파싱 실패: {result.error}")
    
    return result


if __name__ == "__main__":
    import asyncio
    
    # 테스트 실행
    async def main():
        # 검색 테스트
        search_result = await test_search("강남 맛집")
        
        # 첫 번째 결과의 상세 정보 테스트
        if search_result.restaurants:
            first_restaurant = search_result.restaurants[0]
            if first_restaurant.source_url:
                await test_detail_parsing(first_restaurant.source_url)
    
    asyncio.run(main())