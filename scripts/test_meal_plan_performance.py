#!/usr/bin/env python3
"""
식단 생성 기능 성능 테스트 스크립트
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

from app.agents.meal_planner import MealPlannerAgent

class MealPlanPerformanceTester:
    def __init__(self):
        self.agent = MealPlannerAgent()
        self.test_queries = [
            # 7일 테스트
            "7일 키토 식단표 만들어줘",
            "다음 주 식단 계획 세워줘",
            "키토 다이어트 1주일 메뉴 추천해줘",
            "저탄수화물 식단표 작성해줘",
            "키토 식단 7일 계획 세워줘",
            
            # 3일 테스트
            "3일 키토 식단 만들어줘",
            "주말 3일치 식단표 작성해줘",
            "키토 다이어트 3일 메뉴 추천해줘",
            "저탄수화물 3일 식단표",
            "키토 식단 3일 계획",
            
            # 1일 테스트
            "오늘 키토 식단 추천해줘",
            "내일 식단표 만들어줘",
            "키토 다이어트 하루 메뉴",
            "저탄수화물 하루 식단",
            "키토 식단 1일 계획",
            
            # 2주 테스트
            "2주 키토 식단표 만들어줘",
            "2주일 식단 계획 세워줘",
            "키토 다이어트 2주 메뉴 추천해줘",
            "저탄수화물 2주 식단표",
            "키토 식단 2주 계획",
            
            # 자연어 테스트
            "이번 주 식단 만들어줘",
            "다음 주말 식단표",
            "키토 다이어트 며칠치 메뉴",
            "저탄수화물 며칠 식단표",
            "키토 식단 며칠 계획"
        ]
    
    def _categorize_query(self, query: str) -> str:
        """쿼리를 기간별로 분류"""
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ["1일", "하루", "오늘", "내일"]):
            return "1일"
        elif any(keyword in query_lower for keyword in ["3일", "주말"]):
            return "3일"
        elif any(keyword in query_lower for keyword in ["7일", "1주일", "다음 주", "이번 주"]):
            return "7일"
        elif any(keyword in query_lower for keyword in ["2주", "2주일"]):
            return "2주"
        else:
            return "자연어"
    
    def _calculate_parsing_accuracy(self, category_results: List[Dict], expected_category: str) -> float:
        """날짜 파싱 정확도 계산"""
        if not category_results:
            return 0.0
        
        expected_days = {
            "1일": 1,
            "3일": 3,
            "7일": 7,
            "2주": 14,
            "자연어": None  # 자연어는 정확한 일수 예측이 어려움
        }
        
        expected = expected_days.get(expected_category)
        if expected is None:
            return 0.0  # 자연어는 정확도 계산 제외
        
        correct_parsing = 0
        for result in category_results:
            parsed_days = result.get("parsed_days")
            if parsed_days == expected:
                correct_parsing += 1
        
        return (correct_parsing / len(category_results)) * 100
    
    async def test_single_query(self, query: str) -> Dict[str, Any]:
        """단일 쿼리 테스트"""
        print(f"🔍 테스트 쿼리: '{query}'")
        
        start_time = time.time()
        
        try:
            result = await self.agent.handle_meal_request(
                message=query,
                state={
                    "user_profile": {
                        "diet_type": "keto",
                        "allergies": [],
                        "dislikes": [],
                        "preferences": []
                    }
                }
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.get("response", "") != ""
            has_meal_plan = "식단" in result.get("response", "") or "메뉴" in result.get("response", "")
            has_weekly_structure = "월요일" in result.get("response", "") or "1일차" in result.get("response", "")
            
            # 기간별 분류
            query_category = self._categorize_query(query)
            
            # 파싱된 일수 확인 (state에서 추출)
            parsed_days = None
            if "state" in result and "slots" in result["state"]:
                parsed_days = result["state"]["slots"].get("days")
            
            print(f"  ✅ 성공: {success}, 시간: {duration:.2f}초, 카테고리: {query_category}, 파싱된 일수: {parsed_days}")
            if success and result.get("response"):
                # 응답 내용 미리보기 (처음 100글자)
                response_preview = result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
                print(f"  📝 응답 미리보기: {response_preview}")
            
            return {
                "query": query,
                "query_category": query_category,
                "success": success,
                "duration": duration,
                "has_meal_plan": has_meal_plan,
                "has_weekly_structure": has_weekly_structure,
                "parsed_days": parsed_days,
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
                "has_meal_plan": False,
                "has_weekly_structure": False,
                "response_length": 0,
                "error": str(e)
            }
    
    async def run_performance_test(self, iterations: int = 3) -> Dict[str, Any]:
        """성능 테스트 실행"""
        print(f"🚀 식단 생성 성능 테스트 시작 (각 쿼리당 {iterations}회 반복)")
        print("=" * 80)
        
        all_results = []
        
        for i in range(iterations):
            print(f"\n📊 반복 {i+1}/{iterations}")
            print("-" * 40)
            
            for query in self.test_queries:
                result = await self.test_single_query(query)
                all_results.append(result)
                
                # 요청 간 간격 (API 제한 고려)
                await asyncio.sleep(2)
        
        # 결과 분석
        successful_results = [r for r in all_results if r["success"]]
        failed_results = [r for r in all_results if not r["success"]]
        meal_plan_results = [r for r in successful_results if r["has_meal_plan"]]
        weekly_structure_results = [r for r in successful_results if r["has_weekly_structure"]]
        
        # 기간별 분석
        category_stats = {}
        for category in ["1일", "3일", "7일", "2주", "자연어"]:
            category_results = [r for r in all_results if r.get("query_category") == category]
            category_successful = [r for r in category_results if r["success"]]
            
            if category_results:
                category_stats[category] = {
                    "total": len(category_results),
                    "successful": len(category_successful),
                    "success_rate": len(category_successful) / len(category_results) * 100,
                    "avg_duration": statistics.mean([r["duration"] for r in category_successful]) if category_successful else 0,
                    "parsed_days_accuracy": self._calculate_parsing_accuracy(category_results, category)
                }
        
        if successful_results:
            durations = [r["duration"] for r in successful_results]
            response_lengths = [r["response_length"] for r in successful_results]
            
            stats = {
                "total_tests": len(all_results),
                "successful_tests": len(successful_results),
                "failed_tests": len(failed_results),
                "meal_plan_tests": len(meal_plan_results),
                "weekly_structure_tests": len(weekly_structure_results),
                "success_rate": len(successful_results) / len(all_results) * 100,
                "meal_plan_rate": len(meal_plan_results) / len(successful_results) * 100 if successful_results else 0,
                "weekly_structure_rate": len(weekly_structure_results) / len(successful_results) * 100 if successful_results else 0,
                "avg_duration": statistics.mean(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "median_duration": statistics.median(durations),
                "std_duration": statistics.stdev(durations) if len(durations) > 1 else 0,
                "avg_response_length": statistics.mean(response_lengths),
                "category_stats": category_stats,
                "failed_queries": [r["query"] for r in failed_results]
            }
        else:
            stats = {
                "total_tests": len(all_results),
                "successful_tests": 0,
                "failed_tests": len(failed_results),
                "meal_plan_tests": 0,
                "weekly_structure_tests": 0,
                "success_rate": 0,
                "meal_plan_rate": 0,
                "weekly_structure_rate": 0,
                "error": "모든 테스트가 실패했습니다."
            }
        
        return stats
    
    def print_summary(self, stats: Dict[str, Any]):
        """결과 요약 출력"""
        print("\n" + "=" * 80)
        print("📈 식단 생성 성능 테스트 결과 요약")
        print("=" * 80)
        
        print(f"총 테스트 수: {stats['total_tests']}")
        print(f"성공한 테스트: {stats['successful_tests']}")
        print(f"실패한 테스트: {stats['failed_tests']}")
        print(f"식단 포함 테스트: {stats['meal_plan_tests']}")
        print(f"주간 구조 포함 테스트: {stats['weekly_structure_tests']}")
        print(f"성공률: {stats['success_rate']:.1f}%")
        print(f"식단 포함률: {stats['meal_plan_rate']:.1f}%")
        print(f"주간 구조 포함률: {stats['weekly_structure_rate']:.1f}%")
        
        if 'avg_duration' in stats:
            print(f"\n⏱️ 시간 통계:")
            print(f"  평균 시간: {stats['avg_duration']:.2f}초")
            print(f"  최단 시간: {stats['min_duration']:.2f}초")
            print(f"  최장 시간: {stats['max_duration']:.2f}초")
            print(f"  중간값: {stats['median_duration']:.2f}초")
            print(f"  표준편차: {stats['std_duration']:.2f}초")
            
            print(f"\n📝 응답 통계:")
            print(f"  평균 응답 길이: {stats['avg_response_length']:.0f} 글자")
        
        # 기간별 통계
        if 'category_stats' in stats and stats['category_stats']:
            print(f"\n📅 기간별 성능 분석:")
            for category, cat_stats in stats['category_stats'].items():
                print(f"  {category} 테스트:")
                print(f"    총 테스트: {cat_stats['total']}개")
                print(f"    성공: {cat_stats['successful']}개")
                print(f"    성공률: {cat_stats['success_rate']:.1f}%")
                print(f"    평균 시간: {cat_stats['avg_duration']:.2f}초")
                if cat_stats['parsed_days_accuracy'] > 0:
                    print(f"    파싱 정확도: {cat_stats['parsed_days_accuracy']:.1f}%")
                print()
        
        if stats['failed_tests'] > 0:
            print(f"\n❌ 실패한 쿼리들:")
            for query in stats.get('failed_queries', []):
                print(f"  - {query}")

async def main():
    """메인 실행 함수"""
    tester = MealPlanPerformanceTester()
    
    try:
        stats = await tester.run_performance_test(iterations=1)  # 각 쿼리당 1회 반복 (쿼리가 많아서)
        tester.print_summary(stats)
        
    except KeyboardInterrupt:
        print("\n⏹️ 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())
