#!/usr/bin/env python3
"""
식단 저장 기능 성능 테스트 스크립트
자연어 요청부터 식단 생성 및 저장까지의 전체 플로우를 테스트합니다.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import sys
import os
from dotenv import load_dotenv
from datetime import date, timedelta

# 프로젝트 루트를 Python path에 추가
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# .env 파일 로드
env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(env_path)

from app.core.orchestrator import Orchestrator

class MealSavePerformanceTester:
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.test_user_id = "test_user_123"
        self.test_queries = [
            # 식단 생성 및 저장 요청
            "7일 키토 식단표 만들어서 저장해줘",
            "다음 주 식단 계획 세워서 캘린더에 추가해줘",
            "키토 다이어트 1주일 메뉴 만들어서 저장해줘",
            "저탄수화물 식단표 작성해서 저장해줘",
            "키토 식단 7일 계획 세워서 저장해줘",
            
            # 3일 식단 저장
            "3일 키토 식단 만들어서 저장해줘",
            "주말 3일치 식단표 작성해서 저장해줘",
            "키토 다이어트 3일 메뉴 만들어서 저장해줘",
            
            # 1일 식단 저장
            "오늘 키토 식단 만들어서 저장해줘",
            "내일 식단표 작성해서 저장해줘",
            "키토 다이어트 하루 메뉴 만들어서 저장해줘",
            
            # 자연어 저장 요청
            "이번 주 식단 만들어서 저장해줘",
            "키토 다이어트 며칠치 메뉴 만들어서 저장해줘",
            "저탄수화물 식단 만들어서 저장해줘"
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
        else:
            return "자연어"
    
    async def test_single_query(self, query: str) -> Dict[str, Any]:
        """단일 자연어 쿼리 테스트 (의도 분류 → 식단 생성 → 저장)"""
        print(f"🔍 테스트 쿼리: '{query}'")
        
        start_time = time.time()
        
        try:
            # Orchestrator를 통한 전체 플로우 처리
            result = await self.orchestrator.process_message(
                message=query,
                user_id=self.test_user_id,
                location={"lat": 37.4979, "lng": 127.0276},  # 강남역
                radius_km=5.0
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 결과 분석
            success = result.get("response", "") != ""
            has_meal_plan = "식단" in result.get("response", "") or "메뉴" in result.get("response", "")
            has_save_intent = "저장" in query or "추가" in query or "계획" in query
            has_weekly_structure = "월요일" in result.get("response", "") or "1일차" in result.get("response", "")
            
            # 기간별 분류
            query_category = self._categorize_query(query)
            
            # 의도 분류 확인
            intent = result.get("intent", "unknown")
            
            print(f"  ✅ 성공: {success}, 시간: {duration:.2f}초, 의도: {intent}, 카테고리: {query_category}")
            if success and result.get("response"):
                # 응답 내용 미리보기 (처음 100글자)
                response_preview = result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
                print(f"  📝 응답 미리보기: {response_preview}")
            
            return {
                "query": query,
                "query_category": query_category,
                "success": success,
                "duration": duration,
                "intent": intent,
                "has_meal_plan": has_meal_plan,
                "has_save_intent": has_save_intent,
                "has_weekly_structure": has_weekly_structure,
                "response_length": len(result.get("response", "")),
                "error": None
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"  ❌ 실패: {str(e)}, 시간: {duration:.2f}초")
            
            return {
                "query": query,
                "query_category": self._categorize_query(query),
                "success": False,
                "duration": duration,
                "intent": "error",
                "has_meal_plan": False,
                "has_save_intent": False,
                "has_weekly_structure": False,
                "response_length": 0,
                "error": str(e)
            }
    
    async def test_conversation_flow(self, queries: List[str]) -> Dict[str, Any]:
        """대화 흐름 테스트 (여러 요청을 순차적으로 처리)"""
        print(f"🔍 대화 흐름 테스트: {len(queries)}개 요청")
        
        start_time = time.time()
        conversation_results = []
        
        try:
            for i, query in enumerate(queries):
                print(f"  요청 {i+1}/{len(queries)}: {query}")
                
                result = await self.test_single_query(query)
                conversation_results.append(result)
                
                # 요청 간 간격
                await asyncio.sleep(1)
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            successful_responses = [r for r in conversation_results if r["success"]]
            avg_response_time = statistics.mean([r["duration"] for r in successful_responses]) if successful_responses else 0
            
            print(f"  ✅ 대화 완료: {len(successful_responses)}/{len(queries)} 성공, 총 시간: {total_duration:.2f}초")
            
            return {
                "total_queries": len(queries),
                "successful_responses": len(successful_responses),
                "total_duration": total_duration,
                "avg_response_time": avg_response_time,
                "conversation_results": conversation_results
            }
            
        except Exception as e:
            end_time = time.time()
            total_duration = end_time - start_time
            
            print(f"  ❌ 대화 실패: {str(e)}, 시간: {total_duration:.2f}초")
            
            return {
                "total_queries": len(queries),
                "successful_responses": 0,
                "total_duration": total_duration,
                "avg_response_time": 0,
                "error": str(e)
            }
    
    async def run_performance_test(self, iterations: int = 3) -> Dict[str, Any]:
        """성능 테스트 실행"""
        print(f"🚀 식단 저장 성능 테스트 시작 (각 쿼리당 {iterations}회 반복)")
        print("=" * 80)
        
        all_results = []
        
        # 1. 단일 요청 테스트
        print(f"\n📊 1. 단일 요청 테스트")
        print("-" * 40)
        for i in range(iterations):
            print(f"\n반복 {i+1}/{iterations}")
            for query in self.test_queries:
                result = await self.test_single_query(query)
                all_results.append(result)
                await asyncio.sleep(2)
        
        # 2. 대화 흐름 테스트
        print(f"\n📊 2. 대화 흐름 테스트")
        print("-" * 40)
        conversation_queries = [
            "7일 키토 식단표 만들어서 저장해줘",
            "3일 키토 식단도 만들어서 저장해줘",
            "오늘 식단도 만들어서 저장해줘"
        ]
        
        for i in range(iterations):
            print(f"\n대화 흐름 반복 {i+1}/{iterations}")
            conversation_result = await self.test_conversation_flow(conversation_queries)
            all_results.append({
                "test_type": "conversation",
                "iteration": i + 1,
                **conversation_result
            })
            await asyncio.sleep(3)
        
        # 결과 분석
        single_query_results = [r for r in all_results if "test_type" not in r]
        conversation_results = [r for r in all_results if r.get("test_type") == "conversation"]
        
        successful_single = [r for r in single_query_results if r["success"]]
        successful_conversations = [r for r in conversation_results if r["successful_responses"] > 0]
        
        # 기간별 분석
        category_stats = {}
        for category in ["1일", "3일", "7일", "자연어"]:
            category_results = [r for r in single_query_results if r.get("query_category") == category]
            category_successful = [r for r in category_results if r["success"]]
            
            if category_results:
                category_stats[category] = {
                    "total": len(category_results),
                    "successful": len(category_successful),
                    "success_rate": len(category_successful) / len(category_results) * 100,
                    "avg_duration": statistics.mean([r["duration"] for r in category_successful]) if category_successful else 0,
                    "meal_plan_rate": len([r for r in category_successful if r["has_meal_plan"]]) / len(category_successful) * 100 if category_successful else 0
                }
        
        # 의도별 분석
        intent_stats = {}
        for result in single_query_results:
            intent = result.get("intent", "unknown")
            if intent not in intent_stats:
                intent_stats[intent] = {"total": 0, "successful": 0, "durations": []}
            intent_stats[intent]["total"] += 1
            if result["success"]:
                intent_stats[intent]["successful"] += 1
                intent_stats[intent]["durations"].append(result["duration"])
        
        for intent in intent_stats:
            stats = intent_stats[intent]
            stats["success_rate"] = stats["successful"] / stats["total"] * 100 if stats["total"] > 0 else 0
            stats["avg_duration"] = statistics.mean(stats["durations"]) if stats["durations"] else 0
        
        if successful_single:
            durations = [r["duration"] for r in successful_single]
            response_lengths = [r["response_length"] for r in successful_single]
            
            single_stats = {
                "total_queries": len(single_query_results),
                "successful_queries": len(successful_single),
                "success_rate": len(successful_single) / len(single_query_results) * 100,
                "avg_duration": statistics.mean(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "median_duration": statistics.median(durations),
                "std_duration": statistics.stdev(durations) if len(durations) > 1 else 0,
                "avg_response_length": statistics.mean(response_lengths)
            }
        else:
            single_stats = {"error": "단일 요청 테스트 실패"}
        
        if successful_conversations:
            conversation_durations = [r["total_duration"] for r in successful_conversations]
            avg_response_times = [r["avg_response_time"] for r in successful_conversations]
            
            conversation_stats = {
                "total_conversations": len(conversation_results),
                "successful_conversations": len(successful_conversations),
                "success_rate": len(successful_conversations) / len(conversation_results) * 100,
                "avg_total_duration": statistics.mean(conversation_durations),
                "avg_response_time": statistics.mean(avg_response_times)
            }
        else:
            conversation_stats = {"error": "대화 흐름 테스트 실패"}
        
        stats = {
            "total_tests": len(all_results),
            "single_query_tests": len(single_query_results),
            "conversation_tests": len(conversation_results),
            "single_query_stats": single_stats,
            "conversation_stats": conversation_stats,
            "category_stats": category_stats,
            "intent_stats": intent_stats
        }
        
        return stats
    
    def print_summary(self, stats: Dict[str, Any]):
        """결과 요약 출력"""
        print("\n" + "=" * 80)
        print("📈 식단 저장 성능 테스트 결과 요약")
        print("=" * 80)
        
        print(f"총 테스트 수: {stats['total_tests']}")
        print(f"단일 요청 테스트: {stats['single_query_tests']}")
        print(f"대화 흐름 테스트: {stats['conversation_tests']}")
        
        # 단일 요청 통계
        if "error" not in stats["single_query_stats"]:
            print(f"\n⏱️ 단일 요청 시간 통계:")
            print(f"  총 요청 수: {stats['single_query_stats']['total_queries']}")
            print(f"  성공한 요청: {stats['single_query_stats']['successful_queries']}")
            print(f"  성공률: {stats['single_query_stats']['success_rate']:.1f}%")
            print(f"  평균 응답 시간: {stats['single_query_stats']['avg_duration']:.2f}초")
            print(f"  최단 응답 시간: {stats['single_query_stats']['min_duration']:.2f}초")
            print(f"  최장 응답 시간: {stats['single_query_stats']['max_duration']:.2f}초")
            print(f"  중간값: {stats['single_query_stats']['median_duration']:.2f}초")
            print(f"  표준편차: {stats['single_query_stats']['std_duration']:.2f}초")
            print(f"  평균 응답 길이: {stats['single_query_stats']['avg_response_length']:.0f}글자")
        else:
            print(f"\n❌ 단일 요청 테스트: {stats['single_query_stats']['error']}")
        
        # 대화 흐름 통계
        if "error" not in stats["conversation_stats"]:
            print(f"\n💬 대화 흐름 통계:")
            print(f"  총 대화 수: {stats['conversation_stats']['total_conversations']}")
            print(f"  성공한 대화: {stats['conversation_stats']['successful_conversations']}")
            print(f"  성공률: {stats['conversation_stats']['success_rate']:.1f}%")
            print(f"  평균 대화 시간: {stats['conversation_stats']['avg_total_duration']:.2f}초")
            print(f"  평균 응답 시간: {stats['conversation_stats']['avg_response_time']:.2f}초")
        else:
            print(f"\n❌ 대화 흐름 테스트: {stats['conversation_stats']['error']}")
        
        # 기간별 통계
        if 'category_stats' in stats and stats['category_stats']:
            print(f"\n📅 기간별 성능 분석:")
            for category, cat_stats in stats['category_stats'].items():
                print(f"  {category} 요청:")
                print(f"    총 요청: {cat_stats['total']}개")
                print(f"    성공: {cat_stats['successful']}개")
                print(f"    성공률: {cat_stats['success_rate']:.1f}%")
                print(f"    평균 시간: {cat_stats['avg_duration']:.2f}초")
                print(f"    식단 포함률: {cat_stats['meal_plan_rate']:.1f}%")
                print()
        
        # 의도별 통계
        if 'intent_stats' in stats and stats['intent_stats']:
            print(f"\n🎯 의도별 성능 분석:")
            for intent, intent_stats in stats['intent_stats'].items():
                print(f"  {intent} 의도:")
                print(f"    총 요청: {intent_stats['total']}개")
                print(f"    성공: {intent_stats['successful']}개")
                print(f"    성공률: {intent_stats['success_rate']:.1f}%")
                print(f"    평균 시간: {intent_stats['avg_duration']:.2f}초")
                print()

async def main():
    """메인 실행 함수"""
    tester = MealSavePerformanceTester()
    
    try:
        stats = await tester.run_performance_test(iterations=2)  # 각 쿼리당 2회 반복
        tester.print_summary(stats)
        
    except KeyboardInterrupt:
        print("\n⏹️ 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())