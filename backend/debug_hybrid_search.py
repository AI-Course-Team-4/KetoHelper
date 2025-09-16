"""
하이브리드 검색 디버깅 스크립트
실제 검색 결과를 확인
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tools.hybrid_search import hybrid_search_tool

async def debug_hybrid_search():
    """하이브리드 검색 디버깅"""
    print("🔍 하이브리드 검색 디버깅 시작")
    print("=" * 50)
    
    # 테스트 쿼리
    test_query = "한식 중에 어떤 음식을 섭취하면 키토 다이어트에 도움이 되는지 알려줘"
    
    print(f"테스트 쿼리: '{test_query}'")
    print("-" * 30)
    
    try:
        # 1. 벡터 검색 테스트
        print("1. ChromaDB 벡터 검색 테스트:")
        vector_results = await hybrid_search_tool._vector_search(test_query, 3)
        print(f"   결과: {len(vector_results)}개")
        for i, result in enumerate(vector_results, 1):
            print(f"   {i}. {result['title']} (점수: {result['vector_score']:.3f})")
        
        # 2. 키워드 검색 테스트
        print("\n2. Supabase 키워드 검색 테스트:")
        keyword_results = await hybrid_search_tool._keyword_search(test_query, 3)
        print(f"   결과: {len(keyword_results)}개")
        for i, result in enumerate(keyword_results, 1):
            print(f"   {i}. {result['title']} (점수: {result['keyword_score']:.3f})")
        
        # 3. 하이브리드 검색 테스트
        print("\n3. 하이브리드 검색 테스트:")
        hybrid_results = await hybrid_search_tool.hybrid_search(test_query, k=3)
        print(f"   결과: {len(hybrid_results)}개")
        for i, result in enumerate(hybrid_results, 1):
            print(f"   {i}. {result['title']} (하이브리드 점수: {result['hybrid_score']:.3f})")
        
        # 4. 간단한 검색 테스트
        print("\n4. 간단한 검색 테스트:")
        simple_results = await hybrid_search_tool.search(test_query, "", max_results=3)
        print(f"   결과: {len(simple_results)}개")
        for i, result in enumerate(simple_results, 1):
            print(f"   {i}. {result['title']} (유사도: {result['similarity']:.3f})")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_hybrid_search())
