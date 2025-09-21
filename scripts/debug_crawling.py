#!/usr/bin/env python3
"""
크롤링 디버깅 스크립트
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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_crawling():
    """크롤링 디버깅"""
    logger.info("크롤링 디버깅 시작")
    
    # 크롤러 등록
    register_crawlers()
    
    # 크롤러 생성
    crawler = crawler_factory.create('diningcode')
    
    try:
        # 연결 테스트
        logger.info("연결 테스트 중...")
        connection_ok = await crawler.test_connection()
        logger.info(f"연결 테스트 결과: {'성공' if connection_ok else '실패'}")
        
        if not connection_ok:
            logger.error("연결 실패로 종료")
            return
        
        # 검색 URL 생성
        keyword = "강남역 맛집"
        search_url = crawler.get_search_url(keyword, 1)
        logger.info(f"검색 URL: {search_url}")
        
        # 검색 페이지 크롤링
        logger.info("검색 페이지 크롤링 중...")
        restaurant_urls = await crawler._crawl_search_page(search_url)
        logger.info(f"발견된 식당 URL 수: {len(restaurant_urls)}")
        
        if restaurant_urls:
            logger.info("발견된 URL들:")
            for i, url in enumerate(restaurant_urls[:5]):  # 처음 5개만 출력
                logger.info(f"  {i+1}. {url}")
            
            # 첫 번째 식당 상세 정보 크롤링
            if restaurant_urls:
                first_url = restaurant_urls[0]
                logger.info(f"첫 번째 식당 크롤링: {first_url}")
                
                crawl_result = await crawler.crawl_restaurant_detail(first_url)
                if crawl_result.success:
                    logger.info("식당 크롤링 성공!")
                    logger.info(f"식당명: {crawl_result.data.get('restaurant', {}).get('name', 'Unknown')}")
                    logger.info(f"메뉴 수: {len(crawl_result.data.get('menus', []))}")
                else:
                    logger.error(f"식당 크롤링 실패: {crawl_result.error}")
        else:
            logger.warning("식당 URL을 찾을 수 없습니다")
            
            # HTML 내용 확인을 위해 직접 요청
            logger.info("HTML 내용 확인 중...")
            await crawler.initialize()
            response = await crawler._client.get(search_url)
            logger.info(f"응답 상태: {response.status_code}")
            logger.info(f"응답 헤더: {dict(response.headers)}")
            
            # HTML 일부 출력
            html_preview = response.text[:1000]
            logger.info(f"HTML 미리보기:\n{html_preview}")
    
    except Exception as e:
        logger.error(f"디버깅 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await crawler.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_crawling())
