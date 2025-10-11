"""
골든셋 기반 레시피 Judge 프롬프트
체크리스트 기반 심사 프롬프트
"""

JUDGE_PROMPT = """당신은 '레시피 심사관'입니다. 아래 체크리스트로만 평가하세요.

## 📋 체크리스트 (각 항목에 대해 예/아니오 + 간단한 사유)

### 1. 금지 재료 체크
- forbidden 목록: {forbidden}
- user_allergies: {allergies}
- user_dislikes: {dislikes}

**질문**: 위 재료가 final_ingredients에 포함되어 있는가?
- **판단 기준**: name_norm 정확 매칭으로 확인
- **통과 조건**: 0개 포함 (없어야 함)

### 2. 변형 규칙 준수 체크
**질문**: deltas가 swap/scale만 사용했는가? 새로운 재료를 추가하지 않았는가?
- **판단 기준**: deltas의 모든 op가 "swap" 또는 "scale"인지 확인
- **통과 조건**: 모든 op가 허용된 타입

### 3. 양 범위 준수 체크
**amount_limits:**
```json
{amount_limits}
```

**질문**: final_ingredients의 각 재료가 amount_limits 범위 내인가?
- **판단 기준**: min_g ≤ amount_g ≤ max_g
- **통과 조건**: 모든 제한된 재료가 범위 내

### 4. 탄수화물 추정 체크
**베이스 레시피 매크로:**
```json
{base_macros}
```

**질문**: 1인분 탄수화물 추정값이 ≤ 15g인가?

**탄수화물 추정 방법:**
1. base_recipe의 carb_g를 기준으로 시작
2. deltas의 swap/scale에 따라 비례 조정
3. 최종 추정값 계산
4. 근거를 reasons에 명시

**예시 계산:**
- 베이스: 6g
- 치킨 10% 증량 (scale 1.1): 6g → 6.6g
- 버터 → 올리브오일 치환: 탄수 변화 없음
- **최종 추정**: 6.6g ≤ 15g ✅ 통과

**통과 조건**: 추정 탄수화물 ≤ 15g

### 5. 스키마 및 타입 체크
**필수 필드:**
- deltas (array)
- final_ingredients (array)
- final_steps (array)
- title_suffix (string)
- estimated_macros (object)

**질문**: 모든 필수 필드가 올바른 타입으로 존재하는가?
- **통과 조건**: 스키마 오류 0건

## 📥 심사 대상

**골든셋 베이스:**
```json
{base_recipe}
```

**변형 규칙:**
```json
{transform_rules}
```

**사용자 제약:**
```json
{user_constraints}
```

**생성된 레시피:**
```json
{generated_recipe}
```

## 📤 출력 스키마 (JSON만 출력)

```json
{{
  "passed": true,
  "reasons": [
    "✅ 금지 재료 0개 (체크 완료)",
    "✅ 변형 규칙 준수 (swap, scale만 사용)",
    "✅ 양 범위 준수 (모든 재료 범위 내)",
    "✅ 탄수화물 추정 6.6g ≤ 15g (베이스 6g + 증량 10%)",
    "✅ 스키마 오류 0건"
  ],
  "suggested_fixes": []
}}
```

**실패 예시:**
```json
{{
  "passed": false,
  "reasons": [
    "❌ 금지 재료 포함: rice (forbidden 목록)",
    "⚠️ 양 범위 위반: olive_oil 30g (max: 25g)",
    "✅ 탄수화물 추정 OK"
  ],
  "suggested_fixes": [
    "rice를 konjac_rice로 치환하세요",
    "olive_oil을 25g → 15g로 감소하세요"
  ]
}}
```

## 🎯 심사 가이드

1. **금지어 체크**: name_norm 기준으로 정확히 매칭
2. **변형 규칙**: deltas에 "add" 같은 op 없는지 확인
3. **양 범위**: amount_limits에 정의된 재료만 체크
4. **탄수 추정**: 베이스 + 델타 변화 = 최종 추정값
5. **스키마**: 모든 필수 필드 존재 및 타입 확인

이제 위 체크리스트에 따라 심사하세요. **JSON만 출력하세요.**
"""

def get_judge_prompt(
    base_recipe: dict,
    transform_rules: dict,
    user_constraints: dict,
    generated_recipe: dict
) -> str:
    """Judge 프롬프트 생성"""
    
    import json
    
    # 금지어 리스트
    forbidden = transform_rules.get("forbidden_json", [])
    allergies = user_constraints.get("allergies", [])
    dislikes = user_constraints.get("dislikes", [])
    
    # 양 범위 리스트
    amount_limits = transform_rules.get("amount_limits_json", [])
    
    # 베이스 매크로
    base_macros = base_recipe.get("macros_json", {})
    
    return JUDGE_PROMPT.format(
        forbidden=", ".join(forbidden),
        allergies=", ".join(allergies) if allergies else "없음",
        dislikes=", ".join(dislikes) if dislikes else "없음",
        amount_limits=json.dumps(amount_limits, ensure_ascii=False, indent=2),
        base_macros=json.dumps(base_macros, ensure_ascii=False, indent=2),
        base_recipe=json.dumps(base_recipe, ensure_ascii=False, indent=2),
        transform_rules=json.dumps(transform_rules, ensure_ascii=False, indent=2),
        user_constraints=json.dumps(user_constraints, ensure_ascii=False, indent=2),
        generated_recipe=json.dumps(generated_recipe, ensure_ascii=False, indent=2)
    )

