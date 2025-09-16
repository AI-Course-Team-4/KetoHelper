"""
Frontend API 검색 테스트 스크립트
실제 API 엔드포인트를 통해 검색 기능 테스트
"""

import asyncio
import requests
import json
import time

# API 엔드포인트 설정
API_BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat/"

async def test_frontend_search():
    """Frontend API 검색 테스트"""
    print("🌐 Frontend API 검색 테스트")
    print("=" * 60)
    
    # 테스트 쿼리들
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
            # API 요청 데이터
            request_data = {
                "message": query,
                "location": None,
                "radius_km": 5.0,
                "profile": None
            }
            
            # API 호출
            start_time = time.time()
            response = requests.post(
                CHAT_ENDPOINT,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            api_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"  ✅ API 응답 성공: {api_time:.2f}ms")
                print(f"  🔍 의도: {result.get('intent', 'unknown')}")
                print(f"  📊 결과 수: {len(result.get('results', []))}개")
                
                # 응답 내용 출력
                response_text = result.get('response', '')
                if response_text:
                    print(f"  💬 AI 응답:")
                    print(f"    {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
                
                # 검색 결과 출력
                results = result.get('results', [])
                if results:
                    print(f"  📋 검색 결과:")
                    for j, result_item in enumerate(results, 1):
                        title = result_item.get('title', '제목 없음')
                        similarity = result_item.get('similarity', 0.0)
                        search_strategy = result_item.get('search_strategy', 'unknown')
                        search_message = result_item.get('search_message', '')
                        
                        print(f"    {j}. {title} (점수: {similarity:.3f})")
                        if search_strategy != 'unknown':
                            print(f"       전략: {search_strategy}")
                        if search_message:
                            print(f"       메시지: {search_message}")
                else:
                    print("  ❌ 검색 결과 없음")
                    
            else:
                print(f"  ❌ API 오류: {response.status_code}")
                print(f"  오류 내용: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ 요청 오류: {e}")
        except Exception as e:
            print(f"  ❌ 처리 오류: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Frontend API 검색 테스트 완료")

async def test_direct_hybrid_search():
    """직접 하이브리드 검색 도구 테스트"""
    print("\n🔧 직접 하이브리드 검색 도구 테스트")
    print("=" * 60)
    
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from app.tools.hybrid_search import hybrid_search_tool
    
    test_queries = [
        "키토",
        "키토 불고기", 
        "한식 키토"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 직접 테스트 쿼리: '{query}'")
        print("-" * 40)
        
        try:
            start_time = time.time()
            results = await hybrid_search_tool.search(query, "", 3)
            direct_time = (time.time() - start_time) * 1000
            
            print(f"  ✅ 직접 검색 성공: {direct_time:.2f}ms")
            print(f"  📊 결과 수: {len(results)}개")
            
            for j, result in enumerate(results, 1):
                title = result.get('title', '제목 없음')
                similarity = result.get('similarity', 0.0)
                search_strategy = result.get('search_strategy', 'unknown')
                search_message = result.get('search_message', '')
                
                print(f"    {j}. {title} (점수: {similarity:.3f})")
                if search_strategy != 'unknown':
                    print(f"       전략: {search_strategy}")
                if search_message:
                    print(f"       메시지: {search_message}")
                    
        except Exception as e:
            print(f"  ❌ 직접 검색 오류: {e}")

async def main():
    """메인 테스트 함수"""
    print("🚀 Frontend 검색 기능 종합 테스트")
    print("=" * 60)
    
    # 1. 직접 하이브리드 검색 도구 테스트
    await test_direct_hybrid_search()
    
    # 2. Frontend API 검색 테스트
    await test_frontend_search()
    
    print("\n🎉 모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())
