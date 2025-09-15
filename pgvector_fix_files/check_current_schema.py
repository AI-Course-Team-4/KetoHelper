#!/usr/bin/env python3
"""
현재 테이블 스키마 확인
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def check_current_schema():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    
    print("=== 현재 테이블 스키마 확인 ===")
    
    # 1. 테이블 정보 확인
    try:
        result = client.table('recipes_hybrid_ingredient_llm').select('*').limit(1).execute()
        if result.data:
            sample = result.data[0]
            print(f"테이블 컬럼들:")
            for key, value in sample.items():
                print(f"  - {key}: {type(value)} (값: {str(value)[:100]}...)")
        else:
            print("데이터가 없습니다.")
    except Exception as e:
        print(f"테이블 접근 실패: {e}")
    
    # 2. embedding 컬럼 타입 확인
    print(f"\n=== embedding 컬럼 상세 분석 ===")
    try:
        result = client.table('recipes_hybrid_ingredient_llm').select('recipe_id, title, embedding').limit(3).execute()
        for i, row in enumerate(result.data, 1):
            print(f"\n{i}. {row['title']}")
            embedding = row.get('embedding')
            print(f"   - embedding 타입: {type(embedding)}")
            print(f"   - embedding 길이: {len(str(embedding))}")
            
            if isinstance(embedding, str):
                print(f"   - 문자열로 저장됨")
                try:
                    import json
                    parsed = json.loads(embedding)
                    print(f"   - JSON 파싱 성공: {type(parsed)}, 길이: {len(parsed)}")
                except Exception as e:
                    print(f"   - JSON 파싱 실패: {e}")
            else:
                print(f"   - 리스트 타입으로 저장됨")
                print(f"   - 길이: {len(embedding) if hasattr(embedding, '__len__') else 'N/A'}")
    except Exception as e:
        print(f"embedding 분석 실패: {e}")

if __name__ == "__main__":
    check_current_schema()
