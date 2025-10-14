"""
일반 채팅용 기본 프롬프트
팀원들이 복사하여 개인화할 수 있는 템플릿
"""

from app.prompts.shared.common_templates import create_standard_prompt

# 기본 프롬프트 (간결하고 실용적인 답변용)
_base_prompt = """
키토 전문가로서 간결하고 실용적으로 답변해주세요.

질문: {message}
프로필: {profile_context}

답변 형식:
- 핵심 내용 위주로 간결하게
- 구체적인 예시 포함
- 실용적인 조언 제공

**마크다운 형식 사용 (반드시 적용):**
- ## 제목 (섹션 구분)
- **굵은 글씨** (중요한 내용 강조)
- - 불릿 포인트 (목록)
- 1. 번호 목록 (단계별 설명)

형식: 마크다운, 이모지 사용, 300-500자 내외
"""

GENERAL_CHAT_PROMPT = create_standard_prompt(_base_prompt)  # common_templates 적용

# Chat Agent의 기본 프롬프트 (agent 파일에서 분리됨)
DEFAULT_CHAT_PROMPT = GENERAL_CHAT_PROMPT

# 대안 프롬프트 (PROMPT로도 접근 가능)
PROMPT = GENERAL_CHAT_PROMPT
