"""
프롬프트 공통 템플릿 사용 예제
팀원들이 참고할 수 있는 실제 사용 예시들
"""

from app.prompts.shared.common_templates import (
    create_standard_prompt,
    add_markdown_formatting,
    add_response_guidelines,
    add_keto_expert_role,
    add_friendly_tone
)

# ========================================
# 예제 1: 기본 사용법 (가장 많이 사용)
# ========================================

def example_basic_usage():
    """기본 사용법 예제"""
    
    # 기본 프롬프트 정의 (공통 규칙은 자동 적용됨)
    _base_prompt = """
    사용자 질문에 답변해주세요.
    
    질문: {message}
    사용자 정보: {user_info}
    
    특별한 요구사항:
    - 냥체로 답변해주세요
    - 300자 이내로 작성해주세요
    """
    
    # 공통 템플릿 적용 (마크다운 규칙, 가이드라인 등 자동 포함)
    BASIC_PROMPT = create_standard_prompt(_base_prompt)
    
    return BASIC_PROMPT

# ========================================
# 예제 2: 선택적 요소 사용
# ========================================

def example_selective_usage():
    """선택적 요소 사용 예제"""
    
    _base_prompt = """
    키토 식단에 대해 설명해주세요.
    
    질문: {message}
    """
    
    # 마크다운 규칙만 추가
    markdown_only_prompt = add_markdown_formatting(_base_prompt)
    
    # 가이드라인만 추가
    guidelines_only_prompt = add_response_guidelines(_base_prompt)
    
    # 여러 요소 조합
    custom_prompt = _base_prompt
    custom_prompt = add_markdown_formatting(custom_prompt)
    custom_prompt = add_friendly_tone(custom_prompt)
    
    return {
        "markdown_only": markdown_only_prompt,
        "guidelines_only": guidelines_only_prompt,
        "custom": custom_prompt
    }

# ========================================
# 예제 3: 커스터마이징 옵션
# ========================================

def example_customization():
    """커스터마이징 옵션 예제"""
    
    _base_prompt = """
    식당을 추천해주세요.
    
    요청: {message}
    위치: {location}
    """
    
    # 마크다운 규칙은 포함하되, 기본 가이드라인은 제외
    custom_prompt_1 = create_standard_prompt(
        _base_prompt,
        include_markdown=True,
        include_guidelines=False,
        include_tone=True
    )
    
    # 모든 공통 요소 제외 (완전 커스텀)
    custom_prompt_2 = create_standard_prompt(
        _base_prompt,
        include_markdown=False,
        include_guidelines=False,
        include_tone=False
    )
    
    return {
        "partial_common": custom_prompt_1,
        "no_common": custom_prompt_2
    }

# ========================================
# 예제 4: 실제 사용 시나리오
# ========================================

def example_real_scenarios():
    """실제 사용 시나리오 예제들"""
    
    # 시나리오 1: 채팅 프롬프트
    _chat_prompt = """
    사용자와 대화하세요.
    
    사용자 메시지: {message}
    사용자 프로필: {profile}
    
    특별한 처리:
    - 인사말에는 따뜻하게 응답
    - 질문에는 구체적으로 답변
    - 감사 인사에는 격려로 응답
    """
    CHAT_PROMPT = create_standard_prompt(_chat_prompt)
    
    # 시나리오 2: 레시피 프롬프트
    _recipe_prompt = """
    레시피를 추천해주세요.
    
    요청: {message}
    재료: {ingredients}
    
    형식:
    ## 🍽️ 추천 레시피
    ### 📋 재료
    ### 👨‍🍳 조리법
    ### 📊 영양 정보
    """
    RECIPE_PROMPT = create_standard_prompt(_recipe_prompt)
    
    # 시나리오 3: 식당 검색 프롬프트
    _place_prompt = """
    식당을 추천해주세요.
    
    요청: {message}
    위치: {location}
    검색 결과: {results}
    
    추가 요구사항:
    - 키토 점수 높은 식당 우선
    - 거리 정보 포함
    - 주문 팁 제공
    """
    PLACE_PROMPT = create_standard_prompt(_place_prompt)
    
    return {
        "chat": CHAT_PROMPT,
        "recipe": RECIPE_PROMPT,
        "place": PLACE_PROMPT
    }

# ========================================
# 예제 5: 기존 프롬프트 마이그레이션
# ========================================

def example_migration():
    """기존 프롬프트를 새 시스템으로 마이그레이션하는 예제"""
    
    # ❌ 기존 방식 (이렇게 하지 마세요)
    old_style_prompt = """
    키토 식단 전문가로서 답변해주세요.
    
    질문: {message}
    
    답변 가이드라인:
    1. 한국어로 자연스럽게 답변
    2. 키토 식단의 특성을 고려한 조언 포함
    3. 구체적이고 실용적인 정보 제공
    4. 200-300자 내외로 간결하게
    
    마크다운 포맷팅 규칙:
    - 번호 목록 사용 시: "1. 제목:" (번호와 제목 사이에 공백 없음)
    - 하위 목록은 바로 다음 줄에: "- 항목1"
    - 예시:
      1. 곡물류:
      - 쌀, 밀, 보리 등
    
    친근하고 격려하는 톤으로 답변해주세요.
    """
    
    # ✅ 새로운 방식 (이렇게 하세요)
    _base_prompt = """
    질문: {message}
    
    특별한 요구사항:
    - 냥체로 답변해주세요
    - 300자 이내로 작성해주세요
    """
    new_style_prompt = create_standard_prompt(_base_prompt)
    
    return {
        "old_style": old_style_prompt,
        "new_style": new_style_prompt
    }

# ========================================
# 예제 6: 테스트 및 디버깅
# ========================================

def example_testing():
    """테스트 및 디버깅 예제"""
    
    _base_prompt = """
    테스트용 프롬프트입니다.
    
    입력: {input}
    """
    
    # 프롬프트 생성
    test_prompt = create_standard_prompt(_base_prompt)
    
    # 프롬프트 테스트
    test_input = {
        "input": "키토 식단이 뭐야?"
    }
    
    # 실제 사용 예시
    formatted_prompt = test_prompt.format(**test_input)
    
    print("생성된 프롬프트:")
    print(formatted_prompt)
    
    return formatted_prompt

# ========================================
# 실행 예제
# ========================================

if __name__ == "__main__":
    print("🚀 프롬프트 공통 템플릿 사용 예제")
    print("=" * 50)
    
    # 기본 사용법
    print("\n1. 기본 사용법:")
    basic_prompt = example_basic_usage()
    print(basic_prompt[:200] + "...")
    
    # 선택적 사용법
    print("\n2. 선택적 사용법:")
    selective_prompts = example_selective_usage()
    print("마크다운만:", selective_prompts["markdown_only"][:100] + "...")
    
    # 커스터마이징
    print("\n3. 커스터마이징:")
    custom_prompts = example_customization()
    print("부분 공통:", custom_prompts["partial_common"][:100] + "...")
    
    # 실제 시나리오
    print("\n4. 실제 시나리오:")
    real_prompts = example_real_scenarios()
    print("채팅 프롬프트:", real_prompts["chat"][:100] + "...")
    
    print("\n✅ 모든 예제가 성공적으로 실행되었습니다!")
