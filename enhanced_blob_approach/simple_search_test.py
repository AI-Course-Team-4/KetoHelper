#!/usr/bin/env python3
"""
Enhanced Blob 방식 간단 검색 테스트
"""
from enhanced_blob_supabase import EnhancedBlobApproachSupabase

def simple_search_test():
    print("=== Enhanced Blob 방식 검색 테스트 ===")
    
    # Enhanced Blob 방식 초기화
    approach = EnhancedBlobApproachSupabase()
    
    # 테스트 쿼리들
    test_queries = ["김밥", "아몬드", "키토", "다이어트"]
    
    for query in test_queries:
        print(f"\n🔍 '{query}' 검색:")
        try:
            results = approach.search_similar_recipes(query, top_k=5)
            
            if results:
                print(f"  📊 {len(results)}개 결과:")
                for i, result in enumerate(results, 1):
                    similarity_percent = result['similarity'] * 100
                    print(f"    {i}. {result['title'][:60]}... ({similarity_percent:.1f}%)")
            else:
                print("  검색 결과 없음")
                
        except Exception as e:
            print(f"  오류: {e}")

if __name__ == "__main__":
    simple_search_test()
