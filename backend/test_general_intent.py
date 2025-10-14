"""
General 분기 AI 응답 생성 테스트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.core.orchestrator import KetoCoachAgent


async def test_general_chat():
    """일반 채팅 응답 테스트"""
    
    print("=" * 80)
    print("🧪 General 분기 AI 응답 생성 테스트")
    print("=" * 80)
    
    # 에이전트 초기화
    print("\n1️⃣ 에이전트 초기화 중...")
    try:
        agent = KetoCoachAgent()
        print("✅ 에이전트 초기화 성공")
        print(f"   - LLM 초기화 상태: {agent.llm is not None}")
        print(f"   - IntentClassifier 상태: {agent.intent_classifier is not None}")
    except Exception as e:
        print(f"❌ 에이전트 초기화 실패: {e}")
        return
    
    # 테스트 케이스들
    test_cases = [
        {
            "message": "키토 다이어트가 뭐야?",
            "description": "일반적인 키토 다이어트 질문"
        },
        {
            "message": "안녕하세요",
            "description": "인사 메시지"
        },
        {
            "message": "키토 다이어트 시작하려고 해",
            "description": "키토 시작 질문 (템플릿 응답)"
        },
        {
            "message": "탄수화물을 줄이는 게 힘들어요",
            "description": "일반 상담 메시지"
        }
    ]
    
    # 각 테스트 케이스 실행
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"테스트 {i}/{len(test_cases)}: {test_case['description']}")
        print(f"{'='*80}")
        print(f"📝 입력 메시지: {test_case['message']}")
        
        try:
            # 메시지 처리
            result = await agent.process_message(
                message=test_case['message'],
                profile=None
            )
            
            # 결과 출력
            print(f"\n✅ 처리 완료!")
            print(f"   - 의도 (Intent): {result['intent']}")
            print(f"   - 도구 호출: {len(result.get('tool_calls', []))}개")
            
            # 응답 내용 확인
            response = result.get('response', '')
            if response:
                print(f"\n💬 AI 응답:")
                print(f"   {'-'*76}")
                # 응답을 줄바꿈하여 보기 좋게 출력
                for line in response.split('\n'):
                    print(f"   {line}")
                print(f"   {'-'*76}")
                print(f"   - 응답 길이: {len(response)} 글자")
                
                # LLM 호출 여부 확인
                tool_calls = result.get('tool_calls', [])
                has_llm_call = any(
                    'general' in str(call).lower() 
                    for call in tool_calls
                )
                print(f"   - LLM 호출 여부: {'✅ Yes' if has_llm_call else '❌ No'}")
                
                # 템플릿 사용 여부 확인
                template_used = any(
                    call.get('method') == 'template_based' 
                    for call in tool_calls
                )
                print(f"   - 템플릿 사용: {'✅ Yes' if template_used else '❌ No (LLM 사용)'}")
            else:
                print(f"\n❌ 응답이 비어있음!")
                
        except Exception as e:
            print(f"\n❌ 테스트 실패: {e}")
            import traceback
            print(traceback.format_exc())
    
    print(f"\n{'='*80}")
    print("🎯 테스트 완료")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(test_general_chat())

