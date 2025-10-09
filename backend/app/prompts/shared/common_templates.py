"""
공통 프롬프트 템플릿
모든 프롬프트에서 공통으로 사용되는 템플릿들을 중앙화 관리
"""

# 마크다운 포맷팅 규칙 (공통)
MARKDOWN_FORMATTING_RULES = """
마크다운 포맷팅 규칙:
- 번호 목록 사용 시: "1. 제목:" (번호와 제목 사이에 공백 없음)
- 하위 목록은 바로 다음 줄에: "- 항목1" (제목과 하위 목록 사이에 빈 줄 없음)
- 예시:
  1. 곡물류:
  - 쌀, 밀, 보리 등
  2. 단백질:
  - 고기, 생선, 계란 등
"""

# 기본 답변 가이드라인 (공통)
DEFAULT_RESPONSE_GUIDELINES = """
답변 가이드라인:
1. 한국어로 자연스럽게 답변
2. 키토 식단의 특성을 고려한 조언 포함
3. 구체적이고 실용적인 정보 제공
4. 200-300자 내외로 간결하고 이해하기 쉽게 답변
"""

# 개인화 규칙 (프로필이 있는 경우에만 적용)
PERSONALIZATION_RULES = """
개인화 규칙(프로필 정보가 있는 경우에만 적용):
- 사용자 알레르기 성분과 비선호 재료는 어떤 형태로도 언급·포함하지 마세요
- 필요 시 안전한 대체 재료를 제안하세요 (예: 견과류 → 해바라기씨 등)
- 프로필 정보가 없으면 일반적인 키토 친화적 조언만 제공하세요
"""

# 키토 전문가 역할 정의 (공통)
KETO_EXPERT_ROLE = "키토 식단 전문가로서"

# 친근한 톤 가이드라인 (공통)
FRIENDLY_TONE_GUIDE = "친근하고 격려하는 톤으로 답변해주세요."

# 프롬프트 조합 헬퍼 함수들
def add_markdown_formatting(prompt: str) -> str:
    """프롬프트에 마크다운 포맷팅 규칙 추가"""
    return f"{prompt}\n\n{MARKDOWN_FORMATTING_RULES}"

def add_response_guidelines(prompt: str) -> str:
    """프롬프트에 기본 답변 가이드라인 추가"""
    return f"{prompt}\n\n{DEFAULT_RESPONSE_GUIDELINES}\n\n{PERSONALIZATION_RULES}"

def add_keto_expert_role(prompt: str) -> str:
    """프롬프트에 키토 전문가 역할 추가"""
    return f"{KETO_EXPERT_ROLE} {prompt}"

def add_friendly_tone(prompt: str) -> str:
    """프롬프트에 친근한 톤 가이드 추가"""
    return f"{prompt}\n\n{FRIENDLY_TONE_GUIDE}"

def create_standard_prompt(base_prompt: str, include_markdown: bool = True, include_guidelines: bool = True, include_tone: bool = True) -> str:
    """표준 프롬프트 생성 (모든 공통 요소 포함)"""
    prompt = base_prompt
    
    if include_guidelines:
        prompt = add_response_guidelines(prompt)
    
    if include_markdown:
        prompt = add_markdown_formatting(prompt)
    
    if include_tone:
        prompt = add_friendly_tone(prompt)
    
    return prompt
