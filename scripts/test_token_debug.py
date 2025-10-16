"""
토큰 정보 디버깅을 위한 간단한 테스트 스크립트
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

import asyncio

async def test_token_info():
    from app.core.intent_classifier import IntentClassifier
    
    classifier = IntentClassifier()
    
    # 캐시 초기화
    if classifier.cache and hasattr(classifier.cache, 'redis'):
        try:
            keys = classifier.cache.redis.keys("intent_classify:*")
            if keys:
                classifier.cache.redis.delete(*keys)
                print(f"✅ {len(keys)}개의 캐시 키 삭제 완료\n")
        except Exception as e:
            print(f"⚠️  캐시 초기화 실패: {e}\n")
    
    # 키워드에 걸리지 않는 테스트 케이스 (LLM 호출 보장)
    test_message = "출근용 도시락 위주로 2주 식단"
    
    print(f"🔍 테스트 메시지: '{test_message}'")
    print("=" * 60)
    
    result = await classifier.classify(test_message, "")
    
    print("=" * 60)
    print(f"\n✅ 분류 결과:")
    print(f"   의도: {result.get('intent')}")
    print(f"   신뢰도: {result.get('confidence')}")
    print(f"   방법: {result.get('method')}")
    print(f"   토큰 정보: {result.get('token_usage')}")

if __name__ == "__main__":
    asyncio.run(test_token_info())

