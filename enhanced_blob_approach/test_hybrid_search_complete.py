#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
완전한 하이브리드 검색 테스트 (키워드 + 벡터)
"""

import os
import json
import numpy as np
from typing import List, Dict, Any
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

def test_keyword_search(client, query: str, limit: int = 10) -> List[Dict]:
    """키워드 검색"""
    try:
        result = client.table("recipes_keto_enhanced").select("*").text_search("blob", query).execute()
        if result.data:
            return [{'id': item['id'], 'title': item['title'], 'blob': item['blob'], 'type': 'keyword', 'score': 0.8} for item in result.data[:limit]]
        return []
    except:
        return []

def test_vector_search(client, query: str, limit: int = 10) -> List[Dict]:
    """벡터 검색"""
    try:
        query_embedding = get_query_embedding(query)
        result = client.table("recipes_keto_enhanced").select("id, title, blob, embedding").execute()
        
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
                    'type': 'vector',
                    'score': similarity
                })
        
        similarities.sort(key=lambda x: x['score'], reverse=True)
        return similarities[:limit]
    except:
        return []

def test_hybrid_search(client, query: str, limit: int = 5):
    """하이브리드 검색 (키워드 + 벡터)"""
    print(f"\n🔄 하이브리드 검색: '{query}'")
    
    # 키워드 검색
    keyword_results = test_keyword_search(client, query, limit)
    print(f"✅ 키워드 결과: {len(keyword_results)}개")
    
    # 벡터 검색
    vector_results = test_vector_search(client, query, limit)
    print(f"✅ 벡터 결과: {len(vector_results)}개")
    
    # 결과 합치기
    all_results = {}
    
    # 키워드 결과 추가
    for item in keyword_results:
        all_results[item['id']] = {
            'id': item['id'],
            'title': item['title'],
            'blob': item['blob'],
            'keyword_score': item['score'],
            'vector_score': 0.0
        }
    
    # 벡터 결과 추가/업데이트
    for item in vector_results:
        if item['id'] in all_results:
            all_results[item['id']]['vector_score'] = item['score']
        else:
            all_results[item['id']] = {
                'id': item['id'],
                'title': item['title'],
                'blob': item['blob'],
                'keyword_score': 0.0,
                'vector_score': item['score']
            }
    
    # 하이브리드 점수 계산 (가중 평균)
    for item in all_results.values():
        keyword_score = item['keyword_score']
        vector_score = item['vector_score']
        # 하이브리드 점수 = 0.4 * 키워드 + 0.6 * 벡터
        item['hybrid_score'] = 0.4 * keyword_score + 0.6 * vector_score
    
    # 하이브리드 점수 순으로 정렬
    hybrid_results = sorted(all_results.values(), key=lambda x: x['hybrid_score'], reverse=True)
    
    print(f"✅ 하이브리드 결과: {len(hybrid_results)}개")
    for i, item in enumerate(hybrid_results[:limit], 1):
        keyword_score = item['keyword_score'] * 100
        vector_score = item['vector_score'] * 100
        hybrid_score = item['hybrid_score'] * 100
        print(f"  {i}. {item['title'][:40]}...")
        print(f"     키워드: {keyword_score:.1f}% | 벡터: {vector_score:.1f}% | 하이브리드: {hybrid_score:.1f}%")

def test_all_searches():
    """모든 검색 방식 테스트"""
    print("=== 완전한 하이브리드 검색 성능 테스트 ===")
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 테스트 쿼리들
    test_queries = ["김밥", "키토 케이크", "저탄수 디저트", "계란 요리", "다이어트 음식"]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🔍 검색 쿼리: '{query}'")
        print('='*60)
        
        # 하이브리드 검색 테스트
        test_hybrid_search(client, query, 3)

if __name__ == "__main__":
    test_all_searches()
