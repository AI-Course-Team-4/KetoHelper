#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON 문자열로 저장된 임베딩을 파싱해서 벡터 검색 테스트
"""

import os
import json
import numpy as np
from typing import List
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

# 환경설정
load_dotenv('../.env')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def get_query_embedding(query: str) -> List[float]:
    """쿼리 임베딩 생성"""
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return response.data[0].embedding

def parse_embedding_string(embedding_str: str) -> List[float]:
    """JSON 문자열로 저장된 임베딩을 파싱"""
    try:
        if isinstance(embedding_str, str):
            return json.loads(embedding_str)
        return embedding_str
    except:
        return []

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """코사인 유사도 계산"""
    if not a or not b or len(a) != len(b):
        return 0.0
    
    a_np = np.array(a)
    b_np = np.array(b)
    
    dot_product = np.dot(a_np, b_np)
    norm_a = np.linalg.norm(a_np)
    norm_b = np.linalg.norm(b_np)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)

def test_vector_search_with_parsing():
    """JSON 파싱을 사용한 벡터 검색 테스트"""
    print("=== JSON 파싱을 사용한 벡터 검색 테스트 ===")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 테스트 쿼리
    query = "김밥"
    print(f"\n🧠 벡터 검색: '{query}'")
    
    try:
        # 쿼리 임베딩 생성
        query_embedding = get_query_embedding(query)
        print(f"쿼리 임베딩 차원: {len(query_embedding)}")
        
        # 모든 레시피 가져오기
        result = client.table("recipes_keto_enhanced").select("id, title, blob, embedding").execute()
        
        if not result.data:
            print("❌ 데이터가 없습니다.")
            return
        
        # 각 레시피와 유사도 계산
        similarities = []
        for recipe in result.data:
            embedding_str = recipe.get('embedding', '')
            parsed_embedding = parse_embedding_string(embedding_str)
            
            if parsed_embedding and len(parsed_embedding) == len(query_embedding):
                similarity = cosine_similarity(query_embedding, parsed_embedding)
                similarities.append({
                    'id': recipe.get('id'),
                    'title': recipe.get('title', ''),
                    'blob': recipe.get('blob', ''),
                    'similarity': similarity
                })
        
        # 유사도 순으로 정렬
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        print(f"✅ 결과 {len(similarities)}개:")
        for i, item in enumerate(similarities[:5], 1):
            score = item['similarity'] * 100
            print(f"  {i}. {item['title'][:40]}... (유사도: {score:.1f}%)")
            
    except Exception as e:
        print(f"❌ 벡터 검색 오류: {e}")

if __name__ == "__main__":
    test_vector_search_with_parsing()
