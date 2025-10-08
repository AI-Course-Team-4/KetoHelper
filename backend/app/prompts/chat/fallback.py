"""
Chat Agent 폴백 프롬프트들
프롬프트 파일 로딩이 실패했을 때 사용되는 최종 폴백
"""

from app.prompts.shared.common_templates import create_standard_prompt

# 일반 채팅 폴백 프롬프트 (공통 템플릿 사용)
_base_fallback_prompt = """
다음 질문에 친근하고 도움이 되는 답변을 해주세요.

질문: {message}
사용자 프로필: {profile_context}
"""

FALLBACK_GENERAL_CHAT_PROMPT = create_standard_prompt(_base_fallback_prompt)

# 의도 분류 폴백 프롬프트
FALLBACK_INTENT_CLASSIFICATION_PROMPT = """
사용자 메시지를 분석하여 의도를 분류하세요.

사용자 메시지: "{message}"

다음 JSON 형태로 응답하세요:
{
    "intent": "other",
    "slots": {}
}
"""

# 응답 생성 폴백 프롬프트
FALLBACK_RESPONSE_GENERATION_PROMPT = """
사용자 질문에 간단히 답변하세요.

질문: "{message}"
의도: {intent}

키토 식단 관련 기본 조언을 제공하거나, 도움이 필요하다고 안내해주세요.
"""

# 메모리 업데이트 폴백 프롬프트
FALLBACK_MEMORY_UPDATE_PROMPT = """
사용자 메시지에서 프로필 정보를 추출하세요.

메시지: "{message}"

JSON 형태로 응답하세요:
{
    "allergies": [],
    "dislikes": [],
    "goals_kcal": null,
    "goals_carbs_g": 20
}
"""
