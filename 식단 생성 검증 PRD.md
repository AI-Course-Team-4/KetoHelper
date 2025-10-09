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
  version INTEGER NOT NULL DEFAULT 1,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 골든셋 버전 관리 인덱스
CREATE INDEX idx_golden_active ON golden_recipes(id, version DESC) WHERE is_active = true;

-- 2) 변형(치환/범위/금지) 규칙
CREATE TABLE IF NOT EXISTS transform_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  base_recipe_id UUID REFERENCES golden_recipes(id) ON DELETE CASCADE,
  swaps_json JSONB NOT NULL,         -- [{from, to, ratio}]
  amount_limits_json JSONB NOT NULL, -- [{name_norm, min_g, max_g}]
  forbidden_json JSONB NOT NULL,     -- ["sugar","honey","rice"...]
  version INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 3) 생성 결과 + 심사 리포트(프로비넌스)
CREATE TABLE IF NOT EXISTS generated_recipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,                      -- 사용자 ID (옵션)
  base_recipe_id UUID REFERENCES golden_recipes(id) ON DELETE SET NULL,
  deltas_json JSONB NOT NULL,        -- [{op: "swap"|"scale", ...}]
  final_ingredients_json JSONB NOT NULL,
  final_steps_json JSONB NOT NULL,
  judge_report_json JSONB NOT NULL,  -- {passed, reasons[], suggested_fixes[]}
  passed BOOLEAN NOT NULL,
  attempts INTEGER DEFAULT 1,        -- 재시도 횟수
  response_time_ms INTEGER,          -- 응답 시간 (밀리초)
  model_gen TEXT,
  model_judge TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 성능 분석용 인덱스
CREATE INDEX idx_generated_created_at ON generated_recipes(created_at DESC);
CREATE INDEX idx_generated_passed ON generated_recipes(passed);
CREATE INDEX idx_generated_user_id ON generated_recipes(user_id) WHERE user_id IS NOT NULL;
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

**name_norm 정규화 규칙**

```csv
korean,english,name_norm,category
닭가슴살,chicken breast,chicken_breast,protein
올리브오일,olive oil,olive_oil,fat
두부면,tofu noodles,tofu_noodles,carb_substitute
곤약밥,konjac rice,konjac_rice,carb_substitute
로메인,romaine lettuce,romaine_lettuce,vegetable
버터,butter,butter,fat
```

정규화 규칙:
- 소문자 + 언더스코어만 사용
- 한글→영문 매핑 테이블 관리 (`backend/data/ingredient_normalization.csv`)
- 복합 재료는 `base_modifier` 형식: `tofu_noodles`, `coconut_flour`
- 공백 없음, 특수문자 없음

---

## 3. API 계약 (FastAPI 초안)

### 3.0 파일 구조 (Backend)

```
backend/app/domains/recipe/
  ├── api/
  │   ├── __init__.py
  │   └── golden_recipe_routes.py
  ├── models/
  │   └── recipe_models.py
  └── services/
      ├── recipe_selector.py
      ├── recipe_generator.py
      └── recipe_judge.py

backend/data/
  └── ingredient_normalization.csv
```

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
- 1인분 탄수화물 '추정'이 기준(<=15g)을 만족하는가?
  * 탄수화물 추정 방법:
    1. base_recipe의 macros_json.carb_g를 기준으로 시작
    2. deltas의 swap/scale에 따라 비례 조정
    3. 최종 추정값이 <= 15g인지 확인
    4. 근거를 reasons에 명시 (예: "베이스 6g, 치킨 10% 증량으로 6.6g 추정")
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
from json import JSONDecodeError
from asyncio import TimeoutError
import logging

logger = logging.getLogger(__name__)

def select_base(query, prefer_tags) -> GoldenRecipe:
    # 간단: 태그 일치 + 제목 ILIKE로 상위 3개 중 1개 선택
    ...

async def call_generator(base, rules, user_constraints, timeout=30) -> dict:
    """Generator LLM 호출 (타임아웃 30초)"""
    try:
        prompt = build_generator_prompt(base, rules, user_constraints)
        return await llm_generate_json(prompt, timeout=timeout)
    except (JSONDecodeError, TimeoutError) as e:
        logger.error(f"Generator failed for base {base.id}: {e}")
        raise

async def call_judge(base, rules, user_constraints, gen_out, timeout=20) -> dict:
    """Judge LLM 호출 (타임아웃 20초)"""
    try:
        prompt = build_judge_prompt(base, rules, user_constraints, gen_out)
        return await llm_generate_json(prompt, timeout=timeout)
    except (JSONDecodeError, TimeoutError) as e:
        logger.error(f"Judge failed for base {base.id}: {e}")
        raise

@app.post("/generate-from-golden")
async def generate_from_golden(req: GenerateRequest):
    try:
        # 사용자 입력 검증 (보안)
        validate_user_constraints(req.user_constraints)
        
        base = select_base(req.selection, req.selection.prefer_tags) if req.selection.by=="auto" else get_by_id(req.selection.id)
        rules = get_rules_for_base(base.id)

        attempts, max_attempts = 0, 3  # 최초 1회 + 수정 2회
        last_gen, last_judge = None, None

        while attempts < max_attempts:
            try:
                last_gen = await call_generator(base, rules, req.user_constraints)
                last_judge = await call_judge(base, rules, req.user_constraints, last_gen)
                
                if last_judge.get("passed") is True:
                    break
                    
                # suggested_fixes를 generator 입력에 반영하도록 간단 로직
                apply_suggested_fixes_to_context(rules, req.user_constraints, last_gen, last_judge)
                attempts += 1
                
            except (JSONDecodeError, TimeoutError) as e:
                logger.error(f"Attempt {attempts} failed: {e}")
                if attempts >= max_attempts - 1:
                    raise HTTPException(status_code=500, detail="Generation failed after retries")
                attempts += 1
                continue

        passed = last_judge.get("passed") is True
        
        try:
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
        except Exception as e:
            logger.error(f"DB persist failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to save generation")

        return {
            "generated_id": rec_id,
            "title": base.title + (last_gen.get("title_suffix") or ""),
            "final_ingredients": last_gen.get("final_ingredients", []),
            "final_steps": last_gen.get("final_steps", []),
            "passed": passed,
            "judge_report": last_judge
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_from_golden: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def validate_user_constraints(constraints: UserConstraints):
    """사용자 입력 검증 (보안)"""
    import re
    allowed_pattern = re.compile(r'^[a-z_]+$')
    
    for item in constraints.allergies + constraints.dislikes:
        if not allowed_pattern.match(item):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid input: {item}. Only lowercase letters and underscores allowed."
            )
```

---

## 6. 운영 규칙(간단하고 실전적인 가이드)

1. **골든셋 30개**: *닭/돼지/계란/샐러드/볶음* 5카테고리 × 6개.
2. **정규화 이름(name_norm) 고정표**: 팀 공용 CSV 만들어 공유.
3. **금지어 리스트 공통화**: `sugar, honey, rice, wheat_flour, noodle_wheat, ...`
4. **양 범위(amount_limits)**: 오일/버터/소금 등 **최소~최대** 범위 정해두기.
5. **로그 필수 저장**: 실패사유(`reasons`)와 수정제안(`suggested_fixes`)는 개선의 핵심.
6. **성능 가이드**:
   - Generator/Judge 순차 호출 필수 (병렬 불가)
   - 타임아웃: Generator 30초, Judge 20초
   - 캐싱: 동일 base_id + user_constraints 조합은 10분간 캐싱 권장
   - 평균 응답시간: 5-10초 (재시도 없을 때), 최대 30초 (2회 재시도)

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

## 9. 테스트 예시

### 9.1 수동 검증 케이스

* **Case A**: "닭가슴살, 10분 이내, 샐러드" → 샐러드 골든셋 기반 변형, 금지어 0, 통과.
* **Case B**: "면 요리" → `wheat_noodles -> tofu_noodles`로 치환, 통과.
* **Case C(실패 기대)**: 사용자 기피 `cilantro` 포함된 베이스 → Judge Fail → Generator 재시도에서 제거 후 Pass.
* **Case D(범위 위반)**: olive_oil 30g 제안 → Judge "25g→15g"로 축소 제안 → 재시도 후 Pass.

### 9.2 자동화 테스트 (pytest)

```python
# tests/domains/recipe/test_recipe_generation.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.domains.recipe.models.recipe_models import GenerateRequest, UserConstraints, Selection

client = TestClient(app)

@pytest.mark.asyncio
async def test_forbidden_ingredient_rejection():
    """금지어(sugar) 포함 시 자동 거부 또는 수정"""
    req = {
        "user_constraints": {
            "allergies": ["sugar"],
            "dislikes": [],
            "time_limit_min": 15,
            "tools": ["pan"]
        },
        "selection": {
            "by": "id",
            "id": "golden-recipe-with-sugar-base",
            "prefer_tags": []
        }
    }
    response = client.post("/generate-from-golden", json=req)
    assert response.status_code == 200
    result = response.json()
    
    # sugar가 최종 재료에 없어야 함
    ingredient_names = [ing["name_norm"] for ing in result["final_ingredients"]]
    assert "sugar" not in ingredient_names
    assert result["passed"] is True

@pytest.mark.asyncio
async def test_amount_limits_enforcement():
    """양 범위 제한 준수 확인"""
    req = {
        "user_constraints": {
            "allergies": [],
            "dislikes": [],
            "time_limit_min": 20,
            "tools": ["pan", "oven"]
        },
        "selection": {
            "by": "auto",
            "id": None,
            "prefer_tags": ["keto", "salad"]
        }
    }
    response = client.post("/generate-from-golden", json=req)
    assert response.status_code == 200
    result = response.json()
    
    # olive_oil이 있다면 5-25g 범위 내
    for ing in result["final_ingredients"]:
        if ing["name_norm"] == "olive_oil":
            assert 5 <= ing["amount_g"] <= 25

@pytest.mark.asyncio
async def test_carb_limit_check():
    """탄수화물 15g 이하 확인"""
    req = {
        "user_constraints": {
            "allergies": [],
            "dislikes": [],
            "time_limit_min": None,
            "tools": []
        },
        "selection": {
            "by": "auto",
            "id": None,
            "prefer_tags": ["keto"]
        }
    }
    response = client.post("/generate-from-golden", json=req)
    assert response.status_code == 200
    result = response.json()
    
    # Judge 리포트에서 탄수 추정값 확인
    assert result["passed"] is True
    assert any("탄수" in reason or "carb" in reason.lower() 
               for reason in result["judge_report"]["reasons"])

@pytest.mark.asyncio
async def test_schema_validation():
    """출력 스키마 검증"""
    req = {
        "user_constraints": {
            "allergies": [],
            "dislikes": [],
            "time_limit_min": 10,
            "tools": ["pan"]
        },
        "selection": {
            "by": "auto",
            "id": None,
            "prefer_tags": ["quick"]
        }
    }
    response = client.post("/generate-from-golden", json=req)
    assert response.status_code == 200
    result = response.json()
    
    # 필수 필드 존재 확인
    assert "generated_id" in result
    assert "title" in result
    assert "final_ingredients" in result
    assert "final_steps" in result
    assert "passed" in result
    assert "judge_report" in result
    
    # 각 재료가 name_norm, amount_g 가짐
    for ing in result["final_ingredients"]:
        assert "name_norm" in ing
        assert "amount_g" in ing
        assert isinstance(ing["amount_g"], (int, float))

@pytest.mark.asyncio
async def test_invalid_user_input_rejection():
    """보안: 잘못된 사용자 입력 거부"""
    req = {
        "user_constraints": {
            "allergies": ["sugar; DROP TABLE users;"],  # SQL 인젝션 시도
            "dislikes": [],
            "time_limit_min": 10,
            "tools": []
        },
        "selection": {
            "by": "auto",
            "id": None,
            "prefer_tags": []
        }
    }
    response = client.post("/generate-from-golden", json=req)
    assert response.status_code == 400
    assert "Invalid input" in response.json()["detail"]
```

---

## 10. 응답/UI 표시 권장안

* **라벨**: `생성됨`, `검증 통과`(✅) / `수정 후 통과`(🛠️✅) / `검증 실패`(❌)
* **툴팁**:

  * 사용한 **베이스 레시피 제목**
  * 적용 **치환/스케일 deltas**
  * Judge **체크리스트 결과** 핵심만(금지어 0, 탄수 추정 OK 등)

---

## 11. 유지보수 및 개선 팁

### 11.1 주간 리뷰 체크리스트
* 실패 로그를 **주간 10개**만 골라 규칙/이름표/골든셋을 보강 → 통과율이 꾸준히 오름.
* Judge Fail 사유별 통계 확인 및 프롬프트 개선
* 가장 많이 사용된 골든셋 레시피 분석 → 유사 레시피 추가

### 11.2 골든셋 확장 전략
* 초기 30개 → 월 10개씩 추가 (목표: 6개월 후 100개)
* 추가 기준:
  - 사용자 요청이 많은 카테고리
  - 기존 레시피와 겹치지 않는 재료 조합
  - 계절별 특화 레시피 (여름/겨울)

### 11.3 향후 기능 로드맵
* **Phase 4 (3개월 후)**: 근거 고정 RAG (evidence_ids) 추가
  - 각 골든셋에 영양학적 근거 문서 링크
  - Judge가 근거 기반으로 더 정확한 심사
* **Phase 5 (6개월 후)**: 영양 수치화 (소형 100재료 CSV)
  - 재료별 정확한 탄수화물/단백질/지방 함량 DB
  - 추정이 아닌 계산된 영양 정보 제공

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
* [ ] pytest 자동화 테스트 5개 이상 작성 및 통과
* [ ] 에러 핸들링 (타임아웃, JSON 파싱 오류, DB 저장 실패) 구현
* [ ] 사용자 입력 검증 (보안) 구현

---

## 14. 보안 가이드

### 14.1 입력 검증
- **allergies/dislikes**: 소문자 알파벳과 언더스코어만 허용 (`^[a-z_]+$`)
- **time_limit_min**: 양의 정수만 허용 (1~180분)
- **tools**: 사전 정의된 화이트리스트에서만 선택
- **prefer_tags**: 사전 정의된 태그 목록에서만 선택

### 14.2 프롬프트 인젝션 방지
- 사용자 입력을 프롬프트 문자열에 직접 삽입하지 말 것
- 구조화된 JSON으로만 LLM에 전달
- 예시:
  ```python
  # ❌ 나쁜 예
  prompt = f"User allergies: {user_input}"
  
  # ✅ 좋은 예
  prompt_data = {
    "user_constraints": {
      "allergies": validated_allergies_list
    }
  }
  prompt = json.dumps(prompt_data)
  ```

### 14.3 SQL 인젝션 방지
- Supabase ORM 또는 파라미터화된 쿼리만 사용
- 원시 SQL 사용 시 반드시 파라미터 바인딩 사용

### 14.4 Rate Limiting
- 사용자당 `/generate-from-golden` 호출: **분당 5회**
- IP당 제한: **분당 10회**

---

## 15. 모니터링 및 알림

### 15.1 실시간 지표
- `/generate-from-golden` 평균 응답시간
- HTTP 에러율 (4xx, 5xx)
- Generator/Judge LLM 호출 실패율
- DB 저장 실패율

### 15.2 일간/주간 지표
- 재시도율 분포 (0회/1회/2회/실패)
- 금지어 위반 시도 건수
- Judge Fail 사유별 통계
- 가장 많이 사용된 골든셋 레시피 Top 10

### 15.3 알림 트리거
- 실패율 > 20% (10분간 지속): Slack 알림
- 평균 응답시간 > 15초 (10분간): Slack 알림
- Generator/Judge 타임아웃 > 5회/시간: Slack 알림
- DB 연결 오류: 즉시 Slack 알림

### 15.4 로깅 전략
```python
# 필수 로그 필드
log_entry = {
    "timestamp": datetime.now().isoformat(),
    "user_id": user_id,
    "base_recipe_id": base.id,
    "attempts": attempts,
    "passed": passed,
    "judge_report": judge_report,
    "response_time_ms": elapsed_ms,
    "error": error_message if error else None
}
```

---

## 16. 기존 시스템 통합 계획

### 16.1 현재 Meal 도메인과의 관계
- 기존: `backend/app/domains/meal/` - 사용자 식단 저장/조회
- 신규: `backend/app/domains/recipe/` - 골든셋 기반 레시피 생성

### 16.2 통합 전략

**Phase 1: 병렬 운영 (Week 1-2)**
- 골든셋 시스템 독립적으로 구축
- 기존 meal 생성 로직 유지
- `/generate-from-golden` 엔드포인트 별도 제공
- 내부 테스트 및 검증

**Phase 2: 점진적 마이그레이션 (Week 3-4)**
- `generated_recipes` → `meal` 테이블 변환 로직 추가
  ```python
  def convert_generated_to_meal(generated_recipe, user_id):
      return Meal(
          user_id=user_id,
          title=generated_recipe.title,
          ingredients=generated_recipe.final_ingredients_json,
          steps=generated_recipe.final_steps_json,
          source_recipe_id=generated_recipe.base_recipe_id,
          validation_passed=generated_recipe.passed,
          created_at=datetime.now()
      )
  ```
- 골든셋 기반 생성을 우선 사용, 실패 시 기존 로직 폴백
- A/B 테스트: 50% 사용자에게만 골든셋 적용

**Phase 3: 완전 전환 (Week 5+)**
- 골든셋 통과율 ≥ 90% 확인 후 완전 전환
- 기존 meal 생성 로직 deprecate
- 모니터링 지표 안정화 확인

### 16.3 데이터 마이그레이션
- 기존 우수 평가 받은 meal → golden_recipes 후보로 추가
- 골든셋 확장 시 기존 사용자 데이터 활용

### 16.4 롤백 계획
```sql
-- 골든셋/규칙 버전 관리
ALTER TABLE golden_recipes ADD COLUMN version INTEGER DEFAULT 1;
ALTER TABLE golden_recipes ADD COLUMN is_active BOOLEAN DEFAULT true;
ALTER TABLE transform_rules ADD COLUMN version INTEGER DEFAULT 1;

CREATE INDEX idx_golden_active ON golden_recipes(id, version DESC) WHERE is_active = true;
```

- 문제 발생 시 이전 버전으로 즉시 롤백
- 기존 meal 로직으로 폴백 (feature flag 사용)

---


