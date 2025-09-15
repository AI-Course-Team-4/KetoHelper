#!/usr/bin/env python3
"""
임베딩 데이터 타입 최종 확인
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def check_embedding_type_final():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    
    print("=== 임베딩 데이터 타입 최종 확인 ===")
    
    # 1. Supabase에서 반환되는 타입 확인
    result = client.table('recipes_hybrid_ingredient_llm').select('recipe_id, title, embedding').limit(3).execute()
    
    for i, row in enumerate(result.data, 1):
        print(f"\n{i}. {row['title']}")
        embedding = row.get('embedding')
        print(f"   - Supabase에서 반환된 타입: {type(embedding)}")
        print(f"   - 데이터 길이: {len(str(embedding))}")
        
        if isinstance(embedding, str):
            print(f"   - ❌ 여전히 문자열로 반환됨")
            print(f"   - 이는 Supabase 클라이언트가 vector 타입을 JSON 문자열로 직렬화해서 반환하기 때문")
            print(f"   - 실제 데이터베이스에서는 vector 타입으로 저장되어 있을 수 있음")
        else:
            print(f"   - ✅ 리스트 타입으로 반환됨")
    
    # 2. 실제 데이터베이스 스키마 확인 (SQL로)
    print(f"\n=== 데이터베이스 스키마 확인 ===")
    print("실제 데이터베이스에서 embedding 컬럼의 타입을 확인하려면:")
    print("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'recipes_hybrid_ingredient_llm' AND column_name = 'embedding';")
    
    # 3. 결론
    print(f"\n=== 결론 ===")
    print("❓ 임베딩 데이터 타입 문제 해결 여부:")
    print("   - Supabase 클라이언트는 vector 타입을 JSON 문자열로 직렬화해서 반환")
    print("   - 실제 데이터베이스 스키마가 vector(1536)인지 확인 필요")
    print("   - pgvector 함수가 작동한다면 vector 타입으로 저장된 것")
    print("   - 하지만 클라이언트에서는 여전히 문자열로 받아옴")

if __name__ == "__main__":
    check_embedding_type_final()
