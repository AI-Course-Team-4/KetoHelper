#!/usr/bin/env python3
"""
전체 키토 레시피 크롤링 실행
"""

import asyncio
import sys
sys.path.append('src')

from src.crawler import KetoCrawler
import json
from datetime import datetime

async def full_crawling():
    """전체 키토 레시피 크롤링"""
    print("=== 전체 키토 레시피 크롤링 시작 ===")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 크롤러 초기화
    crawler = KetoCrawler()
    
    try:
        # 전체 크롤링 실행
        result = await crawler.run()
        
        print(f"\n=== 크롤링 완료 ===")
        print(f"완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"페이지 크롤링: {result['pages_crawled']}")
        print(f"발견된 레시피: {result['recipes_discovered']}")
        print(f"처리된 레시피: {result['recipes_processed']}")
        print(f"삽입된 레시피: {result['recipes_inserted']}")
        print(f"업데이트된 레시피: {result['recipes_updated']}")
        print(f"실패한 레시피: {result['recipes_failed']}")
        
        # 실패한 URL들 확인
        if crawler.failed_urls:
            print(f"\n=== 실패한 URL들 ({len(crawler.failed_urls)}개) ===")
            for url in crawler.failed_urls[:10]:  # 처음 10개만 출력
                print(f"- {url}")
            if len(crawler.failed_urls) > 10:
                print(f"... 그리고 {len(crawler.failed_urls) - 10}개 더")
        
        # 데이터베이스 통계 확인
        from src.supabase_client import SupabaseClient
        supabase_client = SupabaseClient()
        
        print(f"\n=== 데이터베이스 통계 ===")
        try:
            # 전체 레시피 수 확인
            total_count = await supabase_client.get_recipe_count()
            print(f"데이터베이스 총 레시피 수: {total_count}")
            
            # 필드 완성도 통계
            completeness_stats = await supabase_client.get_field_completeness_stats()
            if completeness_stats:
                print(f"\n필드 완성도:")
                for field, percentage in completeness_stats.items():
                    print(f"- {field}: {percentage:.1f}%")
            
        except Exception as e:
            print(f"데이터베이스 통계 조회 중 오류: {e}")
        
        print(f"\n=== 크롤링 성공적으로 완료! ===")
        
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # HTTP 클라이언트 정리
        crawler.http_client.close()

if __name__ == "__main__":
    asyncio.run(full_crawling())
