"""
recipe_search 의도 분류만 빠르게 테스트
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

import asyncio

# recipe_search 테스트 케이스만
RECIPE_TEST_CASES = [
    "닭가슴살 수비드 최적 온도 알려줘",
    "에어프라이어 베이컨 칩 만드는 법",
    "콜리플라워 라이스 볶음밥 레시피",
    "두부 스테이크 겉바속촉 비법",
    "계란버터 스크램블 크리미하게",
    "아보카도 참치 샐러드 드레싱",
    "저탄수 김치볶음 밥 없이 조리법",
    "코코넛가루 팬케이크 레시피",
    "주키니 누들 알리오올리오",
    "당 없는 타르타르 소스 만들기",
    "키토 빵 없는 햄버거 볼 레시피",
    "노오븐 치즈케이크 저당 레시피",
    "버터 대신 올리브유 버전으로 바꿔줘",
    "버섯 크림수프(무루) 저탄 레시피",
    "오트는 제외, 대체 재료 추천",
]

async def test_recipe_intent():
    from app.core.intent_classifier import IntentClassifier
    
    classifier = IntentClassifier()
    
    correct = 0
    total = len(RECIPE_TEST_CASES)
    failed = []
    
    print(f"📋 Recipe Search 의도 분류 테스트 ({total}개)\n")
    print("=" * 60)
    
    for i, message in enumerate(RECIPE_TEST_CASES, 1):
        result = await classifier.classify(message, "")
        predicted = getattr(result["intent"], "value", result["intent"])
        
        is_correct = predicted == "recipe_search"
        symbol = "✓" if is_correct else "✗"
        
        print(f"[{i:2d}] {symbol} {message}")
        print(f"     분류: {predicted} (신뢰도: {result.get('confidence', 0):.2f})")
        
        if is_correct:
            correct += 1
        else:
            failed.append({
                "message": message,
                "predicted": predicted,
                "confidence": result.get("confidence", 0),
                "reasoning": result.get("reasoning", "")
            })
        print()
    
    print("=" * 60)
    print(f"정확도: {correct/total:.1%} ({correct}/{total})\n")
    
    if failed:
        print("❌ 실패 케이스:")
        print("=" * 60)
        for i, case in enumerate(failed, 1):
            print(f"\n[{i}] {case['message']}")
            print(f"    실제 분류: {case['predicted']}")
            print(f"    신뢰도: {case['confidence']:.2f}")
            if case['reasoning']:
                print(f"    추론: {case['reasoning']}")

if __name__ == "__main__":
    asyncio.run(test_recipe_intent())

