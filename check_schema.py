#!/usr/bin/env python3
"""
실제 Supabase 테이블 스키마 확인 스크립트
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def check_table_schema():
    """실제 테이블 스키마 확인"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        from src.database import DatabaseManager
        
        print("🔍 실제 테이블 스키마 확인 중...")
        db = DatabaseManager()
        
        # 테이블의 모든 데이터 조회 (구조 확인용)
        result = db.client.table('menus').select('*').limit(1).execute()
        
        if result.data:
            print("✅ 테이블 데이터 조회 성공!")
            print("📊 실제 테이블 컬럼:")
            print("=" * 50)
            
            sample_row = result.data[0]
            for key, value in sample_row.items():
                value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"  {key}: {value_preview}")
            
            print("\n📝 예상 스키마와 비교:")
            expected_columns = [
                'id', 'restaurant_name', 'address', 'menu_name', 
                'price', 'menu_text', 'embedding', 'source', 
                'category', 'rating', 'image_url', 'metadata', 
                'created_at', 'updated_at'
            ]
            
            actual_columns = list(sample_row.keys())
            
            print("\n✅ 존재하는 컬럼:")
            for col in expected_columns:
                if col in actual_columns:
                    print(f"  ✓ {col}")
                else:
                    print(f"  ✗ {col} (누락)")
            
            print("\n🆕 추가 컬럼:")
            for col in actual_columns:
                if col not in expected_columns:
                    print(f"  + {col}")
                    
        else:
            print("❌ 테이블에 데이터가 없습니다.")
            
    except Exception as e:
        print(f"❌ 스키마 확인 중 오류: {e}")

def main():
    """메인 함수"""
    print("🔧 Supabase 테이블 스키마 확인 도구")
    print("=" * 50)
    check_table_schema()

if __name__ == "__main__":
    main()
