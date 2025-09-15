#!/usr/bin/env python3
"""
Enhanced Blob vs 기존 방식 검색 성능 비교
"""
import os
import sys
sys.path.append('..')

from enhanced_blob_supabase import EnhancedBlobApproachSupabase
from approach4_hybrid_ingredient_llm.approach4_supabase import HybridIngredientLLMApproachSupabase

def compare_search_performance():
    print("=== Enhanced Blob vs 기존 방식 검색 성능 비교 ===")
    
    # 두 방식 초기화
    enhanced_approach = EnhancedBlobApproachSupabase()
    existing_approach = HybridIngredientLLMApproachSupabase()
    
    # 테스트 쿼리들
    test_queries = ["김밥", "아몬드 머핀", "키토 다이어트"]
    
    for query in test_queries:
        print(f"\n🔍 '{query}' 검색 비교:")
        
        # Enhanced Blob 방식 검색
        print(f"\n📊 Enhanced Blob 방식:")
        try:
            enhanced_results = enhanced_approach.search_similar_recipes(query, top_k=3)
            if enhanced_results:
                for i, result in enumerate(enhanced_results, 1):
                    similarity_percent = result['similarity'] * 100
                    print(f"  {i}. {result['title'][:50]}... ({similarity_percent:.1f}%)")
            else:
                print("  검색 결과 없음")
        except Exception as e:
            print(f"  오류: {e}")
        
        # 기존 방식 검색
        print(f"\n📊 기존 방식:")
        try:
            existing_results = existing_approach.search_similar_recipes(query, top_k=3)
            if existing_results:
                for i, result in enumerate(existing_results, 1):
                    similarity_percent = result['similarity'] * 100
                    print(f"  {i}. {result['title'][:50]}... ({similarity_percent:.1f}%)")
            else:
                print("  검색 결과 없음")
        except Exception as e:
            print(f"  오류: {e}")

if __name__ == "__main__":
    compare_search_performance()
