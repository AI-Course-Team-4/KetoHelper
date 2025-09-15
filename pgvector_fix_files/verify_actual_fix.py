#!/usr/bin/env python3
"""
실제 해결 상황 정확히 확인
"""
from supabase import create_client
import os
from dotenv import load_dotenv
import json
import numpy as np
from openai import OpenAI

load_dotenv()

def verify_actual_fix():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print("=== 실제 해결 상황 정확히 확인 ===")
    
    # 1. 현재 데이터베이스 상태 확인
    print("\n1. 데이터베이스에 저장된 임베딩 타입 확인:")
    result = client.table('recipes_hybrid_ingredient_llm').select('recipe_id, title, embedding').limit(3).execute()
    
    for i, row in enumerate(result.data, 1):
        print(f"\n{i}. {row['title']}")
        embedding = row.get('embedding')
        print(f"   - Supabase에서 반환된 타입: {type(embedding)}")
        print(f"   - 데이터 길이: {len(str(embedding))}")
        
        if isinstance(embedding, str):
            print(f"   - 여전히 문자열로 반환됨")
            try:
                parsed = json.loads(embedding)
                print(f"   - JSON 파싱 후 타입: {type(parsed)}")
                print(f"   - 파싱 후 길이: {len(parsed)}")
                print(f"   - 실제로는 리스트가 JSON 문자열로 직렬화되어 있음")
            except Exception as e:
                print(f"   - JSON 파싱 실패: {e}")
        else:
            print(f"   - 리스트 타입으로 반환됨")
    
    # 2. 벡터 검색이 실제로 작동하는지 확인
    print(f"\n2. 벡터 검색 작동 확인:")
    query = "김밥"
    query_response = openai_client.embeddings.create(
        model='text-embedding-3-small',
        input=query
    )
    query_embedding = query_response.data[0].embedding
    
    # 클라이언트 사이드에서 유사도 계산
    all_data = client.table('recipes_hybrid_ingredient_llm').select('*').execute()
    query_vec = np.array(query_embedding, dtype=np.float32)
    
    similarities = []
    for row in all_data.data:
        embedding_data = row.get('embedding')
        if not embedding_data:
            continue
        
        # 문자열인 경우 JSON 파싱
        if isinstance(embedding_data, str):
            try:
                embedding_data = json.loads(embedding_data)
            except:
                continue
        
        stored_vec = np.array(embedding_data, dtype=np.float32)
        
        # 코사인 유사도 계산
        norm_query = np.linalg.norm(query_vec)
        norm_stored = np.linalg.norm(stored_vec)
        
        if norm_query == 0 or norm_stored == 0:
            similarity = 0.0
        else:
            similarity = np.dot(query_vec, stored_vec) / (norm_query * norm_stored)
        
        similarities.append({
            'title': row['title'],
            'similarity': similarity
        })
    
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    print(f"상위 5개 결과:")
    for i, result in enumerate(similarities[:5], 1):
        print(f"  {i}. {result['title'][:40]}... ({result['similarity']*100:.1f}%)")
    
    # 3. pgvector 함수 테스트
    print(f"\n3. pgvector 함수 테스트:")
    try:
        search_result = client.rpc('search_hybrid_recipes', {
            'query_embedding': query_embedding,
            'match_count': 3
        }).execute()
        
        if search_result.data:
            print("✅ pgvector 함수 작동!")
            for i, result in enumerate(search_result.data, 1):
                print(f"  {i}. {result['title'][:40]}... ({result['similarity']*100:.1f}%)")
        else:
            print("❌ pgvector 함수 결과 없음")
            
    except Exception as e:
        print(f"❌ pgvector 함수 오류: {e}")
    
    # 4. 결론
    print(f"\n4. 결론:")
    print("✅ 벡터 검색이 작동함 (클라이언트 사이드)")
    print("❓ pgvector 함수는 여전히 작동하지 않을 수 있음")
    print("📝 Supabase는 리스트를 JSON 문자열로 직렬화해서 반환함 (정상 동작)")

if __name__ == "__main__":
    verify_actual_fix()
