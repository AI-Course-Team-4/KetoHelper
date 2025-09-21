#!/usr/bin/env python3
"""
강남 키워드로 10개 식당만 크롤링
"""

import asyncio
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

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

async def crawl_gangnam_10_restaurants():
    """강남 키워드로 10개 식당 크롤링"""
    logger.info("🚀 강남 키워드 10개 식당 크롤링 시작")
    
    # 크롤러 등록
    register_crawlers()
    
    # 크롤러 생성
    crawler = crawler_factory.create('diningcode')
    
    try:
        await crawler.initialize()
        
        keyword = "강남역 맛집"
        target_count = 10
        results = []
        
        logger.info(f"키워드: '{keyword}' - 목표: {target_count}개 식당")
        
        # 검색 URL 생성 (첫 번째 페이지만)
        search_url = crawler.get_search_url(keyword, 1)
        
        # HTML 가져오기
        response = await crawler._client.get(search_url)
        html_content = response.text
        
        # 식당 URL 추출
        restaurant_urls = crawler._extract_restaurant_urls_from_search(html_content)
        logger.info(f"총 {len(restaurant_urls)}개 식당 URL 발견")
        
        # 10개만 선택
        selected_urls = restaurant_urls[:target_count]
        logger.info(f"선택된 {len(selected_urls)}개 식당 크롤링 시작")
        
        # 각 식당 크롤링
        for i, url in enumerate(selected_urls, 1):
            try:
                logger.info(f"[{i}/{len(selected_urls)}] 크롤링 중...")
                
                crawl_result = await crawler.crawl_restaurant_detail(url)
                
                if crawl_result.success:
                    restaurant_data = crawl_result.data
                    restaurant_name = restaurant_data.get('restaurant', {}).get('name', 'Unknown')
                    menu_count = len(restaurant_data.get('menus', []))
                    
                    logger.info(f"✅ [{i}] {restaurant_name}: {menu_count}개 메뉴")
                    results.append(restaurant_data)
                else:
                    logger.error(f"❌ [{i}] 크롤링 실패: {crawl_result.error}")
                
                # Rate limiting
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"❌ [{i}] 크롤링 중 오류: {e}")
                continue
        
        # 결과 저장
        if results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gangnam_10_restaurants_{timestamp}.json"
            file_path = Path(f"data/reports/{filename}")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 통계 출력
            total_menus = sum(len(result.get('menus', [])) for result in results)
            
            logger.info(f"\n🎉 크롤링 완료!")
            logger.info(f"📊 결과 통계:")
            logger.info(f"  - 수집된 식당: {len(results)}개")
            logger.info(f"  - 수집된 메뉴: {total_menus}개")
            logger.info(f"  - 저장 파일: {file_path}")
            
            # 식당 목록 출력
            logger.info(f"\n📋 수집된 식당 목록:")
            for i, result in enumerate(results, 1):
                restaurant_name = result.get('restaurant', {}).get('name', 'Unknown')
                menu_count = len(result.get('menus', []))
                logger.info(f"  {i}. {restaurant_name} ({menu_count}개 메뉴)")
            
        else:
            logger.warning("❌ 수집된 데이터가 없습니다")
    
    except Exception as e:
        logger.error(f"크롤링 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await crawler.cleanup()

if __name__ == "__main__":
    asyncio.run(crawl_gangnam_10_restaurants())
