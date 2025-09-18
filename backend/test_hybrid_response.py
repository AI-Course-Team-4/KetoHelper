"""
하이브리드 응답 방식 테스트 스크립트
다양한 검색 시나리오에 대한 응답 테스트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.simple_agent import SimpleKetoCoachAgent
from app.tools.hybrid_search import hybrid_search_tool

async def test_hybrid_responses():
    """하이브리드 응답 방식 테스트"""
    print("🧪 하이브리드 응답 방식 테스트")
    print("=" * 60)
    
    # 테스트 시나리오들
    test_scenarios = [
        {
            "query": "키토",
            "description": "정확한 매칭 시나리오",
            "expected_strategy": "exact"
        },
        {
            "query": "키토 불고기",
            "description": "부분 매칭 시나리오",
            "expected_strategy": "partial"
        },
        {
            "query": "존재하지않는검색어",
            "description": "검색 결과 없음 시나리오",
            "expected_strategy": "none"
        },
        {
            "query": "한식 키토",
            "description": "하이브리드 검색 시나리오",
            "expected_strategy": "partial"
        }
    ]
    
    agent = SimpleKetoCoachAgent()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['description']}")
        print(f"   쿼리: '{scenario['query']}'")
        print("-" * 50)
        
        try:
            # 1. 검색 결과 확인
            print("   🔍 검색 결과 확인:")
            search_results = await hybrid_search_tool.search(scenario['query'], "", 3)
            
            if search_results:
                first_result = search_results[0]
                search_strategy = first_result.get('search_strategy', 'unknown')
                search_message = first_result.get('search_message', '')
                
                print(f"     전략: {search_strategy}")
                print(f"     메시지: {search_message}")
                print(f"     결과 수: {len(search_results)}개")
                
                for j, result in enumerate(search_results[:2], 1):
                    print(f"     {j}. {result['title']} (점수: {result['similarity']:.3f})")
            else:
                print("     검색 결과 없음")
            
            # 2. AI 에이전트 응답 생성
            print("\n   🤖 AI 에이전트 응답:")
            response = await agent.process_message(scenario['query'])
            
            # 응답 내용 출력 (처음 300자만)
            response_text = response.get('response', '')
            print(f"     {response_text[:300]}{'...' if len(response_text) > 300 else ''}")
            
            # 3. 응답 타입 분석
            print("\n   📊 응답 분석:")
            if "정확한 레시피를 찾았습니다" in response_text:
                print("     ✅ 정확한 매칭 응답")
            elif "관련된 키토 레시피를 찾았습니다" in response_text:
                print("     🎯 부분 매칭 응답")
            elif "구체적인 레시피를 찾을 수 없습니다" in response_text:
                print("     🚫 검색 결과 없음 응답")
            else:
                print("     ❓ 기타 응답")
                
        except Exception as e:
            print(f"   ❌ 테스트 오류: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 하이브리드 응답 방식 테스트 완료")

async def test_specific_scenarios():
    """특정 시나리오 상세 테스트"""
    print("\n🔬 특정 시나리오 상세 테스트")
    print("=" * 60)
    
    agent = SimpleKetoCoachAgent()
    
    # "키토 불고기" 시나리오 상세 테스트
    print("\n1. '키토 불고기' 시나리오 상세 분석")
    print("-" * 40)
    
    try:
        # 검색 결과 확인
        search_results = await hybrid_search_tool.search("키토 불고기", "", 3)
        
        print("🔍 검색 결과:")
        if search_results:
            first_result = search_results[0]
            print(f"   전략: {first_result.get('search_strategy', 'unknown')}")
            print(f"   메시지: {first_result.get('search_message', '')}")
            print(f"   결과 수: {len(search_results)}개")
            
            for i, result in enumerate(search_results, 1):
                print(f"   {i}. {result['title']} (점수: {result['similarity']:.3f})")
        else:
            print("   검색 결과 없음")
        
        # AI 응답 생성
        print("\n🤖 AI 응답 생성:")
        response = await agent.process_message("키토 불고기")
        
        response_text = response.get('response', '')
        print(f"응답 길이: {len(response_text)}자")
        print(f"응답 내용:\n{response_text}")
        
        # 응답 분석
        print("\n📊 응답 분석:")
        if "정확한 레시피를 찾았습니다" in response_text:
            print("   ✅ 정확한 매칭 응답")
        elif "관련된 키토 레시피를 찾았습니다" in response_text:
            print("   🎯 부분 매칭 응답")
        elif "구체적인 레시피를 찾을 수 없습니다" in response_text:
            print("   🚫 검색 결과 없음 응답")
        else:
            print("   ❓ 기타 응답")
            
        # 키워드 분석
        keywords = ["정확한", "관련된", "참고용", "일반적인", "조언"]
        found_keywords = [kw for kw in keywords if kw in response_text]
        print(f"   발견된 키워드: {found_keywords}")
        
    except Exception as e:
        print(f"❌ 상세 테스트 오류: {e}")

async def main():
    """메인 테스트 함수"""
    print("🚀 하이브리드 응답 방식 종합 테스트")
    print("=" * 60)
    
    # 1. 기본 하이브리드 응답 테스트
    await test_hybrid_responses()
    
    # 2. 특정 시나리오 상세 테스트
    await test_specific_scenarios()
    
    print("\n🎉 모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())
