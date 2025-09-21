#!/usr/bin/env python3
"""
다이닝코드 HTML 구조 분석 스크립트
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

async def analyze_html_structure():
    """HTML 구조 분석"""
    logger.info("HTML 구조 분석 시작")
    
    # 크롤러 등록
    register_crawlers()
    
    # 크롤러 생성
    crawler = crawler_factory.create('diningcode')
    
    try:
        await crawler.initialize()
        
        # 검색 URL 생성
        keyword = "강남역 맛집"
        search_url = crawler.get_search_url(keyword, 1)
        logger.info(f"분석할 URL: {search_url}")
        
        # HTML 가져오기
        response = await crawler._client.get(search_url)
        html_content = response.text
        
        logger.info(f"HTML 길이: {len(html_content)} characters")
        
        # HTML 파일로 저장
        html_file = Path("data/cache/diningcode_search.html")
        html_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML 저장됨: {html_file}")
        
        # HTML 파싱
        tree = HTMLParser(html_content)
        
        # 다양한 링크 패턴 분석
        logger.info("\n=== 링크 분석 ===")
        
        # 모든 a 태그 찾기
        all_links = tree.css('a[href]')
        logger.info(f"전체 링크 수: {len(all_links)}")
        
        # profile.php가 포함된 링크 찾기
        profile_links = []
        for link in all_links:
            if link.attributes:
                href = link.attributes.get('href', '')
                if 'profile.php' in href:
                    profile_links.append(href)
        
        logger.info(f"profile.php 링크 수: {len(profile_links)}")
        if profile_links:
            logger.info("profile.php 링크 예시:")
            for i, link in enumerate(profile_links[:5]):
                logger.info(f"  {i+1}. {link}")
        
        # 다양한 선택자 테스트
        selectors_to_test = [
            'a.btxt',
            'a[href*="profile.php"]',
            '.RestaurantItem a',
            '.restaurant-item a',
            '.list-item a',
            '.item a',
            '.restaurant a',
            'a[href*="rid="]',
            '.dc-card a',
            '.card a'
        ]
        
        logger.info("\n=== 선택자 테스트 ===")
        for selector in selectors_to_test:
            elements = tree.css(selector)
            logger.info(f"{selector}: {len(elements)}개 요소")
            
            if elements:
                # 첫 번째 요소의 href 확인
                first_elem = elements[0]
                if first_elem.attributes:
                    href = first_elem.attributes.get('href', '')
                    logger.info(f"  첫 번째 href: {href}")
        
        # 텍스트에서 식당명 패턴 찾기
        logger.info("\n=== 텍스트 패턴 분석 ===")
        text_content = tree.text()
        
        # 일반적인 식당명 패턴들
        import re
        restaurant_patterns = [
            r'([가-힣\w\s]+)\s*\([가-힣]+\s*★[\d\.]+\)',  # 식당명 (음식종류 ★평점)
            r'([가-힣\w\s]{2,})\s*★[\d\.]+',              # 식당명 ★평점
        ]
        
        for pattern in restaurant_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                logger.info(f"패턴 '{pattern}' 매칭: {len(matches)}개")
                for i, match in enumerate(matches[:3]):
                    logger.info(f"  {i+1}. {match}")
        
        # HTML 구조 분석 - 주요 div 클래스들
        logger.info("\n=== 주요 구조 분석 ===")
        div_classes = []
        for div in tree.css('div[class]'):
            if div.attributes:
                class_attr = div.attributes.get('class', '')
                if class_attr and ('list' in class_attr.lower() or 'item' in class_attr.lower() or 'restaurant' in class_attr.lower()):
                    div_classes.append(class_attr)
        
        unique_classes = list(set(div_classes))
        logger.info(f"관련 div 클래스들: {len(unique_classes)}개")
        for cls in unique_classes[:10]:
            logger.info(f"  - {cls}")
        
        # 실제 식당 정보가 있는 부분 찾기
        logger.info("\n=== 식당 정보 구조 분석 ===")
        
        # 메타 데이터에서 힌트 찾기
        meta_desc = tree.css_first('meta[name="description"]')
        if meta_desc and meta_desc.attributes:
            desc_content = meta_desc.attributes.get('content', '')
            logger.info(f"메타 설명: {desc_content[:200]}...")
        
        # 제목에서 힌트 찾기
        title = tree.css_first('title')
        if title:
            logger.info(f"페이지 제목: {title.text()}")
        
    except Exception as e:
        logger.error(f"분석 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await crawler.cleanup()

if __name__ == "__main__":
    asyncio.run(analyze_html_structure())
