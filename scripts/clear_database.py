#!/usr/bin/env python3
"""
데이터베이스 데이터 초기화 스크립트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.database.supabase_connection import SupabaseConnection
from config.settings import settings

async def clear_database():
    """데이터베이스의 모든 데이터 삭제"""
    print("🗑️  데이터베이스 데이터 초기화")
    print("=" * 50)
    
    if not settings.supabase.is_configured:
        print("❌ Supabase 설정이 완료되지 않았습니다.")
        return False
    
    try:
        # Supabase 연결
        supabase_conn = SupabaseConnection()
        await supabase_conn.initialize()
        
        print("🔗 Supabase 연결 성공")
        
        # 삭제 순서 (외래키 제약조건 고려)
        tables_to_clear = [
            'keto_scores',           # 메뉴에 의존
            'menu_ingredients',      # 메뉴에 의존
            'menus',                 # 식당에 의존
            'restaurant_sources',    # 식당에 의존
            'restaurants',           # 기본 테이블
            'geocoding_cache',       # 독립적
            'crawl_jobs'            # 독립적
        ]
        
        print("\n📊 삭제 전 데이터 확인:")
        for table in tables_to_clear:
            count = await supabase_conn.get_table_count(table)
            print(f"   {table}: {count}개")
        
        print(f"\n⚠️  위의 모든 데이터를 삭제하시겠습니까? (y/N): ", end="")
        confirm = input().strip().lower()
        
        if confirm != 'y':
            print("❌ 취소되었습니다.")
            return False
        
        print("\n🗑️  데이터 삭제 중...")
        
        # 각 테이블의 데이터 삭제
        for table in tables_to_clear:
            print(f"   {table} 삭제 중...", end=" ")
            try:
                await supabase_conn.clear_table(table)
                print("✅")
            except Exception as e:
                print(f"❌ ({e})")
        
        print("\n📊 삭제 후 데이터 확인:")
        for table in tables_to_clear:
            count = await supabase_conn.get_table_count(table)
            print(f"   {table}: {count}개")
        
        await supabase_conn.close()
        print("\n✅ 데이터베이스 초기화 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(clear_database())
    sys.exit(0 if success else 1)
