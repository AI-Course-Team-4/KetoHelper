#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
30개 사용자 질의 테스트셋으로 종합 검색 성능 테스트
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

# 30개 테스트 쿼리 (다양한 카테고리)
TEST_QUERIES = [
    # 김밥 관련 (5개)
    "김밥", "키토김밥", "참치계란김밥", "밥없는김밥", "양배추김밥",
    
    # 케이크/디저트 (5개)
    "키토케이크", "저탄수케이크", "치즈케이크", "레몬케이크", "다이어트디저트",
    
    # 계란 요리 (4개)
    "계란요리", "계란말이", "스크램블에그", "계란부침",
    
    # 다이어트/건강식 (4개)
    "다이어트음식", "저탄수식단", "키토식단", "건강식",
    
    # 구체적 재료 (4개)
    "아몬드가루", "베이컨", "치즈", "단무지",
    
    # 요리 방법 (4개)
    "전자렌지요리", "간편요리", "도시락", "한끼식사",
    
    # 특수 요구사항 (4개)
    "무설탕", "밀가루없는", "저칼로리", "고단백"
]

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

def test_keyword_search(client, query: str, limit: int = 5) -> List[Dict]:
    """키워드 검색"""
    try:
        result = client.table("recipes_keto_enhanced").select("*").text_search("blob", query).execute()
        if result.data:
            return [{'id': item['id'], 'title': item['title'], 'blob': item['blob'], 'type': 'keyword', 'score': 0.8} for item in result.data[:limit]]
        return []
    except:
        return []

def test_vector_search(client, query: str, limit: int = 5) -> List[Dict]:
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

def test_hybrid_search(client, query: str, limit: int = 3):
    """하이브리드 검색"""
    # 키워드 검색
    keyword_results = test_keyword_search(client, query, limit)
    
    # 벡터 검색
    vector_results = test_vector_search(client, query, limit)
    
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
    
    return {
        'keyword_count': len(keyword_results),
        'vector_count': len(vector_results),
        'hybrid_results': hybrid_results[:limit]
    }

def run_comprehensive_test():
    """30개 쿼리로 종합 테스트 실행"""
    print("=== 30개 사용자 질의 종합 검색 성능 테스트 ===")
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 카테고리별 결과 집계
    category_stats = {
        '김밥': {'keyword': 0, 'vector': 0, 'hybrid': 0},
        '케이크/디저트': {'keyword': 0, 'vector': 0, 'hybrid': 0},
        '계란요리': {'keyword': 0, 'vector': 0, 'hybrid': 0},
        '다이어트/건강식': {'keyword': 0, 'vector': 0, 'hybrid': 0},
        '구체적재료': {'keyword': 0, 'vector': 0, 'hybrid': 0},
        '요리방법': {'keyword': 0, 'vector': 0, 'hybrid': 0},
        '특수요구사항': {'keyword': 0, 'vector': 0, 'hybrid': 0}
    }
    
    category_ranges = [
        (0, 5, '김밥'),
        (5, 10, '케이크/디저트'),
        (10, 14, '계란요리'),
        (14, 18, '다이어트/건강식'),
        (18, 22, '구체적재료'),
        (22, 26, '요리방법'),
        (26, 30, '특수요구사항')
    ]
    
    total_keyword_results = 0
    total_vector_results = 0
    total_hybrid_results = 0
    
    print(f"\n총 {len(TEST_QUERIES)}개 쿼리 테스트 시작...\n")
    
    for i, query in enumerate(TEST_QUERIES):
        print(f"{i+1:2d}. '{query}' 검색:")
        
        # 하이브리드 검색 실행
        result = test_hybrid_search(client, query, 3)
        
        keyword_count = result['keyword_count']
        vector_count = result['vector_count']
        hybrid_count = len(result['hybrid_results'])
        
        total_keyword_results += keyword_count
        total_vector_results += vector_count
        total_hybrid_results += hybrid_count
        
        # 카테고리별 통계 업데이트
        for start, end, category in category_ranges:
            if start <= i < end:
                category_stats[category]['keyword'] += keyword_count
                category_stats[category]['vector'] += vector_count
                category_stats[category]['hybrid'] += hybrid_count
                break
        
        # 결과 출력
        if result['hybrid_results']:
            print(f"    키워드: {keyword_count}개 | 벡터: {vector_count}개 | 하이브리드: {hybrid_count}개")
            best_result = result['hybrid_results'][0]
            best_score = best_result['hybrid_score'] * 100
            print(f"    최고 점수: {best_result['title'][:40]}... ({best_score:.1f}%)")
        else:
            print(f"    키워드: {keyword_count}개 | 벡터: {vector_count}개 | 하이브리드: 0개")
            print("    ❌ 결과 없음")
        print()
    
    # 전체 통계 출력
    print("="*80)
    print("📊 전체 검색 성능 통계")
    print("="*80)
    print(f"총 쿼리 수: {len(TEST_QUERIES)}개")
    print(f"키워드 검색 총 결과: {total_keyword_results}개 (평균: {total_keyword_results/len(TEST_QUERIES):.1f}개/쿼리)")
    print(f"벡터 검색 총 결과: {total_vector_results}개 (평균: {total_vector_results/len(TEST_QUERIES):.1f}개/쿼리)")
    print(f"하이브리드 검색 총 결과: {total_hybrid_results}개 (평균: {total_hybrid_results/len(TEST_QUERIES):.1f}개/쿼리)")
    
    print(f"\n📈 카테고리별 성능:")
    for category, stats in category_stats.items():
        avg_keyword = stats['keyword'] / 5 if category != '계란요리' else stats['keyword'] / 4
        avg_vector = stats['vector'] / 5 if category != '계란요리' else stats['vector'] / 4
        avg_hybrid = stats['hybrid'] / 5 if category != '계란요리' else stats['hybrid'] / 4
        print(f"  {category:12s}: 키워드 {avg_keyword:.1f} | 벡터 {avg_vector:.1f} | 하이브리드 {avg_hybrid:.1f}")

if __name__ == "__main__":
    run_comprehensive_test()
