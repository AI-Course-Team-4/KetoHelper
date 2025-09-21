#!/usr/bin/env python3
"""
간단한 크롤링 테스트 스크립트
"""

import asyncio
import sys
import logging
import json
from pathlib import Path
from datetime import datetime

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

async def simple_crawling_test():
    """간단한 크롤링 테스트"""
    logger.info("간단한 크롤링 테스트 시작")
    
    # 크롤러 등록
    register_crawlers()
    
    # 크롤러 생성
    crawler = crawler_factory.create('diningcode')
    
    try:
        await crawler.initialize()
        
        # 검색 URL 생성
        keyword = "강남역 맛집"
        search_url = crawler.get_search_url(keyword, 1)
        logger.info(f"검색 URL: {search_url}")
        
        # 직접 HTTP 요청으로 HTML 가져오기
        response = await crawler._client.get(search_url)
        html_content = response.text
        
        logger.info(f"HTML 길이: {len(html_content)}")
        
        # 우리가 수정한 메서드 직접 호출
        restaurant_urls = crawler._extract_restaurant_urls_from_search(html_content)
        logger.info(f"추출된 식당 URL 수: {len(restaurant_urls)}")
        
        if restaurant_urls:
            logger.info("추출된 URL들:")
            for i, url in enumerate(restaurant_urls[:5]):
                logger.info(f"  {i+1}. {url}")
            
            # 첫 번째 식당 상세 정보 크롤링
            first_url = restaurant_urls[0]
            logger.info(f"\n첫 번째 식당 크롤링: {first_url}")
            
            crawl_result = await crawler.crawl_restaurant_detail(first_url)
            if crawl_result.success:
                logger.info("✅ 식당 크롤링 성공!")
                restaurant_data = crawl_result.data
                logger.info(f"식당명: {restaurant_data.get('restaurant', {}).get('name', 'Unknown')}")
                logger.info(f"주소: {restaurant_data.get('restaurant', {}).get('address', 'Unknown')}")
                logger.info(f"전화번호: {restaurant_data.get('restaurant', {}).get('phone', 'Unknown')}")
                logger.info(f"메뉴 수: {len(restaurant_data.get('menus', []))}")
                
                # 메뉴 정보 출력
                menus = restaurant_data.get('menus', [])
                if menus:
                    logger.info("메뉴 목록:")
                    for i, menu in enumerate(menus[:5]):
                        logger.info(f"  {i+1}. {menu.get('name', 'Unknown')}: {menu.get('price', 'Unknown')}원")
                
                # 결과 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result_file = Path(f"data/reports/simple_test_{timestamp}.json")
                result_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(restaurant_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"결과 저장됨: {result_file}")
                
            else:
                logger.error(f"❌ 식당 크롤링 실패: {crawl_result.error}")
        
        else:
            logger.warning("식당 URL을 찾을 수 없습니다")
    
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await crawler.cleanup()

if __name__ == "__main__":
    asyncio.run(simple_crawling_test())
