#!/usr/bin/env python3
"""
일반 채팅 기능 성능 테스트 스크립트
평균 응답 시간과 성공률을 측정합니다.
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

from app.agents.chat_agent import SimpleKetoCoachAgent

class ChatPerformanceTester:
    def __init__(self):
        self.agent = SimpleKetoCoachAgent()
        self.test_queries = [
            "키토 다이어트가 뭐야?",
            "탄수화물을 얼마나 제한해야 해?",
            "키토 플루에 걸렸을 때 어떻게 해야 해?",
            "아보카도가 키토에 좋은 이유가 뭐야?",
            "키토 다이어트 중에 과일을 먹어도 될까?",
            "인슐린 저항성이 뭔가요?",
            "키토시스 상태가 뭔가요?",
            "MCT 오일이 뭐고 언제 먹어야 해?",
            "키토 다이어트 중에 운동은 어떻게 해야 해?",
            "키토 친화적인 간식 추천해줘"
        ]
    
    async def test_single_query(self, query: str) -> Dict[str, Any]:
        """단일 쿼리 테스트"""
        print(f"🔍 테스트 쿼리: '{query}'")
        
        start_time = time.time()
        
        try:
            result = await self.agent.process_message(
                message=query,
                profile={
                    "diet_type": "keto",
                    "experience_level": "beginner"
                }
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.get("response", "") != ""
            response_length = len(result.get("response", ""))
            has_keto_info = any(keyword in result.get("response", "").lower() 
                              for keyword in ["키토", "keto", "탄수화물", "지방", "인슐린"])
            
            print(f"  ✅ 성공: {success}, 시간: {duration:.2f}초, 길이: {response_length}글자, 키토 정보: {has_keto_info}")
            if success and result.get("response"):
                # 응답 내용 미리보기 (처음 100글자)
                response_preview = result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
                print(f"  📝 응답 미리보기: {response_preview}")
            
            return {
                "query": query,
                "success": success,
                "duration": duration,
                "response_length": response_length,
                "has_keto_info": has_keto_info,
                "response": result.get("response", ""),
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
                "response_length": 0,
                "has_keto_info": False,
                "response": "",
                "error": str(e)
            }
    
    async def test_conversation_flow(self, queries: List[str]) -> Dict[str, Any]:
        """대화 흐름 테스트"""
        print(f"🔍 대화 흐름 테스트: {len(queries)}개 질문")
        
        start_time = time.time()
        conversation_results = []
        
        try:
            for i, query in enumerate(queries):
                print(f"  질문 {i+1}/{len(queries)}: {query}")
                
                result = await self.test_single_query(query)
                conversation_results.append(result)
                
                # 질문 간 간격
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
        print(f"🚀 일반 채팅 성능 테스트 시작 (각 쿼리당 {iterations}회 반복)")
        print("=" * 80)
        
        all_results = []
        
        # 1. 단일 질문 테스트
        print(f"\n📊 1. 단일 질문 테스트")
        print("-" * 40)
        for i in range(iterations):
            print(f"\n반복 {i+1}/{iterations}")
            for query in self.test_queries:
                result = await self.test_single_query(query)
                all_results.append(result)
                await asyncio.sleep(1)
        
        # 2. 대화 흐름 테스트
        print(f"\n📊 2. 대화 흐름 테스트")
        print("-" * 40)
        conversation_queries = [
            "키토 다이어트가 뭐야?",
            "그럼 탄수화물을 얼마나 제한해야 해?",
            "아보카도가 키토에 좋은 이유가 뭐야?",
            "키토 다이어트 중에 과일을 먹어도 될까?",
            "그럼 키토 친화적인 간식은 뭐가 있어?"
        ]
        
        for i in range(iterations):
            print(f"\n대화 흐름 반복 {i+1}/{iterations}")
            conversation_result = await self.test_conversation_flow(conversation_queries)
            all_results.append({
                "test_type": "conversation",
                "iteration": i + 1,
                **conversation_result
            })
            await asyncio.sleep(2)
        
        # 결과 분석
        single_query_results = [r for r in all_results if "test_type" not in r]
        conversation_results = [r for r in all_results if r.get("test_type") == "conversation"]
        
        successful_single = [r for r in single_query_results if r["success"]]
        successful_conversations = [r for r in conversation_results if r["successful_responses"] > 0]
        
        if successful_single:
            durations = [r["duration"] for r in successful_single]
            response_lengths = [r["response_length"] for r in successful_single]
            keto_info_count = len([r for r in successful_single if r["has_keto_info"]])
            
            single_stats = {
                "total_queries": len(single_query_results),
                "successful_queries": len(successful_single),
                "success_rate": len(successful_single) / len(single_query_results) * 100,
                "keto_info_rate": keto_info_count / len(successful_single) * 100 if successful_single else 0,
                "avg_duration": statistics.mean(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "median_duration": statistics.median(durations),
                "std_duration": statistics.stdev(durations) if len(durations) > 1 else 0,
                "avg_response_length": statistics.mean(response_lengths)
            }
        else:
            single_stats = {"error": "단일 질문 테스트 실패"}
        
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
            "conversation_stats": conversation_stats
        }
        
        return stats
    
    def print_summary(self, stats: Dict[str, Any]):
        """결과 요약 출력"""
        print("\n" + "=" * 80)
        print("📈 일반 채팅 성능 테스트 결과 요약")
        print("=" * 80)
        
        print(f"총 테스트 수: {stats['total_tests']}")
        print(f"단일 질문 테스트: {stats['single_query_tests']}")
        print(f"대화 흐름 테스트: {stats['conversation_tests']}")
        
        # 단일 질문 통계
        if "error" not in stats["single_query_stats"]:
            print(f"\n⏱️ 단일 질문 시간 통계:")
            print(f"  총 질문 수: {stats['single_query_stats']['total_queries']}")
            print(f"  성공한 질문: {stats['single_query_stats']['successful_queries']}")
            print(f"  성공률: {stats['single_query_stats']['success_rate']:.1f}%")
            print(f"  키토 정보 포함률: {stats['single_query_stats']['keto_info_rate']:.1f}%")
            print(f"  평균 응답 시간: {stats['single_query_stats']['avg_duration']:.2f}초")
            print(f"  최단 응답 시간: {stats['single_query_stats']['min_duration']:.2f}초")
            print(f"  최장 응답 시간: {stats['single_query_stats']['max_duration']:.2f}초")
            print(f"  중간값: {stats['single_query_stats']['median_duration']:.2f}초")
            print(f"  표준편차: {stats['single_query_stats']['std_duration']:.2f}초")
            print(f"  평균 응답 길이: {stats['single_query_stats']['avg_response_length']:.0f}글자")
        else:
            print(f"\n❌ 단일 질문 테스트: {stats['single_query_stats']['error']}")
        
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

async def main():
    """메인 실행 함수"""
    tester = ChatPerformanceTester()
    
    try:
        stats = await tester.run_performance_test(iterations=2)  # 각 테스트당 2회 반복
        tester.print_summary(stats)
        
    except KeyboardInterrupt:
        print("\n⏹️ 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())
