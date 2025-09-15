#!/usr/bin/env python3
"""
Enhanced Blob 방식 대량 테스트
"""
from enhanced_blob_supabase import EnhancedBlobApproachSupabase

def test_enhanced_blob_batch():
    print("=== Enhanced Blob 방식 대량 테스트 ===")
    
    # Enhanced Blob 방식 초기화
    approach = EnhancedBlobApproachSupabase()
    
    # 기존 레시피 데이터로 테스트 (처음 20개)
    print("\n1. 기존 레시피 데이터 처리 시작...")
    approach.load_recipes_from_supabase("recipes_keto_raw", limit=20)
    
    # 검색 테스트
    test_queries = ["김밥", "아몬드 머핀", "키토 다이어트", "초콜릿 케이크"]
    
    print(f"\n2. 검색 테스트:")
    for query in test_queries:
        print(f"\n🔍 '{query}' 검색:")
        results = approach.search_similar_recipes(query, top_k=3)
        
        if results:
            for i, result in enumerate(results, 1):
                similarity_percent = result['similarity'] * 100
                print(f"  {i}. {result['title'][:50]}... ({similarity_percent:.1f}%)")
        else:
            print("  검색 결과 없음")

if __name__ == "__main__":
    test_enhanced_blob_batch()
