"""
벡터 검색 테스트
"""
from ..core.vector_search import vector_search_engine

def test_vector_search():
    """벡터 검색 테스트"""
    print("🔍 벡터 검색 테스트")
    print("=" * 40)
    
    test_queries = [
        "김치찌개",
        "파스타",
        "닭가슴살",
        "디저트"
    ]
    
    for query in test_queries:
        print(f"\n📝 테스트 쿼리: '{query}'")
        results = vector_search_engine.search(query, 5)
        
        if results:
            print(f"✅ {len(results)}개 결과 발견")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result['title']} ({result['similarity_percentage']:.1f}%)")
        else:
            print("❌ 결과 없음")

if __name__ == "__main__":
    test_vector_search()
