# 🎯 골든셋 기반 레시피 검증 시스템 구현 가이드

## 📋 개요

RAG 실패시 AI가 생성하는 레시피를 **골든셋(Golden Set) 기반 변형 + 이중 LLM 검증**으로 안전하게 생성하는 시스템입니다.

### ✅ 구현 완료 항목

- [x] 데이터베이스 스키마 (4개 테이블)
- [x] 골든셋 데이터 30개 (5 카테고리 × 6개)
- [x] 재료 정규화 (40개 재료)
- [x] Generator 프롬프트 (swap/scale만 허용)
- [x] Judge 프롬프트 (체크리스트 기반)
- [x] RecipeValidator 서비스
- [x] MealPlannerAgent 통합
- [x] 자동 재시도 로직 (최대 3회)
- [x] DB 로깅 및 저장

### ⏳ 다음 단계

- [ ] 테스트 케이스 작성 (pytest)
- [ ] 성능 최적화 (캐싱, 타임아웃)
- [ ] 모니터링 대시보드

---

## 🚀 빠른 시작

### 1. 데이터베이스 마이그레이션

```powershell
# Supabase SQL Editor에서 실행
# backend/migrations/recipe_validation_schema.sql 복사 실행

# 골든셋 데이터 삽입
# backend/data/golden_recipes_seed.sql 복사 실행
```

### 2. 확인

```sql
-- 테이블 확인
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('golden_recipes', 'transform_rules', 'generated_recipes', 'ingredient_normalization');

-- 데이터 확인
SELECT COUNT(*) FROM golden_recipes WHERE is_active = true;  -- 30개
SELECT COUNT(*) FROM ingredient_normalization;  -- 40개
```

### 3. 사용 예시

```python
from app.agents.meal_planner import MealPlannerAgent

# MealPlannerAgent 생성
planner = MealPlannerAgent()

# 식단 생성 (자동으로 골든셋 검증 적용)
meal_plan = await planner.generate_meal_plan(
    days=7,
    kcal_target=1800,
    carbs_max=30,
    allergies=["새우"],
    dislikes=["브로콜리"],
    user_id="user_123"
)

# RAG 실패시 _generate_llm_meal이 자동으로 골든셋 검증 사용
```

---

## 📊 시스템 아키텍처

```
사용자 요청
    ↓
MealPlannerAgent
    ↓
[RAG 검색 시도]
    ↓
  실패시
    ↓
RecipeValidator
    ↓
1. 골든셋 선택 (태그 기반)
    ↓
2. Generator LLM (swap/scale만 허용)
    ↓
3. Judge LLM (체크리스트 심사)
    ↓
  통과?
    ├─ Yes → DB 저장 → 사용자에게 반환
    └─ No → suggested_fixes 반영 → 재시도 (최대 3회)
```

---

## 🗂️ 파일 구조

```
backend/
├── migrations/
│   ├── recipe_validation_schema.sql       # 테이블 스키마
│   └── README_RECIPE_VALIDATION.md         # 마이그레이션 가이드
├── data/
│   └── golden_recipes_seed.sql             # 골든셋 30개 + 재료 40개
├── app/
│   ├── domains/recipe/
│   │   └── services/
│   │       └── recipe_validator.py         # 핵심 검증 서비스
│   ├── prompts/meal/
│   │   ├── generator.py                    # Generator 프롬프트
│   │   └── judge.py                        # Judge 프롬프트
│   └── agents/
│       └── meal_planner.py                 # 통합 지점 (_generate_llm_meal)
└── RECIPE_VALIDATION_GUIDE.md              # 이 파일
```

---

## 🔧 핵심 컴포넌트

### 1. RecipeValidator 서비스

**위치**: `backend/app/domains/recipe/services/recipe_validator.py`

**주요 기능**:
- 골든셋 선택 (태그 기반 유사도)
- Generator LLM 호출 (swap/scale만 허용)
- Judge LLM 호출 (체크리스트 기반 심사)
- 자동 재시도 (최대 3회)
- DB 저장 (generated_recipes 테이블)

**사용 예시**:
```python
from app.domains.recipe.services.recipe_validator import RecipeValidator

validator = RecipeValidator()
result = await validator.generate_validated_recipe(
    meal_type="닭고기 요리",
    constraints={
        "allergies": ["새우"],
        "dislikes": ["브로콜리"],
        "kcal_target": 500,
        "carbs_max": 15
    },
    user_id="user_123"
)

if result["success"]:
    recipe = result["recipe"]
    print(f"검증 완료: {recipe['title']} (시도 {result['attempts']}회)")
else:
    print(f"검증 실패: {result['error']}")
```

### 2. Generator 프롬프트

**위치**: `backend/app/prompts/meal/generator.py`

**핵심 규칙**:
1. 재료 치환(swap)과 양 조정(scale)만 허용
2. amount_limits 범위 준수
3. forbidden 재료 절대 사용 금지
4. 1인분 기준, 5단계 이내
5. JSON 출력만

**출력 스키마**:
```json
{
  "deltas": [
    {"op": "swap", "from": "wheat_noodles", "to": "tofu_noodles"},
    {"op": "scale", "name_norm": "olive_oil", "factor": 0.8}
  ],
  "final_ingredients": [
    {"name_norm": "chicken_breast", "amount_g": 120}
  ],
  "final_steps": ["..."],
  "title_suffix": "(변형)",
  "estimated_macros": {"carb_g": 8, "protein_g": 35, "fat_g": 28, "kcal": 420}
}
```

### 3. Judge 프롬프트

**위치**: `backend/app/prompts/meal/judge.py`

**체크리스트**:
1. ✅ 금지 재료 체크 (forbidden + allergies + dislikes)
2. ✅ 변형 규칙 준수 (swap/scale만 사용)
3. ✅ 양 범위 준수 (amount_limits)
4. ✅ 탄수화물 추정 ≤ 15g
5. ✅ 스키마 오류 0건

**출력 스키마**:
```json
{
  "passed": true,
  "reasons": [
    "✅ 금지 재료 0개",
    "✅ 변형 규칙 준수",
    "✅ 양 범위 준수",
    "✅ 탄수화물 추정 8g ≤ 15g",
    "✅ 스키마 오류 0건"
  ],
  "suggested_fixes": []
}
```

### 4. MealPlannerAgent 통합

**위치**: `backend/app/agents/meal_planner.py`

**통합 지점**: `_generate_llm_meal()` 함수

**동작 방식**:
1. RecipeValidator로 검증 시도
2. 성공 시 → 검증된 레시피 반환
3. 실패 시 → 기존 방식(_generate_llm_meal_legacy)으로 폴백

**폴백 전략**:
```python
try:
    # 골든셋 검증 시도
    result = await validator.generate_validated_recipe(...)
    if result["success"]:
        return validated_recipe
    else:
        # 기존 방식으로 폴백
        return await self._generate_llm_meal_legacy(...)
except Exception:
    # 오류 시에도 기존 방식으로 폴백
    return await self._generate_llm_meal_legacy(...)
```

---

## 📈 모니터링 및 분석

### 1. 검증 성공률 확인

```sql
-- 전체 성공률
SELECT 
  COUNT(*) FILTER (WHERE passed = true) * 100.0 / COUNT(*) as success_rate,
  AVG(attempts) as avg_attempts
FROM generated_recipes;

-- 시도별 분포
SELECT attempts, COUNT(*) as count
FROM generated_recipes
GROUP BY attempts
ORDER BY attempts;
```

### 2. 실패 원인 분석

```sql
-- Judge 실패 사유 분석
SELECT 
  judge_report_json->>'reasons' as fail_reasons,
  COUNT(*) as count
FROM generated_recipes
WHERE passed = false
GROUP BY judge_report_json->>'reasons'
ORDER BY count DESC
LIMIT 10;
```

### 3. 응답 시간 분석

```sql
-- 평균/최대/최소 응답 시간
SELECT 
  AVG(response_time_ms) as avg_ms,
  MAX(response_time_ms) as max_ms,
  MIN(response_time_ms) as min_ms,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) as median_ms
FROM generated_recipes;
```

### 4. 골든셋 사용 빈도

```sql
-- 가장 많이 사용된 골든셋 Top 10
SELECT 
  gr.title,
  COUNT(*) as usage_count
FROM generated_recipes gen
JOIN golden_recipes gr ON gen.base_recipe_id = gr.id
GROUP BY gr.title
ORDER BY usage_count DESC
LIMIT 10;
```

---

## 🧪 테스트 가이드

### 수동 테스트

1. **금지어 테스트**
   ```python
   result = await validator.generate_validated_recipe(
       meal_type="쌀밥 요리",  # "rice" 금지어 포함
       constraints={"allergies": [], "dislikes": []}
   )
   # 예상: rice → konjac_rice 치환 또는 다른 골든셋 선택
   ```

2. **양 범위 테스트**
   ```python
   # amount_limits: olive_oil 5-25g
   # 30g 요청시 Judge가 25g로 축소 제안 예상
   ```

3. **탄수화물 테스트**
   ```python
   # 탄수 15g 이하 확인
   assert result["recipe"]["macros"]["carb_g"] <= 15
   ```

### 자동 테스트 (pytest)

**TODO**: `backend/tests/test_recipe_validator.py` 작성

```python
# 예정된 테스트 케이스
- test_forbidden_ingredient_rejection
- test_amount_limits_enforcement
- test_carb_limit_check
- test_schema_validation
- test_retry_logic
```

---

## 🔧 트러블슈팅

### 1. "골든셋 레시피를 찾을 수 없습니다"

**원인**: 데이터베이스에 골든셋 데이터가 없음

**해결**:
```sql
-- 골든셋 데이터 확인
SELECT COUNT(*) FROM golden_recipes WHERE is_active = true;

-- 0개면 golden_recipes_seed.sql 실행
```

### 2. "LLM 초기화 실패"

**원인**: OPENAI_API_KEY 또는 GOOGLE_API_KEY가 설정되지 않음

**해결**:
```powershell
# .env 파일 확인
cat backend/.env

# 키 설정
OPENAI_API_KEY=sk-...
# 또는
GOOGLE_API_KEY=...
```

### 3. "JSON 파싱 오류"

**원인**: LLM이 JSON 형식이 아닌 응답 생성

**해결**: 프롬프트 끝에 "**JSON만 출력하세요.**" 강조 추가 (이미 적용됨)

### 4. "타임아웃"

**원인**: Generator 또는 Judge 호출이 너무 오래 걸림

**해결**:
```python
# RecipeValidator에서 타임아웃 조정
self.generator_timeout = 30  # 기본값
self.judge_timeout = 20  # 기본값
```

---

## 📝 다음 단계 (Phase 2)

### 1. 식단 구조 검증 (옵션)

`_plan_meal_structure()` 함수에 간단한 룰 기반 검증 추가:
- 금지 키워드 체크
- 키토 적합성 검증

### 2. 성능 최적화

- [ ] 캐싱: 동일한 meal_type + constraints 조합 캐싱 (10분)
- [ ] 병렬 처리: 여러 슬롯 동시 생성 (주의: API rate limit)
- [ ] 모델 최적화: Judge는 더 작은 모델 사용 고려

### 3. 골든셋 확장

- [ ] 월 10개씩 추가 (목표: 6개월 후 100개)
- [ ] 사용자 피드백 기반 개선
- [ ] 계절별 특화 레시피

---

## 📚 참고 자료

- **PRD 문서**: `식단 생성 검증 PRD.md`
- **골든셋 가이드**: `골든셋 생성 방법.md`
- **검증 로직**: `ai 식단 생성 검증 로직.md`
- **마이그레이션**: `backend/migrations/README_RECIPE_VALIDATION.md`

---

## 🎉 완료!

이제 RAG 실패시에도 **검증된 안전한 레시피**가 생성됩니다!

**핵심 메트릭 목표**:
- ✅ 금지어 위반률: **0%**
- ✅ 스키마 오류: **0건**
- ✅ 재시도 내 통과율: **≥90%**

