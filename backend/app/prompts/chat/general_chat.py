"""
일반 채팅용 기본 프롬프트
팀원들이 복사하여 개인화할 수 있는 템플릿
"""

from app.prompts.shared.common_templates import create_standard_prompt

# 기본 프롬프트 (초고속 응답용)
_base_prompt = """
키토 전문가로서 간단히 답변해주세요.

질문: {message}
프로필: {profile_context}

형식: 마크다운, 이모지 사용, 간결하게
"""

GENERAL_CHAT_PROMPT = create_standard_prompt(_base_prompt)  # common_templates 적용

# Chat Agent의 기본 프롬프트 (agent 파일에서 분리됨)
DEFAULT_CHAT_PROMPT = GENERAL_CHAT_PROMPT

# 대안 프롬프트 (PROMPT로도 접근 가능)
PROMPT = GENERAL_CHAT_PROMPT
