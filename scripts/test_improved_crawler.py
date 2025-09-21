#!/usr/bin/env python3
"""
개선된 크롤러 테스트
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

async def test_improved_crawler():
    """개선된 크롤러 테스트"""
    logger.info("개선된 크롤러 테스트 시작")
    
    # 크롤러 등록
    register_crawlers()
    
    # 크롤러 생성
    crawler = crawler_factory.create('diningcode')
    
    try:
        await crawler.initialize()
        
        # 테스트할 식당 URL
        test_url = "https://www.diningcode.com/profile.php?rid=FJfopWlhuzJj"
        logger.info(f"테스트 URL: {test_url}")
        
        # 식당 상세 정보 크롤링
        crawl_result = await crawler.crawl_restaurant_detail(test_url)
        
        if crawl_result.success:
            restaurant_data = crawl_result.data
            
            logger.info("✅ 크롤링 성공!")
            logger.info("\n=== 수집된 식당 정보 ===")
            
            restaurant_info = restaurant_data.get('restaurant', {})
            for key, value in restaurant_info.items():
                logger.info(f"{key}: {value}")
            
            menus = restaurant_data.get('menus', [])
            logger.info(f"\n메뉴 수: {len(menus)}개")
            
            if menus:
                logger.info("메뉴 예시 (처음 3개):")
                for i, menu in enumerate(menus[:3], 1):
                    logger.info(f"  {i}. {menu.get('name', 'Unknown')}: {menu.get('price', 'Unknown')}원")
                    if menu.get('description'):
                        logger.info(f"     설명: {menu.get('description')}")
            
            # 결과 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"improved_crawler_test_{timestamp}.json"
            file_path = Path(f"data/reports/{filename}")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(restaurant_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"\n결과 저장됨: {file_path}")
            
        else:
            logger.error(f"❌ 크롤링 실패: {crawl_result.error}")
    
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await crawler.cleanup()

if __name__ == "__main__":
    asyncio.run(test_improved_crawler())
