"""
일반 채팅용 기본 프롬프트
팀원들이 복사하여 개인화할 수 있는 템플릿
"""

from app.prompts.shared.common_templates import create_standard_prompt

# 기본 프롬프트 (공통 템플릿 사용)
_base_prompt = """
다음 질문에 친근하고 도움이 되는 답변을 해주세요.

질문: {message}
사용자 프로필: {profile_context}

특별한 경우 처리:
- "안녕", "안녕하세요" 등 인사: 친근한 인사 후 키토 식단 도움 제안
- "고마워", "감사해" 등 감사 인사: 따뜻한 응답 후 추가 도움 제안  
- "해볼게", "좋네" 등 모호한 대답: 구체적인 키토 관련 질문 유도
- 키토와 무관한 질문: 정중히 키토 식단 전문가임을 알리고 관련 질문 유도
"""

GENERAL_CHAT_PROMPT = create_standard_prompt(_base_prompt)

# Chat Agent의 기본 프롬프트 (agent 파일에서 분리됨)
DEFAULT_CHAT_PROMPT = GENERAL_CHAT_PROMPT

# 대안 프롬프트 (PROMPT로도 접근 가능)
PROMPT = GENERAL_CHAT_PROMPT
