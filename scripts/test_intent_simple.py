"""
간단한 의도분류 테스트 - 실제 동작 확인용
"""
import sys
import os
import asyncio

# 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# UTF-8 인코딩 설정
if sys.platform == "win32":
    import locale
    import codecs
    try:
        import subprocess
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
    except:
        pass
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)
    except:
        pass

# 테스트 케이스 (간단하게 몇 개만)
TEST_CASES = [
    # (메시지, 예상 의도)
    ("일주일 식단표 만들어줘", "meal_plan"),
    ("닭가슴살 레시피 알려줘", "recipe_search"),
    ("강남역 근처 맛집 추천", "place_search"),
    ("캘린더에 저장해줘", "calendar_save"),
    ("안녕하세요", "general"),
]

async def test_intent_classifier():
    """IntentClassifier 직접 테스트"""
    
    print("="*80)
    print("의도분류 간단 테스트 시작")
    print("="*80)
    
    # 1. IntentClassifier 초기화
    print("\n[1단계] IntentClassifier 초기화")
    from app.core.intent_classifier import IntentClassifier
    
    classifier = IntentClassifier()
    
    if classifier.llm is None:
        print("❌ LLM이 None입니다. 초기화 실패!")
        return
    else:
        print("✅ IntentClassifier 초기화 성공")
        print(f"   - LLM 객체: {type(classifier.llm)}")
    
    # 2. LLM 직접 호출 테스트
    print("\n[2단계] LLM 직접 호출 테스트")
    from langchain.schema import HumanMessage
    from app.prompts.chat.intent_classification import get_intent_prompt
    
    test_message = "일주일 식단표 만들어줘"
    prompt = get_intent_prompt(test_message)
    
    print(f"   테스트 메시지: {test_message}")
    print(f"   프롬프트 길이: {len(prompt)}자")
    print(f"   프롬프트 미리보기 (처음 200자):\n{prompt[:200]}...\n")
    
    try:
        response = await classifier.llm.ainvoke([HumanMessage(content=prompt)])
        print(f"✅ LLM 호출 성공")
        print(f"   응답 타입: {type(response)}")
        print(f"   응답 길이: {len(response.content)}자")
        print(f"   응답 내용:\n{response.content}\n")
    except Exception as e:
        print(f"❌ LLM 호출 실패: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. IntentClassifier.classify() 테스트
    print("\n[3단계] IntentClassifier.classify() 메서드 테스트")
    
    for idx, (message, expected_intent) in enumerate(TEST_CASES):
        print(f"\n--- 테스트 {idx+1}/{len(TEST_CASES)} ---")
        print(f"메시지: {message}")
        print(f"예상 의도: {expected_intent}")
        
        try:
            result = await classifier.classify(message, context="")
            
            actual_intent = result["intent"].value if hasattr(result["intent"], "value") else result["intent"]
            confidence = result.get("confidence", 0.0)
            method = result.get("method", "unknown")
            reasoning = result.get("reasoning", "")
            
            print(f"실제 의도: {actual_intent}")
            print(f"신뢰도: {confidence:.2f}")
            print(f"방법: {method}")
            if reasoning:
                print(f"추론: {reasoning}")
            
            if actual_intent == expected_intent:
                print("✅ 정답!")
            else:
                print(f"❌ 오답! (예상: {expected_intent}, 실제: {actual_intent})")
                
        except Exception as e:
            print(f"❌ 분류 실패: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("테스트 완료")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_intent_classifier())

