# 공통 프롬프트 템플릿

이 모듈은 모든 프롬프트에서 공통으로 사용되는 템플릿들을 중앙화하여 관리합니다.

## 🎯 목적

- **코드 중복 제거**: 마크다운 포맷팅 규칙, 답변 가이드라인 등이 여러 프롬프트에 중복으로 들어가는 문제 해결
- **일관성 유지**: 모든 프롬프트에서 동일한 포맷팅 규칙과 가이드라인 적용
- **유지보수성 향상**: 공통 규칙 변경 시 한 곳만 수정하면 모든 프롬프트에 반영

## 📁 구조

```
shared/
├── __init__.py              # 모듈 초기화
├── common_templates.py      # 공통 템플릿 정의
└── README.md               # 사용법 문서
```

## 🚀 사용법

### 1. 기본 사용법

```python
from app.prompts.shared.common_templates import create_standard_prompt

# 기본 프롬프트 정의
_base_prompt = """
사용자 질문에 답변해주세요.
질문: {message}
"""

# 표준 프롬프트 생성 (모든 공통 요소 포함)
PROMPT = create_standard_prompt(_base_prompt)
```

### 2. 선택적 사용법

```python
from app.prompts.shared.common_templates import (
    add_markdown_formatting,
    add_response_guidelines,
    add_keto_expert_role,
    add_friendly_tone
)

# 필요한 요소만 선택적으로 추가
prompt = "기본 프롬프트"
prompt = add_markdown_formatting(prompt)  # 마크다운 규칙만 추가
prompt = add_friendly_tone(prompt)        # 친근한 톤만 추가
```

### 3. 커스터마이징

```python
# 마크다운 규칙은 포함하되, 가이드라인은 제외
PROMPT = create_standard_prompt(
    _base_prompt,
    include_markdown=True,
    include_guidelines=False,
    include_tone=True
)
```

## 📋 포함되는 공통 요소

### 1. 마크다운 포맷팅 규칙
- 번호 목록: `1. 제목:` (공백 없음)
- 하위 목록: 바로 다음 줄에 `- 항목1`
- 예시 제공

### 2. 기본 답변 가이드라인
- 한국어로 자연스럽게 답변
- 키토 식단 특성 고려
- 구체적이고 실용적인 정보 제공
- 200-300자 내외로 간결하게

### 3. 키토 전문가 역할
- "키토 식단 전문가로서" 역할 정의

### 4. 친근한 톤 가이드
- "친근하고 격려하는 톤으로 답변해주세요"

## 🔧 수정 방법

공통 규칙을 변경하려면 `common_templates.py` 파일만 수정하면 됩니다:

```python
# 마크다운 규칙 변경 예시
MARKDOWN_FORMATTING_RULES = """
새로운 마크다운 포맷팅 규칙:
- 새로운 규칙 1
- 새로운 규칙 2
"""
```

모든 프롬프트가 자동으로 새로운 규칙을 사용하게 됩니다.

## ✅ 적용된 프롬프트들

- `chat/general_chat.py`
- `chat/fallback.py`
- `chat/response_generation.py`
- `restaurant/search_failure.py`
- `meal/recipe_response.py`

## 🎉 장점

1. **DRY 원칙**: Don't Repeat Yourself - 코드 중복 제거
2. **일관성**: 모든 프롬프트에서 동일한 규칙 적용
3. **유지보수성**: 한 곳에서 모든 규칙 관리
4. **확장성**: 새로운 공통 요소 쉽게 추가 가능
5. **가독성**: 프롬프트 파일이 더 간결하고 읽기 쉬움
