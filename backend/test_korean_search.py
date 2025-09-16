"""
한글 검색 최적화 테스트 스크립트
PostgreSQL Full-Text Search + pg_trgm + 벡터 검색 통합 테스트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tools.korean_search import korean_search_tool
from app.tools.hybrid_search import hybrid_search_tool

async def test_korean_search():
    """한글 검색 최적화 테스트"""
    print("🔍 한글 검색 최적화 테스트 시작")
    print("=" * 60)
    
    # 테스트 쿼리들 (한글 중심)
    test_queries = [
        "키토 아침 메뉴 추천해줘",
        "김치볶음밥 레시피",
        "아보카도 요리",
        "불고기 만들기",
        "저탄수화물 한국 요리",
        "삼겹살 구이",
        "생선 요리",
        "샐러드 레시피",
        "간단한 키토 식단",
        "한식 키토화"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 테스트 쿼리: '{query}'")
        print("-" * 40)
        
        try:
            # 한글 최적화 검색 실행
            print("  🚀 한글 최적화 검색 실행...")
            korean_results = await korean_search_tool.korean_hybrid_search(query, k=3)
            
            if korean_results:
                print(f"  ✅ 한글 최적화 결과: {len(korean_results)}개")
                for j, result in enumerate(korean_results, 1):
                    print(f"    {j}. {result['title']}")
                    print(f"       최종 점수: {result['final_score']:.3f}")
                    print(f"       검색 타입: {result['search_type']}")
                    print(f"       벡터: {result.get('vector_score', 0):.3f}, FTS: {result.get('fts_score', 0):.3f}")
                    print()
            else:
                print("  ❌ 한글 최적화 검색 결과 없음")
            
            # 기존 검색과 비교
            print("  🔄 기존 검색과 비교...")
            original_results = await hybrid_search_tool.hybrid_search(query, k=3)
            
            if original_results:
                print(f"  ✅ 기존 검색 결과: {len(original_results)}개")
                for j, result in enumerate(original_results, 1):
                    print(f"    {j}. {result['title']} (점수: {result['hybrid_score']:.3f})")
            else:
                print("  ❌ 기존 검색 결과 없음")
                
        except Exception as e:
            print(f"  ❌ 검색 오류: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 한글 검색 최적화 테스트 완료")

async def test_search_performance():
    """검색 성능 비교 테스트"""
    print("\n📊 검색 성능 비교 테스트")
    print("=" * 60)
    
    test_query = "키토 불고기 레시피"
    
    # 한글 최적화 검색 성능 테스트
    print(f"테스트 쿼리: '{test_query}'")
    print("-" * 40)
    
    try:
        import time
        
        # 한글 최적화 검색
        start_time = time.time()
        korean_results = await korean_search_tool.korean_hybrid_search(test_query, k=5)
        korean_time = (time.time() - start_time) * 1000
        
        print(f"한글 최적화 검색:")
        print(f"  실행 시간: {korean_time:.2f}ms")
        print(f"  결과 수: {len(korean_results)}개")
        if korean_results:
            print(f"  최고 점수: {max(r['final_score'] for r in korean_results):.3f}")
        
        # 기존 검색
        start_time = time.time()
        original_results = await hybrid_search_tool.hybrid_search(test_query, k=5)
        original_time = (time.time() - start_time) * 1000
        
        print(f"\n기존 검색:")
        print(f"  실행 시간: {original_time:.2f}ms")
        print(f"  결과 수: {len(original_results)}개")
        if original_results:
            print(f"  최고 점수: {max(r['hybrid_score'] for r in original_results):.3f}")
        
        # 성능 비교
        if korean_time > 0 and original_time > 0:
            speed_improvement = ((original_time - korean_time) / original_time) * 100
            print(f"\n성능 개선: {speed_improvement:+.1f}%")
        
    except Exception as e:
        print(f"성능 테스트 오류: {e}")

async def test_search_types():
    """검색 타입별 테스트"""
    print("\n🔍 검색 타입별 테스트")
    print("=" * 60)
    
    test_query = "한식 키토"
    
    try:
        # Full-Text Search 테스트
        print("1. Full-Text Search 테스트:")
        fts_results = await korean_search_tool._full_text_search(test_query, 3)
        print(f"   결과: {len(fts_results)}개")
        for result in fts_results:
            print(f"   - {result['title']} (점수: {result['search_score']:.3f})")
        
        # Trigram 검색 테스트
        print("\n2. Trigram 유사도 검색 테스트:")
        trigram_results = await korean_search_tool._trigram_similarity_search(test_query, 3)
        print(f"   결과: {len(trigram_results)}개")
        for result in trigram_results:
            print(f"   - {result['title']} (점수: {result['search_score']:.3f})")
        
        # ILIKE 검색 테스트
        print("\n3. ILIKE 폴백 검색 테스트:")
        ilike_results = await korean_search_tool._fallback_ilike_search(test_query, 3)
        print(f"   결과: {len(ilike_results)}개")
        for result in ilike_results:
            print(f"   - {result['title']} (점수: {result['search_score']:.3f})")
        
    except Exception as e:
        print(f"검색 타입별 테스트 오류: {e}")

async def test_smart_search():
    """스마트 검색 테스트 (새로운 기능)"""
    print("\n🧠 스마트 검색 테스트")
    print("=" * 60)
    
    # 다양한 검색 시나리오 테스트
    test_scenarios = [
        {
            "query": "키토",
            "description": "정확한 매칭 시나리오"
        },
        {
            "query": "키토 불고기",
            "description": "부분 매칭 시나리오"
        },
        {
            "query": "존재하지않는검색어",
            "description": "검색 결과 없음 시나리오"
        },
        {
            "query": "한식 키토",
            "description": "하이브리드 검색 시나리오"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['description']}")
        print(f"   쿼리: '{scenario['query']}'")
        print("-" * 40)
        
        try:
            # 스마트 검색 실행
            smart_result = await korean_search_tool.smart_search(scenario['query'], k=3)
            
            print(f"   🔍 검색 전략: {smart_result['search_strategy']}")
            print(f"   💬 메시지: {smart_result['message']}")
            print(f"   📊 결과 수: {smart_result['total_count']}개")
            
            if smart_result['results']:
                print("   📋 검색 결과:")
                for j, result in enumerate(smart_result['results'], 1):
                    print(f"     {j}. {result['title']} (점수: {result.get('search_score', 0):.3f})")
            else:
                print("   ❌ 검색 결과 없음")
                
        except Exception as e:
            print(f"   ❌ 스마트 검색 오류: {e}")

async def test_improved_hybrid_search():
    """개선된 하이브리드 검색 테스트"""
    print("\n🔄 개선된 하이브리드 검색 테스트")
    print("=" * 60)
    
    test_queries = [
        "키토",
        "키토 불고기", 
        "한식 키토",
        "존재하지않는검색어"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 테스트 쿼리: '{query}'")
        print("-" * 40)
        
        try:
            # 개선된 하이브리드 검색 실행
            results = await korean_search_tool.korean_hybrid_search(query, k=3)
            
            if results:
                # 첫 번째 결과에서 검색 전략과 메시지 추출
                first_result = results[0]
                search_strategy = first_result.get('search_strategy', 'unknown')
                search_message = first_result.get('search_message', '')
                
                print(f"   🔍 검색 전략: {search_strategy}")
                print(f"   💬 메시지: {search_message}")
                print(f"   📊 결과 수: {len(results)}개")
                
                print("   📋 검색 결과:")
                for j, result in enumerate(results, 1):
                    print(f"     {j}. {result['title']} (점수: {result['final_score']:.3f}, 타입: {result['search_type']})")
            else:
                print("   ❌ 검색 결과 없음")
                
        except Exception as e:
            print(f"   ❌ 개선된 하이브리드 검색 오류: {e}")

async def main():
    """메인 테스트 함수"""
    print("🚀 한글 검색 최적화 종합 테스트")
    print("=" * 60)
    
    # 1. 기본 한글 검색 테스트
    await test_korean_search()
    
    # 2. 성능 비교 테스트
    await test_search_performance()
    
    # 3. 검색 타입별 테스트
    await test_search_types()
    
    # 4. 스마트 검색 테스트 (새로운 기능)
    await test_smart_search()
    
    # 5. 개선된 하이브리드 검색 테스트
    await test_improved_hybrid_search()
    
    print("\n🎉 모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())
