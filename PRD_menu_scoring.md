# PRD — 메뉴명 기반 재료 추정 & 키토 점수화 V0  
(룰 엔진 + 예외/대체 처리 + 현 스키마 연동)

> 대상: 1~2명, 1~2일 내 실구동  
> 목적: **메뉴명만으로도 초기 키토 판정이 가능한 최소 파이프라인** 구축 (예외/대체어 처리 포함)  
> 원칙: **새 테이블 생성 없이** 기존 스키마 활용(필요 컬럼만 추가)

---

## 0) 범위
- 포함: 스키마 최소 확장, 룰 엔진 V0, 예외/대체 키워드 1차, 품질 리포트 CSV, 추천 UX 라벨/토글
- 제외(후속): LLM 보조, 식당별 키토 프로필 자동화, NER/ML, 다중 소스 확장, PostGIS 전환

---

## 1) 성공 기준(수용 기준)
- 파이프라인 1회 실행(스코어링→리포트) **오류 없이 완료**
- `keto_scores`에 **점수 부여 메뉴 ≥ 200건**, 각 레코드에 `rule_version` 포함
- **대체 감지 히트율 ≥ 60%**(표본 50건 수동 검증)
- `needs_review` 큐 생성 및 CSV 내보내기 정상
- FE에서 라벨/필터 노출(더미 가능)
  - 라벨: `score≥80`=**키토 권장**, `50~79`=**조건부 키토**, `<50`=**비추천**
  - 배지: `ingredients_confidence<0.5`=**추정**
  - 필터: “밥/면 제외 가능만 보기”(예외/부정 감지 기반)

---

## 2) 데이터 모델(최소 확장 — “있는 것 살리기”)
### 2.1 사용 테이블
- `menu` : 메뉴 기본 메타(이미 `name_norm` 존재)
- `keto_scores` : **점수/사유/버전** 저장(스냅샷 성격)
- `menu_ingredient` : 메뉴↔재료 매핑(추정 재료 기록)

### 2.2 마이그레이션 DDL (다운타임 없이, 존재 시 건너뜀)
```sql
-- (필요시) 탄수 베이스 enum
do $$ begin
  if not exists (select 1 from pg_type where typname = 'carb_base') then
    create type carb_base as enum ('rice','noodle','bread','none','konjac_rice','cauli_rice','tofu_noodle');
  end if;
end $$;

-- menu: 메뉴 타입(정식/세트/코스 등) - 우선 text로 시작
alter table public.menu
  add column if not exists menu_type text;

-- keto_scores: 운영 필드 확장
alter table public.keto_scores
  add column if not exists needs_review boolean default false,
  add column if not exists substitution_tags jsonb,
  add column if not exists override_reason text,
  add column if not exists final_carb_base carb_base,
  add column if not exists ingredients_confidence numeric(5,2),
  add column if not exists rule_version text;

-- 조회/운영 인덱스
create index if not exists idx_keto_scores_needs_review on public.keto_scores (needs_review);
create index if not exists idx_keto_scores_score on public.keto_scores (score);
```

> 재료는 `menu_ingredient`에 **upsert**(추정 재료는 `source='rule'`, `confidence` 활용)

---

## 3) 점수화 파이프라인(V0)
### 3.1 입력
- `menu(name, name_norm, description, menu_type?)`
- (있으면) 메뉴 섹션/카테고리 텍스트, (있으면) 한줄 설명

### 3.2 전처리
- `name_norm` 생성/보정: 괄호·특수문자 제거, 연속 공백 1칸, 소문자화(영문), 불용어 제거

### 3.3 키워드 사전(초판)
- **고탄수(큰 감점)**: 밥, 덮밥, 초밥, 스시, 라면/라멘, 우동, 국수/면, 파스타, 빵/버거, 피자, 떡, 토르티야/타코, 전분, 설탕, 시럽  
- **저탄 우호(가점)**: 소/돼지/닭, 연어/참치/대구/삼치, 두부, 계란, 치즈, 베이컨, 아보카도, 브로콜리, 버섯, 가지, **샐러드**, **구이**, **스테이크**, **사시미**  
- **메뉴 타입(저점 베이스)**: 정식, 세트, 코스, 모둠, 런치, 디너, 스페셜  
- **예외/대체(패널티 상쇄/축소)**: 곤약밥, 콜리플라워 라이스, 두부면, 곤약면, **밥 제외**, **면 없이**, 무설탕, 저당, 키토/케토/LCHF

### 3.4 점수 규칙(예시 가중)
- 시작점 **50**
- 고탄수 키워드 발견: **–60**(중복 –10씩, 하한 0)
- 저탄 우호 키워드: **+10~+20**(상한 +40)
- 메뉴 타입(정식/세트/코스 등): **–15**(1회)
- **예외/대체 감지 시**
  - **완전 대체**(곤약밥/두부면/콜리 라이스): 직전 밥·면 패널티 **전액 상쇄 +10**
  - **부정/옵션**(밥 제외/면 없이): 패널티 **50% 상쇄**, 라벨=**조건부**
- 최종 점수 **0~100**로 클램프  
- 경계 **35~45** ⇒ `needs_review=true`

### 3.5 예외/대체 감지(간단 정규식, ±5토큰)
- 부정/대체 패턴 예시  
  - `(밥|면)(을|이)?\s*(빼|제외|없이)`  
  - `(밥|면)\s*대신\s*(곤약|두부|콜리플라워)`  
  - `(곤약밥|두부면|콜리플라워\s*라이스)`  
  - `(무설탕|저당|키토|케토|LCHF)`

### 3.6 산출물 기록(Upsert)
- `keto_scores`  
  - `menu_id`, `score(0~100)`, `reasons_json`(룰 로그),  
    `substitution_tags`, `override_reason`, `final_carb_base`,  
    `ingredients_confidence(0~1)`, `needs_review`, `rule_version(예: 2025-09-19.v0)`
- `menu_ingredient` (있을 때)  
  - `menu_id`, `ingredient_id`(또는 alias→id 매핑), `role('main'/'aux')`, `source='rule'`, `confidence(0.30~0.90)`

---

## 4) 대표 케이스 처리(정책 예)
- **호랑이볶음덮밥**: ‘덮밥’ 감점, 단백질 가점 → **낮은 점수(≈35)**, `ingredients_confidence≈0.6`, `needs_review=true`
- **혼마정식(정보 희박)**: ‘정식/세트’ 저점 베이스.  
  - 스시/런치 문맥이면 밥 포함↑ 유지 → **30~40대**  
  - 구이/사시미/샐러드 문맥이면 가산 → **55~70(조건부)**
- **키토 김밥(밥 대신 계란지단)**: ‘김밥’ 감점 **상쇄**(대체 감지) → **75~85**, `final_carb_base='none'`
- **곤약밥 소고기덮밥**: ‘덮밥’ 감점 **상쇄+가산** → **70~80**, `final_carb_base='konjac_rice'`

---

## 5) 추천 UX 규칙
- **라벨 고정**:  
  - `score ≥ 80` → **키토 권장**  
  - `50 ≤ score < 80` 또는 **예외/부정 감지** → **조건부 키토**  
  - `< 50` → **비추천**
- **배지**: `ingredients_confidence < 0.5` → **추정**  
- **필터/토글**: “**밥/면 제외 가능만 보기**”(예외/부정 감지 기반)

---

## 6) 품질 리포트 CSV
- 파일: `quality_report_rulekit.csv`  
- 컬럼:  
  - `total`, `scored`, `avg_score`, `p25/p50/p75`,  
  - `high_carb_hits`, `low_carb_hits`, `substitution_hits`,  
  - `needs_review_count`,  
  - 상위 N 의심 샘플: `menu_id,name,score,keto_reason`
- 실행 예:
```bash
python score_menus.py --out quality_report_rulekit.csv
```

---

## 7) 운영 원칙
- **Idempotent 배치**: 동일 메뉴 재실행해도 동일 결과(키·해시 기반), `rule_version` 필수 기록
- **검수 루프**: `needs_review=true`/경계 점수대(35~45) **일일 10~30건** 수동 확인 → 사전/가중치 튜닝
- **사전(JSON) 버전 관리**: `/data/rules/high_carb.v1.json` 등 파일명에 버전 부여
- **롤백**: 신규 필드 참조 OFF로 즉시 비활성화(스키마는 유지)

---

## 8) 조회/추천 쿼리(참고)
```sql
select
  m.id, m.restaurant_id, m.name, m.price,
  ks.score as keto_score, ks.reasons_json,
  ks.substitution_tags, ks.needs_review
from public.menu m
join public.keto_scores ks on ks.menu_id = m.id
where ks.score >= 50
order by ks.score desc
limit 50;
```

---

## 9) 실행 체크리스트(오늘)
- [ ] DDL 적용(위 2.2)  
- [ ] 사전 JSON 5종: `high_carb.json`, `keto_friendly.json`, `substitutions.json`, `negations.json`, `stopwords.json`  
- [ ] 전처리/정규식/가중치 구현 → `keto_scores`/`menu_ingredient` upsert  
- [ ] 리포트 CSV 생성 → 표본 50건 수동 검증(대체 감지 정확도)  
- [ ] FE 라벨/토글 연결(조건부/추정/제외보기)

---

### 부록 X — 현 스키마 기반 통합 계획(요약 재기재)
- 점수·사유·예외·검수: `keto_scores`  
- 메뉴 타입: `menu.menu_type`  
- 추정 재료: `menu_ingredient (source='rule', confidence 사용)`  
- KPI 추가:  
  - `keto_scores` 점수 적재 **≥200건**, `rule_version` 포함  
  - `menu_ingredient(source='rule')` **≥50건** 생성
