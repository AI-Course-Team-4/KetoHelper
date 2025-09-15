#!/usr/bin/env python3
"""
테이블 데이터 확인 테스트
"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

def test_table_data():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    
    # 테이블 데이터 확인
    result = client.table('recipes_hybrid_ingredient_llm').select('*').limit(3).execute()
    print(f'테이블 데이터: {len(result.data)}개')
    
    for i, r in enumerate(result.data[:3], 1):
        print(f'{i}. {r["title"]}')
        print(f'   - structured_blob 길이: {len(r.get("structured_blob", ""))}')
        print(f'   - embedding 존재: {"embedding" in r}')
    
    # 벡터 검색 함수 테스트
    print("\n벡터 검색 함수 테스트:")
    try:
        # 더미 임베딩으로 테스트
        dummy_embedding = [0.1] * 1536
        search_result = client.rpc('search_hybrid_recipes', {
            'query_embedding': dummy_embedding,
            'match_count': 3
        }).execute()
        print(f"벡터 검색 결과: {len(search_result.data)}개")
    except Exception as e:
        print(f"벡터 검색 오류: {e}")

if __name__ == "__main__":
    test_table_data()
