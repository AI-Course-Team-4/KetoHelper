"""
다이닝코드 크롤러 구현
"""

import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from selectolax.parser import HTMLParser
import logging

from services.crawler.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

def clean_menu_name(name: str) -> str:
    """메뉴명 전처리 함수"""
    if not name:
        return name
        
    original_name = name
    
    # 1. "메뉴정보" 접두사 제거
    name = name.replace("메뉴정보 ", "")
    
    # 2. "추천 숫자" 패턴 제거 (예: "추천 1", "추천 2")
    name = re.sub(r'\s+추천\s+\d+$', '', name)
    
    # 3. 끝의 단독 숫자 제거 (예: "돈육전 1" -> "돈육전")
    # 단, 용량/수량 정보는 보존 (예: "150g", "500ml")
    name = re.sub(r'\s+\d+$', '', name)
    
    # 4. 연속된 공백을 하나로 정리
    name = re.sub(r'\s+', ' ', name)
    
    # 5. 앞뒤 공백 제거
    name = name.strip()
    
    # 6. 빈 문자열이 되면 원본 반환
    if not name:
        return original_name
        
    return name

class DiningcodeCrawler(BaseCrawler):
    """다이닝코드 크롤러"""

    BASE_DOMAIN = "www.diningcode.com"
    BASE_URL = f"https://{BASE_DOMAIN}"

    @property
    def source_name(self) -> str:
        return "diningcode"

    def _get_base_domain(self) -> str:
        return self.BASE_DOMAIN

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        """검색 URL 생성"""
        # 다이닝코드 검색 URL 패턴
        return f"{self.BASE_URL}/list?keyword={keyword}&page={page}"

    def is_restaurant_url(self, url: str) -> bool:
        """식당 상세 페이지 URL 여부 확인"""
        # 다이닝코드 식당 URL 패턴: /profile.php?rid=숫자
        return bool(re.search(r'/profile\.php\?rid=\d+', url))

    def _extract_restaurant_urls_from_search(self, html: str) -> List[str]:
        """검색 결과에서 식당 URL 추출 - JavaScript JSON 데이터에서 추출"""
        urls = []
        
        try:
            # JavaScript의 listData에서 JSON 데이터 추출
            import json
            
            # listData 변수 찾기
            listdata_pattern = r"localStorage\.setItem\('listData',\s*'([^']+)'\)"
            listdata_match = re.search(listdata_pattern, html)
            
            if listdata_match:
                # JSON 문자열 디코딩
                json_str = listdata_match.group(1)
                # 유니코드 이스케이프 문자 디코딩
                json_str = json_str.encode().decode('unicode_escape')
                
                try:
                    data = json.loads(json_str)
                    
                    # poi_section > list에서 식당 정보 추출
                    if 'poi_section' in data and 'list' in data['poi_section']:
                        restaurants = data['poi_section']['list']
                        
                        for restaurant in restaurants:
                            if 'v_rid' in restaurant:
                                # 식당 URL 생성
                                restaurant_url = f"https://www.diningcode.com/profile.php?rid={restaurant['v_rid']}"
                                urls.append(restaurant_url)
                                
                        logger.info(f"JSON 데이터에서 {len(urls)}개 식당 URL 추출 완료")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 파싱 오류: {e}")
            
            # JSON 추출 실패시 기존 방법으로 시도
            if not urls:
                logger.warning("JSON 데이터 추출 실패, HTML 파싱으로 시도")
                tree = HTMLParser(html)
                
                # 다이닝코드 특정 선택자 사용
                for link in tree.css('a.btxt'):
                    if link.attributes:
                        href = link.attributes.get('href', '')
                        if self.is_restaurant_url(href):
                            full_url = self._normalize_url(href)
                            urls.append(full_url)

                # 대체 선택자들
                if not urls:
                    selectors = [
                        'a[href*="profile.php"]',
                        'a[href*="rid="]'
                    ]
                    
                    for selector in selectors:
                        for link in tree.css(selector):
                            if link.attributes:
                                href = link.attributes.get('href', '')
                                if self.is_restaurant_url(href):
                                    full_url = self._normalize_url(href)
                                    urls.append(full_url)
                        if urls:  # 하나라도 찾으면 중단
                            break
            
        except Exception as e:
            logger.error(f"URL 추출 중 오류 발생: {e}")
        
        return list(set(urls))  # 중복 제거

    async def extract_restaurant_info(self, html: str, url: str) -> Dict[str, Any]:
        """HTML에서 식당 정보 추출"""
        tree = HTMLParser(html)
        info = {}

        try:
            # 식당명
            name_element = tree.css_first('h1.tit, .tit h1, .restaurant_name h1, h1')
            if name_element:
                info['name'] = self._clean_text(name_element.text())

            # 주소 - 텍스트 패턴에서 추출
            text_content = tree.text()
            addr_patterns = [
                r'서울특별시\s+[^0-9]*?구\s+[^0-9]*?[동로길][^0-9]*?\d+[^0-9]*?[^\n]*',
                r'서울\s+[^0-9]*?구\s+[^0-9]*?[동로길][^0-9]*?\d+[^0-9]*?[^\n]*'
            ]
            
            for pattern in addr_patterns:
                addr_matches = re.findall(pattern, text_content)
                if addr_matches:
                    # 가장 완전한 주소 선택
                    full_address = max(addr_matches, key=len)
                    info['address'] = self._clean_text(full_address)
                    break

            # 전화번호 - 개선된 선택자와 패턴 매칭
            phone_element = tree.css_first('.tel, .phone, .contact')
            if phone_element:
                phone_text = self._clean_text(phone_element.text())
                # 전화번호 정규화
                phone_clean = re.sub(r'[^\d-]', '', phone_text)
                if phone_clean and len(phone_clean) >= 10:
                    info['phone'] = phone_clean
            else:
                # 텍스트에서 전화번호 패턴 찾기
                phone_patterns = [r'0\d{1,2}-\d{3,4}-\d{4}', r'\d{3,4}-\d{3,4}-\d{4}']
                for pattern in phone_patterns:
                    phone_matches = re.findall(pattern, text_content)
                    if phone_matches:
                        info['phone'] = phone_matches[0]
                        break

            # 영업시간
            hours_element = tree.css_first('.hours, .time, .business_hours')
            if hours_element:
                info['business_hours'] = self._clean_text(hours_element.text())

            # 평점 - 개선된 선택자
            score_element = tree.css_first('.score, .rating, .rate_point')
            if score_element:
                score_text = self._clean_text(score_element.text())
                score_match = re.search(r'(\d+\.?\d*)', score_text)
                if score_match:
                    try:
                        score_value = float(score_match.group(1))
                        # 100점 만점을 5점 만점으로 변환
                        if score_value > 10:
                            info['rating'] = round(score_value / 20, 1)
                        else:
                            info['rating'] = score_value
                    except ValueError:
                        pass

            # 리뷰 수
            review_element = tree.css_first('.Rating .rate_count, .rating .count, .review_count')
            if review_element:
                review_text = self._clean_text(review_element.text())
                review_count = self._extract_number(review_text)
                if review_count:
                    info['review_count'] = review_count

            # 요리 종류/카테고리
            category_elements = tree.css('.Restaurant_Category, .category, .food_type')
            if category_elements:
                categories = []
                for elem in category_elements:
                    cat_text = self._clean_text(elem.text())
                    if cat_text:
                        categories.append(cat_text)
                if categories:
                    info['cuisine_types'] = categories

            # 가격대
            price_element = tree.css_first('.Restaurant_Price, .price_range, .price')
            if price_element:
                price_text = self._clean_text(price_element.text())
                info['price_range'] = self._classify_price_range(price_text)

            # 메타데이터
            info['source_url'] = url
            info['source_name'] = self.source_name

            # 데이터 검증
            if not info.get('name'):
                logger.warning(f"No restaurant name found for URL: {url}")

            return info

        except Exception as e:
            logger.error(f"Error extracting restaurant info from {url}: {e}")
            return {'source_url': url, 'source_name': self.source_name}

    async def extract_menu_list(self, html: str, url: str) -> List[Dict[str, Any]]:
        """HTML에서 메뉴 리스트 추출"""
        tree = HTMLParser(html)
        menus = []

        try:
            # 다이닝코드 메뉴 섹션 찾기
            menu_sections = [
                '.Menu_List',
                '.menu_list',
                '.Restaurant_Menu',
                '.menu_info',
                '.menu_section'
            ]

            menu_container = None
            for selector in menu_sections:
                menu_container = tree.css_first(selector)
                if menu_container:
                    break

            if not menu_container:
                # 대체 방법: 메뉴 아이템을 직접 찾기
                menu_items = tree.css('.menu_item, .Menu_Item, .menu, .food_menu')
            else:
                menu_items = menu_container.css('.menu_item, .Menu_Item, .menu, .food_menu')

            for item in menu_items:
                menu_info = self._extract_single_menu(item)
                if menu_info and menu_info.get('name'):
                    menus.append(menu_info)

            # 메뉴가 없다면 다른 패턴으로 시도
            if not menus:
                menus = self._extract_menus_alternative_method(tree)

            logger.info(f"Extracted {len(menus)} menus from {url}")
            return menus

        except Exception as e:
            logger.error(f"Error extracting menu list from {url}: {e}")
            return []

    def _extract_single_menu(self, menu_element) -> Optional[Dict[str, Any]]:
        """단일 메뉴 정보 추출"""
        try:
            menu_info = {}

            # 메뉴명
            name_selectors = ['.menu_name', '.name', '.title', '.menu_title', 'h3', 'h4']
            for selector in name_selectors:
                name_elem = menu_element.css_first(selector)
                if name_elem:
                    name = self._clean_text(name_elem.text())
                    if name:
                        # 메뉴명 전처리 적용
                        menu_info['name'] = clean_menu_name(name)
                        break

            # 가격
            price_selectors = ['.menu_price', '.price', '.cost', '.amount']
            for selector in price_selectors:
                price_elem = menu_element.css_first(selector)
                if price_elem:
                    price_text = self._clean_text(price_elem.text())
                    price = self._extract_price(price_text)
                    if price:
                        menu_info['price'] = price
                        break

            # 설명
            desc_selectors = ['.menu_desc', '.description', '.desc', '.menu_detail']
            for selector in desc_selectors:
                desc_elem = menu_element.css_first(selector)
                if desc_elem:
                    desc = self._clean_text(desc_elem.text())
                    if desc and len(desc) > 5:  # 의미있는 설명만
                        menu_info['description'] = desc
                        break

            return menu_info if menu_info.get('name') else None

        except Exception as e:
            logger.debug(f"Error extracting single menu: {e}")
            return None

    def _extract_menus_alternative_method(self, tree: HTMLParser) -> List[Dict[str, Any]]:
        """대체 메뉴 추출 방법"""
        menus = []

        # 텍스트에서 메뉴 패턴 찾기
        text_content = tree.text()
        menu_patterns = [
            r'([가-힣\w\s]+)\s*[:\-]\s*(\d+[,\d]*)\s*원',
            r'([가-힣\w\s]+)\s*(\d+[,\d]*)\s*원',
            r'◦\s*([가-힣\w\s]+)\s*(\d+[,\d]*)'
        ]

        for pattern in menu_patterns:
            matches = re.finditer(pattern, text_content)
            for match in matches:
                name = self._clean_text(match.group(1))
                price_text = match.group(2).replace(',', '')

                if len(name) > 2 and name not in ['전화번호', '주소', '영업시간']:
                    try:
                        price = int(price_text)
                        if 1000 <= price <= 500000:  # 합리적인 가격 범위
                            menus.append({
                                'name': clean_menu_name(name),  # 메뉴명 전처리 적용
                                'price': price
                            })
                    except ValueError:
                        continue

        return menus[:20]  # 최대 20개로 제한

    def _extract_price(self, price_text: str) -> Optional[int]:
        """가격 텍스트에서 숫자 추출"""
        if not price_text:
            return None

        # 숫자와 콤마만 추출
        price_clean = re.sub(r'[^\d,]', '', price_text)
        price_clean = price_clean.replace(',', '')

        if price_clean.isdigit():
            price = int(price_clean)
            # 합리적인 가격 범위 체크
            if 500 <= price <= 1000000:
                return price

        return None

    def _classify_price_range(self, price_text: str) -> Optional[str]:
        """가격대 분류"""
        if not price_text:
            return None

        price_text = price_text.lower()

        if any(keyword in price_text for keyword in ['저렴', '만원 이하', '경제적']):
            return 'low'
        elif any(keyword in price_text for keyword in ['고급', '비싼', '프리미엄', '5만원 이상']):
            return 'high'
        elif any(keyword in price_text for keyword in ['보통', '적당', '2-3만원']):
            return 'medium'

        # 숫자에서 판단
        prices = re.findall(r'\d+', price_text.replace(',', ''))
        if prices:
            avg_price = sum(int(p) for p in prices) / len(prices)
            if avg_price < 15000:
                return 'low'
            elif avg_price > 50000:
                return 'high'
            else:
                return 'medium'

        return None