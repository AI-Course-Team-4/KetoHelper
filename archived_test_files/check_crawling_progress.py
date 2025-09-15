#!/usr/bin/env python3
"""
크롤링 진행 상황 확인
"""

import asyncio
import sys
sys.path.append('src')

from src.supabase_client import SupabaseClient
from datetime import datetime

async def check_progress():
    """크롤링 진행 상황 확인"""
    print("=== 크롤링 진행 상황 확인 ===")
    print(f"확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        supabase_client = SupabaseClient()
        
        # 전체 레시피 수 확인
        total_count = await supabase_client.get_recipe_count()
        print(f"현재 데이터베이스 총 레시피 수: {total_count}")
        
        # 최근 크롤링된 레시피들 확인 (최근 10개)
        result = supabase_client.client.table('recipes_keto_raw').select('*').order('fetched_at', desc=True).limit(10).execute()
        
        if result.data:
            print(f"\n=== 최근 크롤링된 레시피들 (최근 10개) ===")
            for i, recipe in enumerate(result.data, 1):
                print(f"{i}. {recipe.get('title', 'N/A')[:50]}... - {recipe.get('fetched_at', 'N/A')}")
        
        # 크롤링 실행 이력 확인
        crawl_runs = supabase_client.client.table('crawl_runs').select('*').order('started_at', desc=True).limit(5).execute()
        
        if crawl_runs.data:
            print(f"\n=== 최근 크롤링 실행 이력 ===")
            for run in crawl_runs.data:
                print(f"- 시작: {run.get('started_at', 'N/A')}")
                print(f"  완료: {run.get('finished_at', '진행중')}")
                print(f"  페이지: {run.get('page_start', 'N/A')} ~ {run.get('page_end', 'N/A')}")
                print(f"  삽입: {run.get('inserted_count', 0)}, 업데이트: {run.get('updated_count', 0)}, 오류: {run.get('error_count', 0)}")
                print(f"  메모: {run.get('notes', 'N/A')}")
                print()
        
    except Exception as e:
        print(f"진행 상황 확인 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_progress())
