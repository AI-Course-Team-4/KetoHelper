#!/usr/bin/env python3
"""
벡터 유사도 낮은 원인 분석
"""
from supabase import create_client
import os
from dotenv import load_dotenv
import numpy as np
from openai import OpenAI

load_dotenv()

def analyze_vector_similarity():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # 1. 테이블 데이터 확인
    print("=== 1. 테이블 데이터 분석 ===")
    result = client.table('recipes_hybrid_ingredient_llm').select('*').limit(5).execute()
    
    for i, row in enumerate(result.data, 1):
        print(f"\n{i}. {row['title']}")
        print(f"   - structured_blob: {row.get('structured_blob', '')}")
        print(f"   - embedding 타입: {type(row.get('embedding'))}")
        print(f"   - embedding 길이: {len(row.get('embedding', []))}")
        
        # embedding 값 확인
        embedding = row.get('embedding')
        if embedding:
            if isinstance(embedding, list):
                print(f"   - embedding 범위: {min(embedding):.4f} ~ {max(embedding):.4f}")
                print(f"   - embedding 평균: {np.mean(embedding):.4f}")
                print(f"   - embedding 표준편차: {np.std(embedding):.4f}")
    
    # 2. 쿼리 임베딩 생성 및 분석
    print("\n=== 2. 쿼리 임베딩 분석 ===")
    query = "김밥"
    query_response = openai_client.embeddings.create(
        model='text-embedding-3-small',
        input=query
    )
    query_embedding = query_response.data[0].embedding
    
    print(f"쿼리: '{query}'")
    print(f"쿼리 임베딩 길이: {len(query_embedding)}")
    print(f"쿼리 임베딩 범위: {min(query_embedding):.4f} ~ {max(query_embedding):.4f}")
    print(f"쿼리 임베딩 평균: {np.mean(query_embedding):.4f}")
    print(f"쿼리 임베딩 표준편차: {np.std(query_embedding):.4f}")
    
    # 3. 유사도 계산 분석
    print("\n=== 3. 유사도 계산 분석 ===")
    query_vec = np.array(query_embedding, dtype=np.float32)
    
    for i, row in enumerate(result.data, 1):
        title = row['title']
        stored_embedding = row.get('embedding')
        
        if stored_embedding:
            stored_vec = np.array(stored_embedding, dtype=np.float32)
            
            # 코사인 유사도 계산
            norm_query = np.linalg.norm(query_vec)
            norm_stored = np.linalg.norm(stored_vec)
            
            if norm_query == 0 or norm_stored == 0:
                similarity = 0.0
            else:
                similarity = np.dot(query_vec, stored_vec) / (norm_query * norm_stored)
            
            print(f"\n{i}. {title}")
            print(f"   - 코사인 유사도: {similarity:.4f}")
            print(f"   - 정규화된 점수: {similarity * 100:.1f}%")
            
            # 벡터 크기 분석
            print(f"   - 쿼리 벡터 크기: {norm_query:.4f}")
            print(f"   - 저장된 벡터 크기: {norm_stored:.4f}")
            
            # 내적 분석
            dot_product = np.dot(query_vec, stored_vec)
            print(f"   - 내적: {dot_product:.4f}")
    
    # 4. structured_blob 내용 분석
    print("\n=== 4. structured_blob 내용 분석 ===")
    for i, row in enumerate(result.data, 1):
        blob = row.get('structured_blob', '')
        print(f"\n{i}. {row['title']}")
        print(f"   - blob 내용: '{blob}'")
        print(f"   - blob 길이: {len(blob)}")
        
        # blob이 어떻게 생성되었는지 확인
        llm_metadata = row.get('llm_metadata', {})
        basic_metadata = row.get('basic_metadata', {})
        print(f"   - LLM 메타데이터: {llm_metadata}")
        print(f"   - 기본 메타데이터: {basic_metadata}")

if __name__ == "__main__":
    analyze_vector_similarity()
