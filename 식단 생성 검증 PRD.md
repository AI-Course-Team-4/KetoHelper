# KetoHelper — 골든셋(Whitelist) 변형 + 이중 LLM 심사 구현서 (v1)

> 팀 상황에 맞춰 **쉽게 시작**하고 **안전성/일관성**을 담보하는 방식으로 설계했습니다.
> 핵심: **⑥ 골든셋(Whitelist)에서만 변형 허용 + ⑦ 생성→심사 이중 LLM**.

---

## 0. 목표 & 범위

* **목표**: AI가 만든 식단/레시피가 **안전(금지재료 없음)**, **일관(템플릿 준수)**, **현실성(단계/도구 적절)**을 만족하도록 **자동 게이트**를 통과시킨다.
* **범위**:

  1. **골든셋**(검증된 30~100개 레시피) 준비
  2. **생성 LLM(Generator)**: 골든셋을 **치환/양조정**만으로 변형
  3. **심사 LLM(Judge)**: 체크리스트로 자동 심사(+자기수정 루프 ≤ 2회)
  4. **저장/로깅/간단한 평가**까지

---

## 1. 전체 흐름(High-level)

```mermaid
flowchart LR
  U[User Request] --> S[Selector: 골든셋 후보 Top-3]
  S --> G[Generator LLM\n(치환/양조정만)]
  G --> J[Judge LLM\n체크리스트 심사]
  J -->|Fail + fixes| G
  J -->|Pass| P[Persist to DB]
  P --> R[Response to User]
```

* **루프 제한**: Judge가 Fail이면 **최대 2회**까지 Generator가 수정 재시도.
* **Pass 조건**: 금지어 0건, 치환/양조정만, 양 범위 준수, 1인분 탄수 추정 ≤ 기준, 스키마/타입 오류 0건.

---

## 2. 데이터 모델 (PostgreSQL/Supabase)

### 2.1 테이블 구성

```sql
-- 1) 검증된 골든셋 레시피
CREATE TABLE IF NOT EXISTS golden_recipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  servings INTEGER NOT NULL DEFAULT 1,
  ingredients_json JSONB NOT NULL,   -- [{name_norm, amount_g}]
  steps_json JSONB NOT NULL,         -- ["...", "..."]
  tags TEXT[] DEFAULT '{}',
  macros_json JSONB,                 -- {carb_g, protein_g, fat_g, kcal}
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 2) 변형(치환/범위/금지) 규칙
CREATE TABLE IF NOT EXISTS transform_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  base_recipe_id UUID REFERENCES golden_recipes(id) ON DELETE CASCADE,
  swaps_json JSONB NOT NULL,         -- [{from, to, ratio}]
  amount_limits_json JSONB NOT NULL, -- [{name_norm, min_g, max_g}]
  forbidden_json JSONB NOT NULL,     -- ["sugar","honey","rice"...]
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 3) 생성 결과 + 심사 리포트(프로비넌스)
CREATE TABLE IF NOT EXISTS generated_recipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  base_recipe_id UUID REFERENCES golden_recipes(id) ON DELETE SET NULL,
  deltas_json JSONB NOT NULL,        -- [{op: "swap"|"scale", ...}]
  final_ingredients_json JSONB NOT NULL,
  final_steps_json JSONB NOT NULL,
  judge_report_json JSONB NOT NULL,  -- {passed, reasons[], suggested_fixes[]}
  passed BOOLEAN NOT NULL,
  model_gen TEXT,
  model_judge TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

> **Tip**: `name_norm`은 미리 정규화 규칙을 정해 통일(예: `olive_oil`, `tofu_noodles`).

### 2.2 시드/예시 JSON

**골든셋 예시**

```json
{
  "title": "버터치킨 샐러드",
  "servings": 1,
  "ingredients_json": [
    {"name_norm": "chicken_breast", "amount_g": 120},
    {"name_norm": "romaine_lettuce", "amount_g": 80},
    {"name_norm": "olive_oil", "amount_g": 15},
    {"name_norm": "butter", "amount_g": 10}
  ],
  "steps_json": ["닭 가슴살 굽기...", "채소 손질...", "드레싱..."],
  "tags": ["keto","high_protein"],
  "macros_json": {"carb_g": 6, "protein_g": 35, "fat_g": 28, "kcal": 430}
}
```

**변형 규칙 예시**

```json
{
  "base_recipe_id": "uuid",
  "swaps_json": [
    {"from": "wheat_noodles", "to": "tofu_noodles", "ratio": 1.0},
    {"from": "rice", "to": "konjac_rice", "ratio": 1.0}
  ],
  "amount_limits_json": [
    {"name_norm": "olive_oil", "min_g": 5, "max_g": 25},
    {"name_norm": "butter", "min_g": 5, "max_g": 15}
  ],
  "forbidden_json": ["sugar","honey","rice","wheat_flour","noodle_wheat"]
}
```

---

## 3. API 계약 (FastAPI 초안)

### 3.1 엔드포인트

* `GET /golden-recipes?query=&tags=&limit=10`
  간단 검색/필터(제목/태그)

* `POST /generate-from-golden`

  * **Body**

    ```json
    {
      "user_constraints": {
        "allergies": ["peanut"],
        "dislikes": ["cilantro"],
        "time_limit_min": 15,
        "tools": ["pan"]
      },
      "selection": {
        "by": "auto",    // "auto" | "id"
        "id": null,
        "prefer_tags": ["salad","chicken"]
      }
    }
    ```
  * **Response**

    ```json
    {
      "generated_id": "uuid",
      "title": "버터치킨 샐러드(변형)",
      "final_ingredients": [...],
      "final_steps": [...],
      "passed": true,
      "judge_report": {"passed": true, "reasons": [], "suggested_fixes": []}
    }
    ```

### 3.2 Pydantic 모델(발췌)

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Ingredient(BaseModel):
    name_norm: str
    amount_g: float

class UserConstraints(BaseModel):
    allergies: List[str] = []
    dislikes: List[str] = []
    time_limit_min: Optional[int] = None
    tools: List[str] = []

class Selection(BaseModel):
    by: Literal["auto","id"] = "auto"
    id: Optional[str] = None
    prefer_tags: List[str] = []

class GenerateRequest(BaseModel):
    user_constraints: UserConstraints
    selection: Selection
```

---

## 4. 프롬프트 (바로 복붙용)

### 4.1 Generator

```
당신은 '골든셋 변형 전용' 조리 어시스턴트입니다.
반드시 아래 제한만 수행하세요:
1) 재료 치환(swaps)과 양 조정(scale)만 허용. 새로운 재료 추가/임의 삭제 금지.
2) amount_limits 범위를 지켜라. forbidden 목록과 user_allergies/dislikes는 절대 포함하지 말라.
3) 1인분 기준. 단계는 5개 이내로 간결히.
4) 출력은 지정된 JSON 스키마만 사용.

입력:
- base_recipe: {title, servings, ingredients_json, steps_json, tags, macros_json}
- transform_rules: {swaps_json[], amount_limits_json[], forbidden_json[]}
- user_constraints: {allergies[], dislikes[], time_limit_min, tools[]}

출력(JSON 스키마):
{
  "deltas": [
    {"op": "swap", "from": "string", "to": "string"},
    {"op": "scale", "name_norm": "string", "factor": 0.5~2.0}
  ],
  "final_ingredients": [{"name_norm": "string","amount_g": number},...],
  "final_steps": ["...", "..."],
  "title_suffix": "(변형)"
}
```

### 4.2 Judge

```
당신은 '레시피 심사관'입니다. 아래 체크리스트로만 평가하세요.

체크리스트(예/아니오 + 간단한 사유):
- forbidden 또는 user_allergies/dislikes 포함? (정확 매칭로 판단)
- base 대비 deltas가 swap/scale만인가? (새 재료 추가 금지)
- amount_limits 위반 없는가?
- 1인분 탄수화물 '추정'이 기준(<=15g)을 만족하는가? (간단 근거/추정보고)
- 출력 스키마/타입 오류가 없는가?

출력(JSON):
{
  "passed": true|false,
  "reasons": ["string..."],
  "suggested_fixes": ["string..."]   // 예: "olive_oil 25g -> 15g로 감소"
}
```

---

## 5. 파이프라인 의사코드 (FastAPI 서비스 안)

```python
def select_base(query, prefer_tags) -> GoldenRecipe:
    # 간단: 태그 일치 + 제목 ILIKE로 상위 3개 중 1개 선택
    ...

def call_generator(base, rules, user_constraints) -> dict:
    prompt = build_generator_prompt(base, rules, user_constraints)
    return llm_generate_json(prompt)

def call_judge(base, rules, user_constraints, gen_out) -> dict:
    prompt = build_judge_prompt(base, rules, user_constraints, gen_out)
    return llm_generate_json(prompt)

@app.post("/generate-from-golden")
def generate_from_golden(req: GenerateRequest):
    base = select_base(req.selection, req.selection.prefer_tags) if req.selection.by=="auto" else get_by_id(req.selection.id)
    rules = get_rules_for_base(base.id)

    attempts, max_attempts = 0, 3  # 최초 1회 + 수정 2회
    last_gen, last_judge = None, None

    while attempts < max_attempts:
        last_gen = call_generator(base, rules, req.user_constraints)
        last_judge = call_judge(base, rules, req.user_constraints, last_gen)
        if last_judge.get("passed") is True:
            break
        # suggested_fixes를 generator 입력에 반영하도록 간단 로직
        apply_suggested_fixes_to_context(rules, req.user_constraints, last_gen, last_judge)
        attempts += 1

    passed = last_judge.get("passed") is True
    rec_id = persist_generation(
        base_id = str(base.id),
        deltas = last_gen.get("deltas", []),
        final_ingredients = last_gen.get("final_ingredients", []),
        final_steps = last_gen.get("final_steps", []),
        judge_report = last_judge,
        passed = passed,
        model_gen = MODEL_GEN,
        model_judge = MODEL_JUDGE
    )

    return {
        "generated_id": rec_id,
        "title": base.title + (last_gen.get("title_suffix") or ""),
        "final_ingredients": last_gen.get("final_ingredients", []),
        "final_steps": last_gen.get("final_steps", []),
        "passed": passed,
        "judge_report": last_judge
    }
```

---

## 6. 운영 규칙(간단하고 실전적인 가이드)

1. **골든셋 30개**: *닭/돼지/계란/샐러드/볶음* 5카테고리 × 6개.
2. **정규화 이름(name_norm) 고정표**: 팀 공용 CSV 만들어 공유.
3. **금지어 리스트 공통화**: `sugar, honey, rice, wheat_flour, noodle_wheat, ...`
4. **양 범위(amount_limits)**: 오일/버터/소금 등 **최소~최대** 범위 정해두기.
5. **로그 필수 저장**: 실패사유(`reasons`)와 수정제안(`suggested_fixes`)는 개선의 핵심.

---

## 7. 단순 평가/품질 게이트(오프라인)

* **샘플 50건** 요청으로 자동 점검:

  * 금지어 위반률: **0%**
  * 스키마 오류: **0건**
  * 재시도(≤2회) 내 통과율: **≥90%**
* 간단 CSV로 **체크리스트 결과**를 적재 → 주간 회고 때 개선.

---

## 8. 릴리즈 계획(1~2일 스프린트)

* Day 1

  * 골든셋 30개 수집/정규화, 금지어/치환/범위 규칙 작성
  * FastAPI 엔드포인트 스캐폴딩, LLM 프롬프트 2개 준비(복붙)
* Day 2

  * 파이프라인 묶기(선택→생성→심사→자기수정→저장)
  * 간단 샘플 20~30건 수동 테스트 → 게이트 통과 확인
  * **DoD** 충족 시 병합

---

## 9. 테스트 예시 (빠른 수동 검증용)

* **Case A**: “닭가슴살, 10분 이내, 샐러드” → 샐러드 골든셋 기반 변형, 금지어 0, 통과.
* **Case B**: “면 요리” → `wheat_noodles -> tofu_noodles`로 치환, 통과.
* **Case C(실패 기대)**: 사용자 기피 `cilantro` 포함된 베이스 → Judge Fail → Generator 재시도에서 제거 후 Pass.
* **Case D(범위 위반)**: olive_oil 30g 제안 → Judge “25g→15g”로 축소 제안 → 재시도 후 Pass.

---

## 10. 응답/UI 표시 권장안

* **라벨**: `생성됨`, `검증 통과`(✅) / `수정 후 통과`(🛠️✅) / `검증 실패`(❌)
* **툴팁**:

  * 사용한 **베이스 레시피 제목**
  * 적용 **치환/스케일 deltas**
  * Judge **체크리스트 결과** 핵심만(금지어 0, 탄수 추정 OK 등)

---

## 11. 유지보수 팁

* 실패 로그를 **주간 10개**만 골라 규칙/이름표/골든셋을 보강 → 통과율이 꾸준히 오름.
* 나중에 여력 생기면 **① 근거 고정 RAG**(evidence_ids)나 **③ 영양 수치화**(소형 100재료 CSV)를 추가로 얹으면 됨.

---

## 12. 샘플 cURL

```bash
curl -X POST https://api.example.com/generate-from-golden \
  -H "Content-Type: application/json" \
  -d '{
    "user_constraints": {
      "allergies": ["peanut"],
      "dislikes": ["cilantro"],
      "time_limit_min": 15,
      "tools": ["pan"]
    },
    "selection": {
      "by": "auto",
      "id": null,
      "prefer_tags": ["salad", "chicken"]
    }
  }'
```

---

## 13. Definition of Done (DoD)

* [ ] DB 3테이블 생성 및 마이그레이션 완료
* [ ] 골든셋 30개 + 공통 규칙 1세트 업로드
* [ ] Generator/Judge 프롬프트 고정 및 환경변수로 모델명 분리
* [ ] `/generate-from-golden` 엔드포인트에서 **50건 배치 테스트** 통과
* [ ] 금지어 위반률 0%, 스키마 오류 0건, 재시도≤2회 내 통과율 ≥90%

---


