# ⚡ 프롬프트 공통 템플릿 빠른 참조

## 🚀 30초 빠른 시작

```python
# 1. Import 추가
from app.prompts.shared.common_templates import create_standard_prompt

# 2. 기본 프롬프트 작성
_base_prompt = """
질문: {message}
특별한 요구사항: 냥체로 답변해주세요
"""

# 3. 공통 템플릿 적용
PROMPT = create_standard_prompt(_base_prompt)
```

## 📋 자주 사용하는 패턴들

### 기본 패턴
```python
from app.prompts.shared.common_templates import create_standard_prompt

_base_prompt = """
질문: {message}
"""
PROMPT = create_standard_prompt(_base_prompt)
```

### 커스터마이징 패턴
```python
# 마크다운만 포함
PROMPT = create_standard_prompt(_base_prompt, include_guidelines=False)

# 모든 공통 요소 제외
PROMPT = create_standard_prompt(_base_prompt, include_markdown=False, include_guidelines=False, include_tone=False)
```

### 선택적 요소 추가
```python
from app.prompts.shared.common_templates import add_markdown_formatting, add_friendly_tone

prompt = add_markdown_formatting(_base_prompt)
prompt = add_friendly_tone(prompt)
```

## 🔧 문제 해결

| 문제 | 해결책 |
|------|--------|
| `create_standard_prompt is not defined` | `from app.prompts.shared.common_templates import create_standard_prompt` 추가 |
| 공통 규칙이 적용되지 않음 | `create_standard_prompt()` 사용했는지 확인 |
| 프롬프트가 너무 길어짐 | `_base_prompt`에서 공통 요소 제거 |
| 기존 프롬프트와 결과가 다름 | 공통 요소를 실수로 제거했는지 확인 |

## 📁 파일 구조

```
app/prompts/
├── shared/
│   ├── common_templates.py    # 공통 템플릿 정의
│   └── __init__.py           # 모듈 초기화
├── chat/
│   └── general_chat.py       # 채팅 프롬프트
├── meal/
│   └── recipe_response.py    # 레시피 프롬프트
├── restaurant/
│   └── search_failure.py     # 식당 프롬프트
└── examples/
    └── example_usage.py      # 사용 예제
```

## 🎯 체크리스트

새로운 프롬프트 만들 때:

- [ ] `from app.prompts.shared.common_templates import create_standard_prompt` import
- [ ] `_base_prompt` 변수명 사용
- [ ] 공통 요소(마크다운 규칙, 가이드라인 등) 수동 추가 안 함
- [ ] `create_standard_prompt(_base_prompt)` 사용
- [ ] 특별한 요구사항만 `_base_prompt`에 작성

## 📚 더 자세한 정보

- 📖 [팀 가이드](./TEAM_GUIDE.md) - 상세한 사용법
- 🔄 [마이그레이션 가이드](./MIGRATION_GUIDE.md) - 기존 프롬프트 변환
- 💻 [사용 예제](./examples/example_usage.py) - 실제 코드 예시
- 📁 [공통 템플릿](./shared/README.md) - 시스템 상세 설명

## 🆘 도움말

- 기존 프롬프트 파일들을 참고하세요
- `examples/example_usage.py`를 실행해보세요
- 팀원들에게 질문하세요

**Happy Coding! 🚀**
