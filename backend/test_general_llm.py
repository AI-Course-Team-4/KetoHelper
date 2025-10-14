"""
General 분기 LLM 응답 테스트
템플릿 최소화 후 LLM이 대부분의 질문을 처리하는지 확인
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.orchestrator import KetoCoachAgent


async def test_general_llm():
    """일반 채팅 LLM 응답 테스트"""
    
    print("=" * 80)
    print("🧪 General 분기 LLM 응답 테스트 (템플릿 최소화)")
    print("=" * 80)
    
    # 에이전트 초기화
    print("\n1️⃣ 에이전트 초기화 중...")
    try:
        agent = KetoCoachAgent()
        print("✅ 에이전트 초기화 성공")
    except Exception as e:
        print(f"❌ 에이전트 초기화 실패: {e}")
        return
    
    # 테스트 케이스들
    test_cases = [
        {
            "message": "안녕하세요",
            "expected": "template",
            "description": "인사말 (템플릿)"
        },
        {
            "message": "키토 시작하려고 해",
            "expected": "template",
            "description": "키토 시작 가이드 (템플릿)"
        },
        {
            "message": "너는 뭐야",
            "expected": "template",
            "description": "자기소개 (템플릿)"
        },
        {
            "message": "키토 다이어트는 어떤걸 먹으면 안돼?",
            "expected": "llm",
            "description": "피해야 할 음식 질문 (LLM)"
        },
        {
            "message": "키토 다이어트가 뭐야?",
            "expected": "llm",
            "description": "키토 설명 (LLM)"
        },
        {
            "message": "탄수화물을 줄이는 게 힘들어요",
            "expected": "llm",
            "description": "일반 상담 (LLM)"
        },
        {
            "message": "키토에서 먹을 수 있는 것은?",
            "expected": "llm",
            "description": "먹을 수 있는 음식 (LLM)"
        }
    ]
    
    # 각 테스트 케이스 실행
    template_count = 0
    llm_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"테스트 {i}/{len(test_cases)}: {test_case['description']}")
        print(f"{'='*80}")
        print(f"📝 입력: {test_case['message']}")
        print(f"🎯 기대: {test_case['expected'].upper()}")
        
        try:
            # 메시지 처리
            result = await agent.process_message(
                message=test_case['message'],
                profile=None
            )
            
            # 응답 방식 확인
            tool_calls = result.get('tool_calls', [])
            is_template = any(
                call.get('method') == 'template_based' 
                for call in tool_calls
            )
            
            actual = "template" if is_template else "llm"
            
            # 결과 출력
            if actual == test_case['expected']:
                print(f"✅ 성공: {actual.upper()} 사용")
                if actual == "template":
                    template_count += 1
                else:
                    llm_count += 1
            else:
                print(f"❌ 실패: {actual.upper()} 사용 (기대: {test_case['expected'].upper()})")
            
            # 응답 미리보기
            response = result.get('response', '')
            if response:
                lines = response.split('\n')
                preview = lines[0][:70] if lines else ""
                print(f"💬 응답: {preview}...")
                print(f"   (총 {len(response)}자)")
            
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            import traceback
            print(traceback.format_exc())
    
    print(f"\n{'='*80}")
    print("📊 테스트 결과 요약")
    print(f"{'='*80}")
    print(f"✅ 템플릿 사용: {template_count}개")
    print(f"🤖 LLM 사용: {llm_count}개")
    print(f"📝 총 테스트: {len(test_cases)}개")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(test_general_llm())

