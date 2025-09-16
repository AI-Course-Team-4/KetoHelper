"""
하이브리드 검색 테스트 스크립트
ChromaDB + Supabase 하이브리드 검색 기능 테스트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tools.hybrid_search import hybrid_search_tool

async def test_hybrid_search():
    """하이브리드 검색 테스트"""
    print("🔍 하이브리드 검색 테스트 시작")
    print("=" * 50)
    
    # 테스트 쿼리들
    test_queries = [
        "키토 아침 메뉴 추천해줘",
        "김치볶음밥 레시피",
        "아보카도 요리",
        "불고기 만들기",
        "저탄수화물 한국 요리"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 테스트 쿼리: '{query}'")
        print("-" * 30)
        
        try:
            # 하이브리드 검색 실행
            results = await hybrid_search_tool.hybrid_search(query, k=3)
            
            if results:
                print(f"✅ 검색 결과: {len(results)}개")
                for j, result in enumerate(results, 1):
                    print(f"  {j}. {result['title']}")
                    print(f"     하이브리드 점수: {result['hybrid_score']:.3f}")
                    print(f"     벡터 점수: {result['vector_score']:.3f}")
                    print(f"     키워드 점수: {result['keyword_score']:.3f}")
                    print(f"     메타데이터 점수: {result['metadata_score']:.3f}")
                    print(f"     검색 유형: {result['search_type']}")
                    print()
            else:
                print("❌ 검색 결과 없음")
                
        except Exception as e:
            print(f"❌ 검색 오류: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 하이브리드 검색 테스트 완료")

async def test_simple_search():
    """간단한 검색 인터페이스 테스트"""
    print("\n🔍 간단한 검색 인터페이스 테스트")
    print("=" * 50)
    
    try:
        # 간단한 검색 실행
        results = await hybrid_search_tool.search("키토 아침 메뉴", "아침에 먹을 수 있는 쉬운 요리", max_results=2)
        
        if results:
            print(f"✅ 검색 결과: {len(results)}개")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['title']}")
                print(f"     유사도: {result['similarity']:.3f}")
                print(f"     검색 유형: {result['search_types']}")
                print(f"     내용: {result['content'][:100]}...")
                print()
        else:
            print("❌ 검색 결과 없음")
            
    except Exception as e:
        print(f"❌ 검색 오류: {e}")

async def main():
    """메인 테스트 함수"""
    print("🚀 하이브리드 검색 시스템 테스트")
    print("ChromaDB (벡터 검색) + Supabase (키워드 검색)")
    print()
    
    # 하이브리드 검색 테스트
    await test_hybrid_search()
    
    # 간단한 검색 테스트
    await test_simple_search()
    
    print("\n🎉 모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())
