"""
하이브리드 검색 테스트
"""
from ..core.hybrid_search import hybrid_search_engine

def test_hybrid_search():
    """하이브리드 검색 테스트"""
    print("🔍 하이브리드 검색 테스트")
    print("=" * 40)
    
    test_queries = [
        "김치찌개",
        "파스타",
        "닭가슴살",
        "디저트"
    ]
    
    for query in test_queries:
        print(f"\n📝 테스트 쿼리: '{query}'")
        results = hybrid_search_engine.search(query, 5)
        
        if results:
            print(f"✅ {len(results)}개 결과 발견")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result['title']} ({result['similarity_percentage']:.1f}%)")
        else:
            print("❌ 결과 없음")

def test_custom_weights():
    """사용자 정의 가중치 테스트"""
    print("\n⚖️ 사용자 정의 가중치 테스트")
    print("=" * 40)
    
    query = "김치찌개"
    weight_combinations = [
        (0.8, 0.2),  # 벡터 중심
        (0.5, 0.5),  # 균형
        (0.2, 0.8),  # 키워드 중심
    ]
    
    for vector_weight, keyword_weight in weight_combinations:
        print(f"\n📝 가중치 테스트: 벡터 {vector_weight}, 키워드 {keyword_weight}")
        results = hybrid_search_engine.search_with_custom_weights(
            query, 3, vector_weight, keyword_weight
        )
        
        if results:
            print(f"✅ {len(results)}개 결과 발견")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['title']} ({result['similarity_percentage']:.1f}%)")
        else:
            print("❌ 결과 없음")

if __name__ == "__main__":
    test_hybrid_search()
    test_custom_weights()
