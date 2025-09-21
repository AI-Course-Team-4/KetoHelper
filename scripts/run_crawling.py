#!/usr/bin/env python3
"""
실제 크롤링 실행 스크립트
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from config.crawler_config import register_crawlers
from services.crawler.crawler_factory import crawler_factory
from services.processor.data_processor import DataProcessor
from services.processor.geocoding_service import MockGeocodingService
from services.processor.deduplication_service import DeduplicationService
from services.cache.cache_manager import CacheManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CrawlingManager:
    """크롤링 관리자"""
    
    def __init__(self):
        self.crawler = None
        self.processor = None
        self.cache_manager = None
        self.results = []
        
    async def initialize(self):
        """초기화"""
        logger.info("크롤링 시스템 초기화 중...")
        
        # 크롤러 생성
        self.crawler = crawler_factory.create('diningcode')
        
        # 데이터 처리 서비스 생성
        geocoding_service = MockGeocodingService()
        dedup_service = DeduplicationService()
        self.cache_manager = CacheManager()
        await self.cache_manager.initialize()
        
        self.processor = DataProcessor(
            geocoding_service=geocoding_service,
            deduplication_service=dedup_service
        )
        
        logger.info("초기화 완료")
    
    async def crawl_keyword(self, keyword: str, max_pages: int = 3) -> List[Dict[str, Any]]:
        """키워드로 크롤링"""
        logger.info(f"키워드 '{keyword}' 크롤링 시작 (최대 {max_pages}페이지)")
        
        all_restaurants = []
        
        for page in range(1, max_pages + 1):
            logger.info(f"페이지 {page} 크롤링 중...")
            
            try:
                # 검색 결과에서 식당 URL 목록 가져오기
                search_url = self.crawler.get_search_url(keyword, page)
                logger.info(f"검색 URL: {search_url}")
                
                # 검색 페이지 크롤링
                restaurant_urls = await self.crawler._crawl_search_page(search_url)
                
                logger.info(f"페이지 {page}에서 {len(restaurant_urls)}개 식당 URL 발견")
                
                # 각 식당 상세 정보 크롤링
                for i, url in enumerate(restaurant_urls):
                    try:
                        logger.info(f"식당 {i+1}/{len(restaurant_urls)} 크롤링: {url}")
                        
                        # 식당 상세 정보 크롤링
                        crawl_result = await self.crawler.crawl_restaurant_detail(url)
                        
                        if crawl_result.success:
                            all_restaurants.append(crawl_result.data)
                            logger.info(f"식당 크롤링 성공: {crawl_result.data.get('restaurant', {}).get('name', 'Unknown')}")
                        else:
                            logger.error(f"식당 크롤링 실패 {url}: {crawl_result.error}")
                        
                        # Rate limiting
                        await asyncio.sleep(1.0)
                        
                    except Exception as e:
                        logger.error(f"식당 크롤링 실패 {url}: {e}")
                        continue
                
                # 페이지 간 대기
                await asyncio.sleep(2.0)
                
            except Exception as e:
                logger.error(f"페이지 {page} 크롤링 실패: {e}")
                continue
        
        logger.info(f"크롤링 완료: 총 {len(all_restaurants)}개 식당")
        return all_restaurants
    
    async def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """데이터 처리"""
        logger.info("데이터 처리 시작...")
        
        try:
            processed_results = await self.processor.process_batch(raw_data)
            
            # 결과 정리
            processed_data = []
            for restaurant, menus in processed_results:
                processed_data.append({
                    'restaurant': {
                        'id': restaurant.id,
                        'name': restaurant.name,
                        'address': restaurant.address.display_address if restaurant.address else None,
                        'phone': restaurant.phone,
                        'rating': restaurant.rating,
                        'review_count': restaurant.review_count,
                        'cuisine_types': restaurant.cuisine_types,
                        'price_range': restaurant.price_range,
                        'source_url': restaurant.source_url,
                        'source_name': restaurant.source_name,
                        'has_location': restaurant.has_location
                    },
                    'menus': [
                        {
                            'id': menu.id,
                            'name': menu.name,
                            'price': menu.price,
                            'description': menu.description,
                            'keto_score': menu.keto_score.score if menu.keto_score else None
                        }
                        for menu in menus
                    ]
                })
            
            logger.info(f"데이터 처리 완료: {len(processed_data)}개 식당")
            return processed_data
            
        except Exception as e:
            logger.error(f"데이터 처리 실패: {e}")
            return []
    
    async def save_results(self, data: List[Dict[str, Any]], filename: str = None):
        """결과 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crawl_results_{timestamp}.json"
        
        file_path = settings.get_data_path("reports", filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"결과 저장 완료: {file_path}")
            
            # 통계 출력
            total_restaurants = len(data)
            total_menus = sum(len(item['menus']) for item in data)
            
            logger.info(f"크롤링 통계:")
            logger.info(f"  - 식당 수: {total_restaurants}")
            logger.info(f"  - 메뉴 수: {total_menus}")
            
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")
    
    async def cleanup(self):
        """정리"""
        if self.crawler:
            await self.crawler.cleanup()

async def main():
    """메인 함수"""
    logger.info("🚀 실제 크롤링 시작")
    
    # 크롤러 등록
    register_crawlers()
    
    # 크롤링 관리자 생성
    manager = CrawlingManager()
    
    try:
        # 초기화
        await manager.initialize()
        
        # 크롤링할 키워드들
        keywords = [
            "강남역 맛집",
            "홍대 맛집", 
            "이태원 맛집",
            "건대 맛집"
        ]
        
        all_results = []
        
        for keyword in keywords:
            logger.info(f"\n{'='*50}")
            logger.info(f"키워드: {keyword}")
            logger.info(f"{'='*50}")
            
            # 크롤링 실행
            raw_data = await manager.crawl_keyword(keyword, max_pages=2)
            
            if raw_data:
                # 데이터 처리
                processed_data = await manager.process_data(raw_data)
                all_results.extend(processed_data)
                
                # 개별 키워드 결과 저장
                await manager.save_results(processed_data, f"crawl_{keyword.replace(' ', '_')}.json")
            else:
                logger.warning(f"키워드 '{keyword}'에서 데이터를 찾을 수 없습니다")
        
        # 전체 결과 저장
        if all_results:
            await manager.save_results(all_results, "crawl_all_results.json")
            logger.info(f"\n🎉 크롤링 완료! 총 {len(all_results)}개 식당 수집")
        else:
            logger.warning("수집된 데이터가 없습니다")
    
    except Exception as e:
        logger.error(f"크롤링 실패: {e}")
        return False
    
    finally:
        await manager.cleanup()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
