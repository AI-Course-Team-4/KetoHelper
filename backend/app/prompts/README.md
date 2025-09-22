# 🎯 Prompts (중앙집중화 프롬프트)

모든 도메인의 AI 프롬프트를 중앙에서 관리하는 폴더입니다.

## 📁 구조

```
prompts/
├── meal/              # 식단 관련 프롬프트
│   ├── generation.py      # 개별 레시피 생성
│   ├── structure.py       # 식단표 구조 계획
│   ├── notes.py          # 식단표 조언 생성
│   ├── single_recipe.py   # 단일 레시피 생성
│   └── fallback.py       # 폴백 프롬프트
├── chat/              # 채팅 관련 프롬프트
│   ├── general_chat.py        # 일반 채팅
│   ├── intent_classification.py   # 의도 분류
│   ├── memory_update.py       # 메모리 업데이트
│   ├── response_generation.py # 응답 생성
│   └── fallback.py           # 폴백 프롬프트
├── restaurant/        # 식당 관련 프롬프트
│   ├── recommendation.py     # 식당 추천
│   ├── search_improvement.py # 검색 개선
│   ├── search_failure.py     # 검색 실패 처리
│   └── fallback.py          # 폴백 프롬프트
└── shared/            # 공통 프롬프트
    └── fallback.py          # 전역 폴백
```

## 🎯 사용법

### 1. 기본 사용
```python
from app.prompts.meal.generation import MEAL_GENERATION_PROMPT
from app.prompts.chat.intent_classification import INTENT_CLASSIFICATION_PROMPT

# 개인화 프롬프트 사용
from app.prompts.meal.soobin_generation import SOOBIN_GENERATION_PROMPT

# 프롬프트 사용
prompt = SOOBIN_GENERATION_PROMPT.format(
    slot="아침",
    meal_type="오믈렛",
    constraints="저탄수화물"
)
```

### 2. 개인화 프롬프트 만들기
개인 맞춤 프롬프트를 만들려면:

1. 해당 도메인 폴더에 `작성자이름_purpose.py` 파일 생성
2. 기존 프롬프트를 복사하여 수정
3. `backend/config/personal_config.py`에서 설정 변경

```python
# prompts/meal/soobin_generation.py
SOOBIN_GENERATION_PROMPT = """
당신은 개인화된 키토 전문가입니다...
"""

# 하위 호환성을 위한 별칭
MEAL_GENERATION_PROMPT = SOOBIN_GENERATION_PROMPT
PROMPT = SOOBIN_GENERATION_PROMPT
```

## 📋 프롬프트 작성 가이드

### 1. 명명 규칙
- 파일명: `작성자명_purpose.py` (예: `soobin_generation.py`)
- 상수명: `작성자명_PURPOSE_PROMPT` (예: `SOOBIN_GENERATION_PROMPT`)

### 2. 포맷 변수
프롬프트에서 사용할 수 있는 공통 변수들:
- `{message}`: 사용자 메시지
- `{profile_context}`: 사용자 프로필 정보
- `{constraints}`: 제약 조건
- `{days}`: 일수 (식단표)

### 3. 프롬프트 구조
```python
"""
프롬프트 설명
용도와 사용 시나리오
"""

SOOBIN_GENERATION_PROMPT = """
명확하고 구체적인 지시사항...

입력:
- 변수1: {variable1}
- 변수2: {variable2}

출력 형식:
JSON/텍스트 형태로 원하는 결과...
"""

# 폴백 프롬프트 (선택사항)
SOOBIN_FALLBACK_PROMPT = """
기본 응답 프롬프트...
"""

# 하위 호환성을 위한 별칭
MEAL_GENERATION_PROMPT = SOOBIN_GENERATION_PROMPT
PROMPT = SOOBIN_GENERATION_PROMPT
```

## 🛠️ 유지보수

### 1. 프롬프트 업데이트
- 기존 프롬프트 수정 시 하위 호환성 고려
- 변경 사항은 주석으로 기록
- 테스트 후 배포

### 2. 새 프롬프트 추가
1. 적절한 도메인 폴더 선택
2. 파일 및 상수 명명 규칙 준수
3. 문서화 추가

### 3. 성능 최적화
- 토큰 수 최적화 (GPT API 비용 절약)
- 명확하고 간결한 지시사항
- 예시 포함으로 품질 향상

## 🔧 트러블슈팅

### Import 오류
```python
# ❌ 잘못된 경로
from meal.prompts.generation import PROMPT

# ✅ 올바른 경로
from app.prompts.meal.generation import MEAL_GENERATION_PROMPT
```

### 프롬프트 로딩 실패
프롬프트 파일이 로드되지 않을 때:
1. 파일 경로 확인
2. 문법 오류 확인
3. 폴백 프롬프트 사용

## 🎯 Best Practices

1. **명확성**: 프롬프트는 명확하고 구체적으로
2. **일관성**: 도메인 내에서 일관된 스타일 유지
3. **테스트**: 새 프롬프트는 충분히 테스트
4. **문서화**: 복잡한 프롬프트는 주석으로 설명
5. **버전 관리**: 중요한 변경사항은 Git으로 추적
