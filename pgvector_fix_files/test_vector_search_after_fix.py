#!/usr/bin/env python3
"""
임베딩 수정 후 벡터 검색 테스트
"""
from supabase import create_client
import os
from dotenv import load_dotenv
import json
import numpy as np
from openai import OpenAI

load_dotenv()

def test_vector_search_after_fix():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print("=== 임베딩 수정 후 벡터 검색 테스트 ===")
    
    # 1. 쿼리 임베딩 생성
    query = "김밥"
    query_response = openai_client.embeddings.create(
        model='text-embedding-3-small',
        input=query
    )
    query_embedding = query_response.data[0].embedding
    
    print(f"쿼리: '{query}'")
    print(f"쿼리 임베딩 길이: {len(query_embedding)}")
    
    # 2. 모든 데이터 가져와서 클라이언트에서 유사도 계산
    print("\n=== 클라이언트 사이드 벡터 검색 ===")
    result = client.table('recipes_hybrid_ingredient_llm').select('*').execute()
    
    similarities = []
    query_vec = np.array(query_embedding, dtype=np.float32)
    
    for row in result.data:
        embedding_data = row.get('embedding')
        if not embedding_data:
            continue
        
        # embedding이 문자열인 경우 파싱
        if isinstance(embedding_data, str):
            try:
                embedding_data = json.loads(embedding_data)
            except:
                continue
        
        # 벡터로 변환
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
            'similarity': similarity,
            'similarity_percentage': similarity * 100
        })
    
    # 유사도 순으로 정렬
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    print(f"\n상위 10개 결과:")
    for i, result in enumerate(similarities[:10], 1):
        print(f"{i:2d}. {result['title'][:50]}... ({result['similarity_percentage']:.1f}%)")
    
    # 3. pgvector 함수 테스트
    print(f"\n=== pgvector 함수 테스트 ===")
    try:
        search_result = client.rpc('search_hybrid_recipes', {
            'query_embedding': query_embedding,
            'match_count': 5
        }).execute()
        
        if search_result.data:
            print("pgvector 함수 성공!")
            for i, result in enumerate(search_result.data, 1):
                print(f"{i}. {result['title'][:50]}... ({result['similarity']*100:.1f}%)")
        else:
            print("pgvector 함수 결과 없음")
            
    except Exception as e:
        print(f"pgvector 함수 오류: {e}")
    
    # 4. 임베딩 데이터 타입 상세 분석
    print(f"\n=== 임베딩 데이터 타입 상세 분석 ===")
    sample_row = result.data[0]
    embedding_data = sample_row.get('embedding')
    
    print(f"원본 타입: {type(embedding_data)}")
    print(f"원본 길이: {len(str(embedding_data))}")
    
    if isinstance(embedding_data, str):
        try:
            parsed = json.loads(embedding_data)
            print(f"파싱 후 타입: {type(parsed)}")
            print(f"파싱 후 길이: {len(parsed)}")
            print(f"파싱 후 범위: {min(parsed):.4f} ~ {max(parsed):.4f}")
            print("✅ 파싱 성공 - 실제로는 리스트로 저장됨")
        except Exception as e:
            print(f"❌ 파싱 실패: {e}")

if __name__ == "__main__":
    test_vector_search_after_fix()
