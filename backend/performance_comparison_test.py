"""
GPT-4o-mini vs Gemini 2.5 Flash 성능 및 비용 비교 테스트
응답 속도, 토큰 사용량, 예상 비용을 수치화하여 비교
"""

import asyncio
import time
import json
from typing import Dict, Any, List
from datetime import datetime

# 테스트용 프롬프트들
TEST_PROMPTS = [
    "안녕하세요",
    "키토 다이어트에 좋은 음식 추천해주세요",
    "강남역 근처에서 키토 식당 추천해주세요",
    "아침에 먹을 키토 친화적인 간단한 요리 알려주세요",
    "키토 다이어트 중인데 외식할 때 주의할 점이 뭐가 있나요?",
    "키토 다이어트에서 탄수화물 하루 권장량은 얼마인가요?",
    "키토 다이어트로 체중 감량 효과를 보려면 얼마나 걸리나요?",
    "키토 다이어트 중 운동은 어떻게 해야 하나요?",
    "키토 다이어트에서 생리 불순이 생겼는데 어떻게 해야 하나요?",
    "키토 다이어트 중 술을 마셔도 되나요?"
]

class PerformanceTester:
    def __init__(self):
        self.results = {
            "gpt-4o-mini": [],
            "gemini-2.5-flash": []
        }
    
    async def test_model(self, provider: str, model: str, test_name: str) -> Dict[str, Any]:
        """단일 모델 테스트"""
        print(f"\n🔍 {test_name} 테스트 시작...")
        
        try:
            # LLM 초기화
            from app.core.llm_factory import create_chat_llm
            from app.core.config import settings
            
            if provider == "openai":
                llm = create_chat_llm(
                    provider="openai",
                    model="gpt-4o-mini",
                    temperature=0.2,
                    max_tokens=512,
                    timeout=10
                )
            else:  # gemini
                llm = create_chat_llm(
                    provider="gemini",
                    model="gemini-2.5-flash",
                    temperature=0.2,
                    max_tokens=8192,
                    timeout=60
                )
            
            print(f"✅ {test_name} LLM 초기화 완료")
            
            # 각 프롬프트에 대해 테스트
            prompt_results = []
            total_tokens = 0
            total_cost = 0.0
            
            for i, prompt in enumerate(TEST_PROMPTS, 1):
                print(f"  📝 테스트 {i}/{len(TEST_PROMPTS)}: {prompt[:30]}...")
                
                try:
                    start_time = time.time()
                    
                    # LLM 호출
                    from langchain.schema import HumanMessage
                    response = await llm.ainvoke([HumanMessage(content=prompt)])
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    # 토큰 수 추정 (대략적)
                    input_tokens = len(prompt.split()) * 1.3  # 한국어 토큰 추정
                    output_tokens = len(response.content.split()) * 1.3
                    total_prompt_tokens = input_tokens + output_tokens
                    
                    # 비용 계산
                    if provider == "openai":
                        # GPT-4o-mini 가격: 입력 $0.15/1M, 출력 $0.60/1M
                        input_cost = (input_tokens / 1_000_000) * 0.15
                        output_cost = (output_tokens / 1_000_000) * 0.60
                        prompt_cost = input_cost + output_cost
                    else:
                        # Gemini 2.5 Flash 가격: 입력 $0.25/1M, 출력 $1.00/1M
                        input_cost = (input_tokens / 1_000_000) * 0.25
                        output_cost = (output_tokens / 1_000_000) * 1.00
                        prompt_cost = input_cost + output_cost
                    
                    total_tokens += total_prompt_tokens
                    total_cost += prompt_cost
                    
                    prompt_result = {
                        "prompt": prompt,
                        "response_time": response_time,
                        "input_tokens": int(input_tokens),
                        "output_tokens": int(output_tokens),
                        "total_tokens": int(total_prompt_tokens),
                        "cost": prompt_cost,
                        "response_length": len(response.content),
                        "success": True
                    }
                    
                    print(f"    ⏱️ {response_time:.2f}초, 💰 ${prompt_cost:.6f}, 📊 {int(total_prompt_tokens)}토큰")
                    
                except Exception as e:
                    print(f"    ❌ 오류: {e}")
                    prompt_result = {
                        "prompt": prompt,
                        "error": str(e),
                        "success": False
                    }
                
                prompt_results.append(prompt_result)
                await asyncio.sleep(0.5)  # API 제한 방지
            
            # 전체 결과 집계
            successful_tests = [r for r in prompt_results if r.get("success", False)]
            avg_response_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests) if successful_tests else 0
            avg_tokens = sum(r["total_tokens"] for r in successful_tests) / len(successful_tests) if successful_tests else 0
            total_successful = len(successful_tests)
            
            model_result = {
                "model": test_name,
                "provider": provider,
                "total_tests": len(TEST_PROMPTS),
                "successful_tests": total_successful,
                "success_rate": (total_successful / len(TEST_PROMPTS)) * 100,
                "avg_response_time": avg_response_time,
                "total_tokens": int(total_tokens),
                "avg_tokens_per_request": avg_tokens,
                "total_cost": total_cost,
                "avg_cost_per_request": total_cost / len(TEST_PROMPTS),
                "detailed_results": prompt_results,
                "tested_at": datetime.now().isoformat()
            }
            
            print(f"\n📊 {test_name} 테스트 완료:")
            print(f"  ✅ 성공률: {model_result['success_rate']:.1f}%")
            print(f"  ⏱️ 평균 응답시간: {avg_response_time:.2f}초")
            print(f"  📊 총 토큰: {int(total_tokens):,}")
            print(f"  💰 총 비용: ${total_cost:.6f}")
            print(f"  💰 평균 비용/요청: ${total_cost/len(TEST_PROMPTS):.6f}")
            
            return model_result
            
        except Exception as e:
            print(f"❌ {test_name} 테스트 실패: {e}")
            return {
                "model": test_name,
                "provider": provider,
                "error": str(e),
                "success": False,
                "tested_at": datetime.now().isoformat()
            }
    
    async def run_comparison(self):
        """전체 비교 테스트 실행"""
        print("🚀 GPT-4o-mini vs Gemini 2.5 Flash 성능 비교 테스트 시작")
        print(f"📝 테스트 프롬프트: {len(TEST_PROMPTS)}개")
        print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # GPT-4o-mini 테스트
        gpt_result = await self.test_model("openai", "gpt-4o-mini", "GPT-4o-mini")
        self.results["gpt-4o-mini"] = gpt_result
        
        print("\n" + "="*60)
        
        # Gemini 테스트
        gemini_result = await self.test_model("gemini", "gemini-2.5-flash", "Gemini 2.5 Flash")
        self.results["gemini-2.5-flash"] = gemini_result
        
        # 결과 비교 및 분석
        self.print_comparison()
        
        # 결과 저장
        self.save_results()
    
    def print_comparison(self):
        """결과 비교 출력"""
        print("\n" + "="*80)
        print("📊 성능 비교 결과")
        print("="*80)
        
        gpt = self.results["gpt-4o-mini"]
        gemini = self.results["gemini-2.5-flash"]
        
        if not gpt.get("success", True) or not gemini.get("success", True):
            print("❌ 일부 테스트가 실패했습니다. 상세 결과를 확인하세요.")
            return
        
        # 응답 시간 비교
        gpt_time = gpt["avg_response_time"]
        gemini_time = gemini["avg_response_time"]
        time_improvement = ((gemini_time - gpt_time) / gemini_time) * 100
        
        print(f"\n⏱️ 응답 속도 비교:")
        print(f"  GPT-4o-mini:    {gpt_time:.2f}초")
        print(f"  Gemini 2.5:     {gemini_time:.2f}초")
        print(f"  개선율:         {time_improvement:+.1f}% ({'빠름' if time_improvement > 0 else '느림'})")
        
        # 비용 비교
        gpt_cost = gpt["total_cost"]
        gemini_cost = gemini["total_cost"]
        cost_savings = ((gemini_cost - gpt_cost) / gemini_cost) * 100
        
        print(f"\n💰 비용 비교 (10개 요청 기준):")
        print(f"  GPT-4o-mini:    ${gpt_cost:.6f}")
        print(f"  Gemini 2.5:     ${gemini_cost:.6f}")
        print(f"  절약액:         ${gemini_cost - gpt_cost:.6f}")
        print(f"  절약율:         {cost_savings:+.1f}%")
        
        # 토큰 효율성 비교
        gpt_tokens = gpt["total_tokens"]
        gemini_tokens = gemini["total_tokens"]
        token_efficiency = (gpt_tokens / gemini_tokens) * 100 if gemini_tokens > 0 else 0
        
        print(f"\n📊 토큰 사용량 비교:")
        print(f"  GPT-4o-mini:    {gpt_tokens:,} 토큰")
        print(f"  Gemini 2.5:     {gemini_tokens:,} 토큰")
        print(f"  효율성:         {token_efficiency:.1f}% (100% = Gemini와 동일)")
        
        # 성공률 비교
        gpt_success = gpt["success_rate"]
        gemini_success = gemini["success_rate"]
        
        print(f"\n✅ 안정성 비교:")
        print(f"  GPT-4o-mini:    {gpt_success:.1f}%")
        print(f"  Gemini 2.5:     {gemini_success:.1f}%")
        
        # 월간 예상 비용 (1000회 요청 기준)
        monthly_gpt = gpt_cost * 100
        monthly_gemini = gemini_cost * 100
        monthly_savings = monthly_gemini - monthly_gpt
        
        print(f"\n📈 월간 예상 비용 (1000회 요청):")
        print(f"  GPT-4o-mini:    ${monthly_gpt:.2f}")
        print(f"  Gemini 2.5:     ${monthly_gemini:.2f}")
        print(f"  월간 절약액:    ${monthly_savings:.2f}")
        
        # 종합 평가
        print(f"\n🎯 종합 평가:")
        if time_improvement > 0 and cost_savings > 0:
            print(f"  🚀 GPT-4o-mini가 우수: {time_improvement:.1f}% 빠르고 {cost_savings:.1f}% 저렴")
        elif time_improvement > 0:
            print(f"  ⚡ GPT-4o-mini가 빠름: {time_improvement:.1f}% 빠른 응답")
        elif cost_savings > 0:
            print(f"  💰 GPT-4o-mini가 저렴: {cost_savings:.1f}% 비용 절약")
        else:
            print(f"  ⚖️  양쪽 모두 장단점 있음")
    
    def save_results(self):
        """결과를 JSON 파일로 저장"""
        filename = f"performance_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 결과 저장: {filename}")

async def main():
    """메인 실행 함수"""
    tester = PerformanceTester()
    await tester.run_comparison()

if __name__ == "__main__":
    asyncio.run(main())
