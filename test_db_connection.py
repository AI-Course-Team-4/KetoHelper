#!/usr/bin/env python3
"""
실제 데이터베이스 연결 테스트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import DatabaseConnection
from src.utils.config_loader import get_config

async def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        print("🔍 데이터베이스 연결 테스트 시작...")
        
        # 설정 로드 테스트
        config = get_config()
        print("✅ 설정 로드 성공")
        print(f"   - Supabase URL: {config.get_supabase_url()}")
        print(f"   - DB Host: {config.database.host}")
        print(f"   - DB Name: {config.database.name}")
        
        # 데이터베이스 연결 초기화
        db = DatabaseConnection()
        print("✅ DatabaseConnection 인스턴스 생성")
        
        # 연결 초기화
        await db.initialize()
        print("✅ 데이터베이스 연결 초기화 성공")
        
        # 헬스 체크
        health = await db.health_check()
        print(f"✅ 헬스 체크 결과: {health}")
        
        # 통계 확인
        stats = db.get_stats()
        print(f"✅ 연결 통계: {stats}")
        
        # 간단한 쿼리 테스트
        result = await db.execute_one("SELECT 1 as test")
        print(f"✅ 테스트 쿼리 결과: {result}")
        
        # 연결 종료
        await db.close()
        print("✅ 데이터베이스 연결 종료")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_database_connection())
    
    if result:
        print("🎉 데이터베이스 연결 테스트 성공!")
    else:
        print("💥 데이터베이스 연결 테스트 실패!")
