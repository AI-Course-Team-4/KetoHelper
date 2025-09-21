#!/usr/bin/env python3
"""
최종 크롤링 실행 스크립트 - 여러 키워드로 대량 수집
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

async def crawl_keyword_restaurants(crawler, keyword: str, max_pages: int = 2) -> List[Dict[str, Any]]:
    """키워드별 식당 크롤링 - 중복 제거 포함"""
    logger.info(f"키워드 '{keyword}' 크롤링 시작")
    
    all_results = []
    crawled_urls = set()  # 이미 크롤링한 URL 추적
    
    for page in range(1, max_pages + 1):
        try:
            logger.info(f"페이지 {page} 크롤링 중...")
            
            # 검색 URL 생성
            search_url = crawler.get_search_url(keyword, page)
            
            # HTML 가져오기
            response = await crawler._client.get(search_url)
            html_content = response.text
            
            # 식당 URL 추출
            restaurant_urls = crawler._extract_restaurant_urls_from_search(html_content)
            logger.info(f"페이지 {page}에서 {len(restaurant_urls)}개 식당 URL 발견")
            
            if not restaurant_urls:
                logger.info(f"페이지 {page}에서 더 이상 식당을 찾을 수 없습니다")
                break
            
            # 새로운 URL만 필터링
            new_urls = [url for url in restaurant_urls if url not in crawled_urls]
            logger.info(f"페이지 {page}에서 새로운 식당 {len(new_urls)}개 (중복 제거됨: {len(restaurant_urls) - len(new_urls)}개)")
            
            if not new_urls:
                logger.info(f"페이지 {page}에서 새로운 식당이 없습니다. 크롤링 중단")
                break
            
            # 새로운 식당들만 크롤링
            for i, url in enumerate(new_urls):
                try:
                    logger.info(f"신규 식당 {i+1}/{len(new_urls)} 크롤링: {url}")
                    
                    crawl_result = await crawler.crawl_restaurant_detail(url)
                    
                    if crawl_result.success:
                        restaurant_data = crawl_result.data
                        restaurant_name = restaurant_data.get('restaurant', {}).get('name', 'Unknown')
                        menu_count = len(restaurant_data.get('menus', []))
                        
                        logger.info(f"✅ {restaurant_name}: {menu_count}개 메뉴")
                        all_results.append(restaurant_data)
                        crawled_urls.add(url)  # 크롤링 완료된 URL 기록
                    else:
                        logger.error(f"❌ 식당 크롤링 실패: {crawl_result.error}")
                        crawled_urls.add(url)  # 실패한 URL도 기록해서 재시도 방지
                    
                    # Rate limiting
                    await asyncio.sleep(1.0)
                    
                except Exception as e:
                    logger.error(f"식당 크롤링 중 오류 {url}: {e}")
                    crawled_urls.add(url)  # 오류 URL도 기록
                    continue
            
            # 페이지 간 대기
            await asyncio.sleep(2.0)
            
        except Exception as e:
            logger.error(f"페이지 {page} 크롤링 실패: {e}")
            continue
    
    logger.info(f"키워드 '{keyword}' 크롤링 완료: {len(all_results)}개 식당 (총 {len(crawled_urls)}개 URL 처리)")
    return all_results

async def main():
    """메인 크롤링 함수"""
    logger.info("🚀 최종 크롤링 시작")
    
    # 크롤러 등록
    register_crawlers()
    
    # 크롤러 생성
    crawler = crawler_factory.create('diningcode')
    
    try:
        await crawler.initialize()
        
        # 크롤링할 키워드들
        keywords = [
            "강남역 맛집",
            "홍대 맛집", 
            "이태원 맛집",
            "건대 맛집",
            "명동 맛집"
        ]
        
        all_results = []
        keyword_results = {}
        global_crawled_urls = set()  # 전체 키워드에서 이미 크롤링한 URL 추적
        
        for keyword in keywords:
            logger.info(f"\n{'='*60}")
            logger.info(f"키워드: {keyword}")
            logger.info(f"{'='*60}")
            
            try:
                # 키워드별 크롤링 실행
                results = await crawl_keyword_restaurants(crawler, keyword, max_pages=2)
                
                if results:
                    all_results.extend(results)
                    keyword_results[keyword] = results
                    
                    logger.info(f"✅ '{keyword}': {len(results)}개 식당 수집 완료")
                else:
                    logger.warning(f"⚠️ '{keyword}': 데이터 없음")
                
            except Exception as e:
                logger.error(f"❌ '{keyword}' 크롤링 실패: {e}")
                continue
        
        # 결과 저장
        if all_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 전체 결과 저장
            all_results_file = Path(f"data/reports/crawl_all_results_{timestamp}.json")
            all_results_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(all_results_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"전체 결과 저장: {all_results_file}")
            
            # 키워드별 결과 저장
            for keyword, results in keyword_results.items():
                if results:
                    keyword_safe = keyword.replace(' ', '_').replace('/', '_')
                    keyword_file = Path(f"data/reports/crawl_{keyword_safe}_{timestamp}.json")
                    
                    with open(keyword_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"키워드 '{keyword}' 결과 저장: {keyword_file}")
            
            # 통계 출력
            logger.info(f"\n🎉 크롤링 완료!")
            logger.info(f"📊 수집 통계:")
            logger.info(f"  - 전체 식당 수: {len(all_results)}")
            
            total_menus = sum(len(result.get('menus', [])) for result in all_results)
            logger.info(f"  - 전체 메뉴 수: {total_menus}")
            
            for keyword, results in keyword_results.items():
                if results:
                    menu_count = sum(len(result.get('menus', [])) for result in results)
                    logger.info(f"  - {keyword}: {len(results)}개 식당, {menu_count}개 메뉴")
            
        else:
            logger.warning("❌ 수집된 데이터가 없습니다")
    
    except Exception as e:
        logger.error(f"크롤링 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await crawler.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
