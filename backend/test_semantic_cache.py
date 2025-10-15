"""
시맨틱 캐시 테스트 스크립트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.semantic_cache import semantic_cache_service


async def test_semantic_cache():
    """시맨틱 캐시 기본 기능 테스트"""
    
    print("🧪 시맨틱 캐시 테스트 시작")
    
    # 테스트 데이터
    test_message = "7일 식단표 만들어줘"
    user_id = "test_user_123"
    model_ver = "meal_planner_gemini-2.5-flash"
    opts_hash = "7_1800_30_0_0"
    test_answer = "7일 키토 식단표를 생성해드릴게요!"
    test_meta = {
        "route": "meal_plan",
        "days": 7,
        "kcal_target": 1800,
        "carbs_max": 30
    }
    
    try:
        # 1. 시맨틱 캐시 저장 테스트
        print("\n1️⃣ 시맨틱 캐시 저장 테스트")
        save_result = await semantic_cache_service.save_semantic_cache(
            test_message, user_id, model_ver, opts_hash, test_answer, test_meta
        )
        print(f"   저장 결과: {'✅ 성공' if save_result else '❌ 실패'}")
        
        # 2. 시맨틱 캐시 조회 테스트 (정확한 메시지)
        print("\n2️⃣ 시맨틱 캐시 조회 테스트 (정확한 메시지)")
        lookup_result = await semantic_cache_service.semantic_lookup(
            test_message, user_id, model_ver, opts_hash
        )
        print(f"   조회 결과: {'✅ 히트' if lookup_result else '❌ 미스'}")
        if lookup_result:
            print(f"   응답 내용: {lookup_result[:50]}...")
        
        # 3. 시맨틱 캐시 조회 테스트 (유사한 메시지)
        print("\n3️⃣ 시맨틱 캐시 조회 테스트 (유사한 메시지)")
        similar_messages = [
            "7일 식단표 이러면",
            "일주일 식단 만들어줘",
            "7일치 식단표",
            "키토 7일 식단"
        ]
        
        for similar_msg in similar_messages:
            lookup_result = await semantic_cache_service.semantic_lookup(
                similar_msg, user_id, model_ver, opts_hash
            )
            print(f"   '{similar_msg}': {'✅ 히트' if lookup_result else '❌ 미스'}")
        
        # 4. 텍스트 정규화 테스트
        print("\n4️⃣ 텍스트 정규화 테스트")
        test_texts = [
            "7일 식단표 만들어줘",
            "7일 식단표 이러면",
            "일주일 식단 만들어줘",
            "키토 7일 식단표 이러면"
        ]
        
        for text in test_texts:
            normalized = semantic_cache_service._normalize_text(text)
            print(f"   '{text}' → '{normalized}'")
        
        print("\n✅ 시맨틱 캐시 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_semantic_cache())
