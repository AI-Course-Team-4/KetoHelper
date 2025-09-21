#!/usr/bin/env python3
"""
중복 제거 로직 빠른 테스트
"""

import asyncio
import sys
import logging
from pathlib import Path

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

async def quick_test():
    """빠른 중복 제거 테스트"""
    logger.info("빠른 중복 제거 테스트 시작")
    
    # 크롤러 등록
    register_crawlers()
    
    # 크롤러 생성
    crawler = crawler_factory.create('diningcode')
    
    try:
        await crawler.initialize()
        
        keyword = "강남역 맛집"
        crawled_urls = set()
        
        # 페이지 1과 2를 연속으로 테스트
        for page in [1, 2]:
            logger.info(f"\n페이지 {page} 테스트")
            
            search_url = crawler.get_search_url(keyword, page)
            response = await crawler._client.get(search_url)
            html_content = response.text
            
            restaurant_urls = crawler._extract_restaurant_urls_from_search(html_content)
            logger.info(f"페이지 {page}: 총 {len(restaurant_urls)}개 URL 발견")
            
            new_urls = [url for url in restaurant_urls if url not in crawled_urls]
            logger.info(f"페이지 {page}: 새로운 URL {len(new_urls)}개")
            logger.info(f"페이지 {page}: 중복 URL {len(restaurant_urls) - len(new_urls)}개")
            
            # URL을 추적 세트에 추가
            crawled_urls.update(restaurant_urls)
            
            # 첫 3개 URL만 출력
            if new_urls:
                logger.info(f"새로운 URL 예시:")
                for i, url in enumerate(new_urls[:3]):
                    logger.info(f"  {i+1}. {url}")
            
            await asyncio.sleep(1.0)
        
        logger.info(f"\n총 처리된 고유 URL: {len(crawled_urls)}개")
        
    except Exception as e:
        logger.error(f"테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await crawler.cleanup()

if __name__ == "__main__":
    asyncio.run(quick_test())
