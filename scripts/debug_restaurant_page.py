#!/usr/bin/env python3
"""
식당 상세 페이지 HTML 구조 분석
"""

import asyncio
import sys
import logging
from pathlib import Path
from selectolax.parser import HTMLParser

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.crawler_config import register_crawlers
from services.crawler.crawler_factory import crawler_factory

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_restaurant_page():
    """식당 상세 페이지 HTML 구조 분석"""
    logger.info("식당 상세 페이지 분석 시작")
    
    # 크롤러 등록
    register_crawlers()
    
    # 크롤러 생성
    crawler = crawler_factory.create('diningcode')
    
    try:
        await crawler.initialize()
        
        # 테스트할 식당 URL (위트앤미트 강남점)
        test_url = "https://www.diningcode.com/profile.php?rid=FJfopWlhuzJj"
        logger.info(f"분석할 URL: {test_url}")
        
        # HTML 가져오기
        response = await crawler._client.get(test_url)
        html_content = response.text
        
        logger.info(f"HTML 길이: {len(html_content)}")
        
        # HTML 파일로 저장
        html_file = Path("data/cache/restaurant_detail.html")
        html_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML 저장됨: {html_file}")
        
        # HTML 파싱
        tree = HTMLParser(html_content)
        
        # 다양한 선택자 테스트
        logger.info("\n=== 식당명 찾기 ===")
        name_selectors = [
            'h1.tit', '.tit h1', '.restaurant_name h1', 
            'h1', '.restaurant-name', '.name', '.title',
            '.RestaurantTitle', '.restaurant_title'
        ]
        
        for selector in name_selectors:
            elements = tree.css(selector)
            if elements:
                logger.info(f"{selector}: {len(elements)}개 - '{elements[0].text()}'")
        
        logger.info("\n=== 주소 찾기 ===")
        addr_selectors = [
            '.txt .Restaurant_Address', '.restaurant_info .addr', '.addr',
            '.address', '.location', '.Restaurant_Info .address',
            '.info .address', '.detail .address'
        ]
        
        for selector in addr_selectors:
            elements = tree.css(selector)
            if elements:
                logger.info(f"{selector}: {len(elements)}개 - '{elements[0].text()}'")
        
        logger.info("\n=== 전화번호 찾기 ===")
        phone_selectors = [
            '.txt .Restaurant_Phone', '.restaurant_info .phone', '.phone',
            '.tel', '.contact', '.Restaurant_Info .phone'
        ]
        
        for selector in phone_selectors:
            elements = tree.css(selector)
            if elements:
                logger.info(f"{selector}: {len(elements)}개 - '{elements[0].text()}'")
        
        logger.info("\n=== 평점 찾기 ===")
        rating_selectors = [
            '.Rating .rate_point', '.rating .point', '.rate_point',
            '.score', '.stars', '.rating-score', '.rate'
        ]
        
        for selector in rating_selectors:
            elements = tree.css(selector)
            if elements:
                logger.info(f"{selector}: {len(elements)}개 - '{elements[0].text()}'")
        
        logger.info("\n=== 주요 클래스 분석 ===")
        # 주요 div들의 클래스 확인
        for div in tree.css('div[class]')[:20]:  # 처음 20개만
            if div.attributes:
                class_attr = div.attributes.get('class', '')
                if class_attr and ('restaurant' in class_attr.lower() or 'info' in class_attr.lower()):
                    text_preview = div.text()[:100] if div.text() else ''
                    logger.info(f"클래스: {class_attr} - 텍스트: {text_preview}")
        
        # 텍스트에서 주소/전화번호 패턴 찾기
        logger.info("\n=== 텍스트 패턴 분석 ===")
        text_content = tree.text()
        
        # 주소 패턴
        import re
        addr_patterns = [
            r'서울[^0-9]*?[구][^0-9]*?[동로길][^0-9]*?\d+',
            r'서울.*?구.*?[동로길].*?\d+',
        ]
        
        for pattern in addr_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                logger.info(f"주소 패턴 '{pattern}': {matches[:3]}")
        
        # 전화번호 패턴
        phone_patterns = [
            r'\d{2,3}-\d{3,4}-\d{4}',
            r'0\d{1,2}-\d{3,4}-\d{4}',
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                logger.info(f"전화번호 패턴 '{pattern}': {matches[:3]}")
        
    except Exception as e:
        logger.error(f"분석 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await crawler.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_restaurant_page())
