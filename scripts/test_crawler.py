#!/usr/bin/env python3
"""
크롤러 테스트 스크립트
"""

import asyncio
import sys
import logging
from pathlib import Path

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

async def test_crawler_basic():
    """기본 크롤러 테스트"""
    logger.info("=== 크롤러 기본 테스트 시작 ===")

    try:
        # 크롤러 생성
        crawler = crawler_factory.create('diningcode')

        # 연결 테스트
        logger.info("연결 테스트 중...")
        connection_ok = await crawler.test_connection()
        logger.info(f"연결 테스트 결과: {'성공' if connection_ok else '실패'}")

        # 검색 URL 테스트
        search_url = crawler.get_search_url("강남역 맛집", 1)
        logger.info(f"검색 URL: {search_url}")

        # URL 패턴 테스트
        test_urls = [
            "https://www.diningcode.com/profile.php?rid=12345",
            "https://www.diningcode.com/list?keyword=test",
            "https://www.diningcode.com/profile.php?rid=abc"
        ]

        for url in test_urls:
            is_restaurant = crawler.is_restaurant_url(url)
            logger.info(f"URL: {url} -> 식당 URL: {is_restaurant}")

        return True

    except Exception as e:
        logger.error(f"크롤러 테스트 실패: {e}")
        return False

    finally:
        if 'crawler' in locals():
            await crawler.cleanup()

async def test_data_processing():
    """데이터 처리 테스트"""
    logger.info("=== 데이터 처리 테스트 시작 ===")

    try:
        # 서비스 생성
        geocoding_service = MockGeocodingService()
        dedup_service = DeduplicationService()
        cache_manager = CacheManager()
        await cache_manager.initialize()

        processor = DataProcessor(
            geocoding_service=geocoding_service,
            deduplication_service=dedup_service
        )

        # 테스트 데이터
        test_restaurant_data = {
            'name': '  강남 테스트 식당  ',
            'address': '서울시 강남구 테헤란로 123',
            'phone': '02-1234-5678',
            'rating': '4.5',
            'review_count': 100,
            'cuisine_types': ['한식', '일식'],
            'price_range': 'medium',
            'source_url': 'https://test.com/restaurant/123',
            'source_name': 'diningcode'
        }

        test_menu_data = [
            {'name': '김치찌개', 'price': '8000원', 'description': '매콤한 김치찌개'},
            {'name': '된장찌개', 'price': 7000},
            {'name': '   ', 'price': '0'},  # 잘못된 데이터
        ]

        # 식당 데이터 처리
        restaurant = await processor.process_restaurant_data(test_restaurant_data)
        logger.info(f"처리된 식당: {restaurant.name}")
        logger.info(f"주소: {restaurant.address.display_address if restaurant.address else 'None'}")
        logger.info(f"위치: {restaurant.has_location}")

        # 메뉴 데이터 처리
        menus = []
        for menu_data in test_menu_data:
            menu = await processor.process_menu_data(menu_data, restaurant.id)
            if menu:
                menus.append(menu)

        logger.info(f"처리된 메뉴 수: {len(menus)}")
        for menu in menus:
            logger.info(f"  - {menu.name}: {menu.price}원")

        return True

    except Exception as e:
        logger.error(f"데이터 처리 테스트 실패: {e}")
        return False

async def test_cache_system():
    """캐시 시스템 테스트"""
    logger.info("=== 캐시 시스템 테스트 시작 ===")

    try:
        cache_manager = CacheManager()
        await cache_manager.initialize()

        # 크롤링 데이터 캐시 테스트
        test_data = [
            {'restaurant': {'name': '테스트 식당 1'}, 'menus': []},
            {'restaurant': {'name': '테스트 식당 2'}, 'menus': []}
        ]

        await cache_manager.store_crawl_data('diningcode', test_data)
        cached_data = await cache_manager.get_recent_crawl_data('diningcode', 1)

        logger.info(f"캐시 저장/조회 테스트: {'성공' if cached_data else '실패'}")

        # 지오코딩 캐시 테스트
        test_address = "서울시 강남구 테헤란로 123"
        test_geocode_result = {
            'lat': 37.4979,
            'lng': 127.0276,
            'formatted_address': '서울 강남구 테헤란로 123'
        }

        await cache_manager.store_geocoding_result(test_address, test_geocode_result)
        cached_geocode = await cache_manager.get_geocoding_result(test_address)

        logger.info(f"지오코딩 캐시 테스트: {'성공' if cached_geocode else '실패'}")

        # 캐시 통계
        stats = await cache_manager.get_cache_statistics()
        logger.info(f"캐시 통계: {stats}")

        return True

    except Exception as e:
        logger.error(f"캐시 시스템 테스트 실패: {e}")
        return False

async def test_full_pipeline():
    """전체 파이프라인 테스트"""
    logger.info("=== 전체 파이프라인 테스트 시작 ===")

    try:
        # 크롤러 생성
        crawler = crawler_factory.create('diningcode')

        # 데이터 처리 서비스 생성
        geocoding_service = MockGeocodingService()
        dedup_service = DeduplicationService()
        cache_manager = CacheManager()
        await cache_manager.initialize()

        processor = DataProcessor(
            geocoding_service=geocoding_service,
            deduplication_service=dedup_service
        )

        # 캐시 확인
        cached_data = await cache_manager.get_recent_crawl_data('diningcode', 24)
        if cached_data:
            logger.info("캐시된 데이터 사용")
            crawl_results = cached_data
        else:
            logger.info("새로운 크롤링 필요 (시뮬레이션)")
            # 실제로는 crawler.crawl_restaurant_list() 호출
            crawl_results = [
                {
                    'restaurant': {
                        'name': '강남 맛집',
                        'address': '서울시 강남구 테헤란로 123',
                        'phone': '02-1234-5678',
                        'source_url': 'https://test.com/123',
                        'source_name': 'diningcode'
                    },
                    'menus': [
                        {'name': '김치찌개', 'price': 8000},
                        {'name': '된장찌개', 'price': 7000}
                    ]
                }
            ]
            await cache_manager.store_crawl_data('diningcode', crawl_results)

        # 데이터 처리
        processed_results = await processor.process_batch(crawl_results)

        logger.info(f"파이프라인 완료: {len(processed_results)}개 식당 처리")

        for restaurant, menus in processed_results:
            logger.info(f"  - {restaurant.name}: {len(menus)}개 메뉴")

        return True

    except Exception as e:
        logger.error(f"전체 파이프라인 테스트 실패: {e}")
        return False

    finally:
        if 'crawler' in locals():
            await crawler.cleanup()

async def main():
    """메인 함수"""
    logger.info("🚀 크롤링 시스템 테스트 시작")

    # 크롤러 등록 확인
    register_crawlers()
    available_sources = crawler_factory.list_sources()
    logger.info(f"사용 가능한 크롤러: {available_sources}")

    # 테스트 실행
    tests = [
        ("크롤러 기본 기능", test_crawler_basic),
        ("데이터 처리", test_data_processing),
        ("캐시 시스템", test_cache_system),
        ("전체 파이프라인", test_full_pipeline)
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"테스트: {test_name}")
        logger.info(f"{'='*50}")

        try:
            result = await test_func()
            results.append((test_name, result))
            logger.info(f"✅ {test_name}: {'성공' if result else '실패'}")
        except Exception as e:
            logger.error(f"❌ {test_name}: 예외 발생 - {e}")
            results.append((test_name, False))

    # 결과 요약
    logger.info(f"\n{'='*50}")
    logger.info("테스트 결과 요약")
    logger.info(f"{'='*50}")

    success_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\n전체 결과: {success_count}/{total_count} 성공")

    return success_count == total_count

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)