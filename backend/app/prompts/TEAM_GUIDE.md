# 🚀 프롬프트 공통 템플릿 시스템 사용 가이드

## 📋 개요

이제 모든 프롬프트는 공통 템플릿 시스템을 사용합니다. 이 가이드를 통해 새로운 시스템을 쉽게 이해하고 사용할 수 있습니다.

## 🎯 왜 이 시스템을 도입했나요?

### ❌ 기존 문제점
```python
# 각 프롬프트 파일마다 동일한 규칙이 중복됨
# chat/general_chat.py
마크다운 포맷팅 규칙:
- 번호 목록 사용 시: "1. 제목:" (번호와 제목 사이에 공백 없음)
- 하위 목록은 바로 다음 줄에: "- 항목1"

# restaurant/search_failure.py  
마크다운 포맷팅 규칙:
- 번호 목록 사용 시: "1. 제목:" (번호와 제목 사이에 공백 없음)
- 하위 목록은 바로 다음 줄에: "- 항목1"

# meal/recipe_response.py
마크다운 포맷팅 규칙:
- 번호 목록 사용 시: "1. 제목:" (번호와 제목 사이에 공백 없음)
- 하위 목록은 바로 다음 줄에: "- 항목1"
```

### ✅ 개선된 방식
```python
# 공통 템플릿에서 한 번만 정의
from app.prompts.shared.common_templates import create_standard_prompt

# 간단하게 사용
PROMPT = create_standard_prompt(_base_prompt)
```

## 🛠️ 기본 사용법

### 1. 새로운 프롬프트 만들기

#### Step 1: 기본 프롬프트 작성
```python
# app/prompts/chat/my_new_prompt.py
from app.prompts.shared.common_templates import create_standard_prompt

# 기본 프롬프트만 작성 (공통 규칙은 자동 적용됨)
_base_prompt = """
사용자 질문에 답변해주세요.

질문: {message}
사용자 정보: {user_info}

특별한 요구사항:
- 냥체로 답변해주세요
- 300자 이내로 작성해주세요
"""

# 공통 템플릿 적용 (마크다운 규칙, 가이드라인 등 자동 포함)
MY_NEW_PROMPT = create_standard_prompt(_base_prompt)
```

#### Step 2: 사용하기
```python
# 다른 파일에서 사용
from app.prompts.chat.my_new_prompt import MY_NEW_PROMPT

# 프롬프트 사용
formatted_prompt = MY_NEW_PROMPT.format(
    message="키토 식단 추천해줘",
    user_info="초보자"
)
```

### 2. 기존 프롬프트 수정하기

#### Before (기존 방식)
```python
# ❌ 이렇게 하지 마세요
OLD_PROMPT = """
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
```

#### After (새로운 방식)
```python
# ✅ 이렇게 하세요
from app.prompts.shared.common_templates import create_standard_prompt

_base_prompt = """
질문: {message}

특별한 요구사항:
- 냥체로 답변해주세요
"""

NEW_PROMPT = create_standard_prompt(_base_prompt)
```

## 🎨 고급 사용법

### 1. 선택적 요소 사용

```python
from app.prompts.shared.common_templates import (
    create_standard_prompt,
    add_markdown_formatting,
    add_response_guidelines,
    add_friendly_tone
)

# 마크다운 규칙만 추가하고 싶을 때
prompt = add_markdown_formatting(_base_prompt)

# 가이드라인만 추가하고 싶을 때
prompt = add_response_guidelines(_base_prompt)

# 여러 요소 조합
prompt = _base_prompt
prompt = add_markdown_formatting(prompt)
prompt = add_friendly_tone(prompt)
```

### 2. 커스터마이징

```python
# 특정 요소만 포함하고 싶을 때
PROMPT = create_standard_prompt(
    _base_prompt,
    include_markdown=True,      # 마크다운 규칙 포함
    include_guidelines=False,   # 기본 가이드라인 제외
    include_tone=True          # 친근한 톤 포함
)
```

### 3. 새로운 공통 요소 추가

```python
# common_templates.py에 새로운 함수 추가
def add_emoji_guidelines(prompt: str) -> str:
    emoji_guide = """
이모지 사용 가이드:
- 적절한 이모지를 사용하여 친근함을 표현하세요
- 과도한 이모지 사용은 피하세요
"""
    return f"{prompt}\n\n{emoji_guide}"

# 사용
prompt = add_emoji_guidelines(_base_prompt)
```

## 📚 실제 예시들

### 1. 채팅 프롬프트
```python
# app/prompts/chat/example_chat.py
from app.prompts.shared.common_templates import create_standard_prompt

_base_chat_prompt = """
사용자와 대화하세요.

사용자 메시지: {message}
사용자 프로필: {profile}

특별한 처리:
- 인사말에는 따뜻하게 응답
- 질문에는 구체적으로 답변
- 감사 인사에는 격려로 응답
"""

CHAT_PROMPT = create_standard_prompt(_base_chat_prompt)
```

### 2. 레시피 프롬프트
```python
# app/prompts/meal/example_recipe.py
from app.prompts.shared.common_templates import create_standard_prompt

_base_recipe_prompt = """
레시피를 추천해주세요.

요청: {message}
재료: {ingredients}

형식:
## 🍽️ 추천 레시피
### 📋 재료
### 👨‍🍳 조리법
### 📊 영양 정보
"""

RECIPE_PROMPT = create_standard_prompt(_base_recipe_prompt)
```

### 3. 식당 검색 프롬프트
```python
# app/prompts/restaurant/example_place.py
from app.prompts.shared.common_templates import create_standard_prompt

_base_place_prompt = """
식당을 추천해주세요.

요청: {message}
위치: {location}
검색 결과: {results}

추가 요구사항:
- 키토 점수 높은 식당 우선
- 거리 정보 포함
- 주문 팁 제공
"""

PLACE_PROMPT = create_standard_prompt(_base_place_prompt)
```

## 🔧 문제 해결

### Q1: 기존 프롬프트가 작동하지 않아요
```python
# ❌ 잘못된 import
from app.prompts.shared.common_templates import MARKDOWN_FORMATTING_RULES

# ✅ 올바른 import
from app.prompts.shared.common_templates import create_standard_prompt
```

### Q2: 공통 규칙을 변경하고 싶어요
```python
# common_templates.py 파일을 수정하세요
# 모든 프롬프트가 자동으로 업데이트됩니다
```

### Q3: 특정 프롬프트에서만 다른 규칙을 사용하고 싶어요
```python
# 커스터마이징 옵션 사용
PROMPT = create_standard_prompt(
    _base_prompt,
    include_markdown=False,  # 마크다운 규칙 제외
    include_guidelines=True  # 가이드라인만 포함
)
```

## 📋 체크리스트

새로운 프롬프트를 만들 때 확인하세요:

- [ ] `from app.prompts.shared.common_templates import create_standard_prompt` import 했나요?
- [ ] `_base_prompt` 변수명을 사용했나요?
- [ ] `create_standard_prompt(_base_prompt)`로 프롬프트를 생성했나요?
- [ ] 공통 규칙(마크다운, 가이드라인 등)을 수동으로 추가하지 않았나요?
- [ ] 특별한 요구사항만 `_base_prompt`에 작성했나요?

## 🎉 장점 요약

1. **코드 중복 제거**: 동일한 규칙을 여러 파일에 반복 작성할 필요 없음
2. **일관성 보장**: 모든 프롬프트에서 동일한 포맷팅 규칙 적용
3. **유지보수 용이**: 공통 규칙 변경 시 한 곳만 수정
4. **개발 속도 향상**: 새로운 프롬프트 작성이 더 간단해짐
5. **팀 협업 개선**: 모든 팀원이 동일한 패턴으로 프롬프트 작성

## 🆘 도움이 필요하시면

- 이 가이드를 다시 읽어보세요
- 기존 프롬프트 파일들을 참고하세요
- 팀원들에게 질문하세요

**Happy Coding! 🚀**
