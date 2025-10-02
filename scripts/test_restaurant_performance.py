#!/usr/bin/env python3
"""
식당 추천 기능 성능 테스트 스크립트
평균 생성 시간과 성공률을 측정합니다.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import sys
import os
from dotenv import load_dotenv

# 프로젝트 루트를 Python path에 추가
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# .env 파일 로드
env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(env_path)

from app.agents.place_search_agent import PlaceSearchAgent

class RestaurantPerformanceTester:
    def __init__(self):
        self.agent = PlaceSearchAgent()
        self.test_queries = [
            "강남역 근처 키토 식당 추천해줘",
            "압구정 맛집 키토 다이어트에 좋은 곳",
            "역삼동 저탄수화물 식당 어디가 좋을까?",
            "서울대입구역 근처 키토 친화적 레스토랑",
            "잠실 키토 식단에 맞는 맛집 찾아줘"
        ]
    
    async def test_single_query(self, query: str) -> Dict[str, Any]:
        """단일 쿼리 테스트"""
        print(f"🔍 테스트 쿼리: '{query}'")
        
        start_time = time.time()
        
        try:
            result = await self.agent.search_places(
                message=query,
                location={"lat": 37.4979, "lng": 127.0276},  # 강남역
                radius_km=5.0
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.get("response", "") != ""
            result_count = len(result.get("results", []))
            
            print(f"  ✅ 성공: {success}, 시간: {duration:.2f}초, 결과: {result_count}개")
            if success and result.get("response"):
                # 응답 내용 미리보기 (처음 100글자)
                response_preview = result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
                print(f"  📝 응답 미리보기: {response_preview}")
            
            return {
                "query": query,
                "success": success,
                "duration": duration,
                "result_count": result_count,
                "response_length": len(result.get("response", "")),
                "error": None
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"  ❌ 실패: {str(e)}, 시간: {duration:.2f}초")
            
            return {
                "query": query,
                "success": False,
                "duration": duration,
                "result_count": 0,
                "response_length": 0,
                "error": str(e)
            }
    
    async def run_performance_test(self, iterations: int = 3) -> Dict[str, Any]:
        """성능 테스트 실행"""
        print(f"🚀 식당 추천 성능 테스트 시작 (각 쿼리당 {iterations}회 반복)")
        print("=" * 80)
        
        all_results = []
        
        for i in range(iterations):
            print(f"\n📊 반복 {i+1}/{iterations}")
            print("-" * 40)
            
            for query in self.test_queries:
                result = await self.test_single_query(query)
                all_results.append(result)
                
                # 요청 간 간격 (API 제한 고려)
                await asyncio.sleep(1)
        
        # 결과 분석
        successful_results = [r for r in all_results if r["success"]]
        failed_results = [r for r in all_results if not r["success"]]
        
        if successful_results:
            durations = [r["duration"] for r in successful_results]
            response_lengths = [r["response_length"] for r in successful_results]
            result_counts = [r["result_count"] for r in successful_results]
            
            stats = {
                "total_tests": len(all_results),
                "successful_tests": len(successful_results),
                "failed_tests": len(failed_results),
                "success_rate": len(successful_results) / len(all_results) * 100,
                "avg_duration": statistics.mean(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "median_duration": statistics.median(durations),
                "std_duration": statistics.stdev(durations) if len(durations) > 1 else 0,
                "avg_response_length": statistics.mean(response_lengths),
                "avg_result_count": statistics.mean(result_counts),
                "failed_queries": [r["query"] for r in failed_results]
            }
        else:
            stats = {
                "total_tests": len(all_results),
                "successful_tests": 0,
                "failed_tests": len(failed_results),
                "success_rate": 0,
                "error": "모든 테스트가 실패했습니다."
            }
        
        return stats
    
    def print_summary(self, stats: Dict[str, Any]):
        """결과 요약 출력"""
        print("\n" + "=" * 80)
        print("📈 성능 테스트 결과 요약")
        print("=" * 80)
        
        print(f"총 테스트 수: {stats['total_tests']}")
        print(f"성공한 테스트: {stats['successful_tests']}")
        print(f"실패한 테스트: {stats['failed_tests']}")
        print(f"성공률: {stats['success_rate']:.1f}%")
        
        if 'avg_duration' in stats:
            print(f"\n⏱️ 시간 통계:")
            print(f"  평균 시간: {stats['avg_duration']:.2f}초")
            print(f"  최단 시간: {stats['min_duration']:.2f}초")
            print(f"  최장 시간: {stats['max_duration']:.2f}초")
            print(f"  중간값: {stats['median_duration']:.2f}초")
            print(f"  표준편차: {stats['std_duration']:.2f}초")
            
            print(f"\n📝 응답 통계:")
            print(f"  평균 응답 길이: {stats['avg_response_length']:.0f} 글자")
            print(f"  평균 결과 수: {stats['avg_result_count']:.1f}개")
        
        if stats['failed_tests'] > 0:
            print(f"\n❌ 실패한 쿼리들:")
            for query in stats.get('failed_queries', []):
                print(f"  - {query}")

async def main():
    """메인 실행 함수"""
    tester = RestaurantPerformanceTester()
    
    try:
        stats = await tester.run_performance_test(iterations=2)  # 각 쿼리당 2회 반복
        tester.print_summary(stats)
        
    except KeyboardInterrupt:
        print("\n⏹️ 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())
