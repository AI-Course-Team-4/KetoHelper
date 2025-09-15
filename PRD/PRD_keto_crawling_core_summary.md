# PRD — 만개의 레시피 "키토" 크롤링 → Supabase 적재 (핵심 요약)

> 목적: 만개의 레시피 사이트에서 "키토" 검색 결과를 크롤링하여 DB에 저장한다.

## 1) 목적 (TL;DR)
- "키토" 검색 결과의 레시피를 **크롤링**해 **Supabase(Postgres)**에 **중복 없이** 저장한다.
- 이후 다른 기능에서 활용할 수 있는 **소스 데이터**로 활용한다.

## 2) 범위
**포함**
- 모바일 검색 목록(`q=키토`) 순회, 상세 페이지 파싱
- 필드: 제목, 작성자, 평점/조회수(있으면), **분량/시간/난이도**, **재료[]**, **조리순서[]**, **태그[]**, **이미지[]**, 원문 URL, 외부 ID
- **UPSERT(on_conflict=source_url)**, 실행 이력 기록
- 보호장치: rate-limit, 재시도, 타임아웃, **증분 종료 규칙**

**제외**
- 이미지 미러링, 영양 파이프라인, 프론트 구현, 개인화 기능

## 3) 데이터 모델 (DDL 최소)
```sql
-- Supabase SQL 에디터에서 실행할 DDL
create extension if not exists pgcrypto;
create extension if not exists pg_trgm;
create extension if not exists vector;

-- 레시피 테이블 (크롤링용)
create table if not exists recipes_keto_raw (
  id uuid primary key default gen_random_uuid(),
  source_site text not null default '10000recipe',
  source_url text not null unique,
  source_recipe_id text,
  title text,
  author text,
  rating numeric,
  views int,
  servings text,
  cook_time text,
  difficulty text,
  summary text,
  tags text[],
  ingredients jsonb,
  steps jsonb,
  images text[],
  fetched_at timestamptz not null default now(),
  -- 검색용 생성열 (저장 비용 거의 없음)
  search_blob text generated always as (
    lower(
      coalesce(title,'') || ' ' ||
      array_to_string(tags,' ') || ' ' ||
      coalesce(summary,'') || ' ' ||
      array_to_string((select array_agg(value::text)
        from jsonb_array_elements_text(ingredients)),' ') || ' ' ||
      array_to_string((select array_agg(s->>'text')
        from jsonb_array_elements(steps) s),' ')
    )
  ) stored,
  -- 임베딩 벡터 (NULL 허용, 나중에 pgvector 인덱스만 추가하면 끝)
  embedding vector(1536)
);

-- 크롤링 실행 이력 테이블
create table if not exists crawl_runs (
  run_id uuid primary key default gen_random_uuid(),
  query text not null,              -- '키토'
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  page_start int,
  page_end int,
  inserted_count int default 0,
  updated_count int default 0,
  error_count int default 0,
  notes text
);

-- 인덱스 생성 (검색 성능 향상)
create index if not exists idx_recipes_tags on recipes_keto_raw using gin(tags);
create index if not exists idx_recipes_ingredients on recipes_keto_raw using gin(ingredients);
-- 키워드/하이브리드 검색용 인덱스 (pg_trgm)
create index if not exists idx_recipes_trgm on recipes_keto_raw using gin (search_blob gin_trgm_ops);
-- source_url은 UNIQUE 자체가 인덱스라 별도 인덱스 불필요

-- ===== 확장 예정: 개인화 기능 =====
-- (나중에 개인화 기능 추가 시 사용할 스키마)

-- 사용자 개인화 정보 테이블
-- create table if not exists user_preferences (
--   user_id uuid primary key,
--   disliked_ingredients text[],
--   allergies text[],
--   preference_embedding vector(1536),  -- OpenAI embedding 차원
--   created_at timestamptz not null default now(),
--   updated_at timestamptz not null default now()
-- );

-- 개인화 관련 인덱스
-- create index if not exists idx_user_preferences_ingredients on user_preferences using gin(disliked_ingredients);
-- create index if not exists idx_user_preferences_allergies on user_preferences using gin(allergies);
-- create index if not exists idx_user_preferences_embedding on user_preferences using ivfflat (preference_embedding vector_cosine_ops);

-- 사용 예시 (주석 처리)
-- SELECT r.* FROM recipes_keto_raw r
-- LEFT JOIN user_preferences u ON u.user_id = $1
-- WHERE NOT (r.ingredients && u.disliked_ingredients)
-- ORDER BY r.rating DESC;
```

## 4) 구현 요구사항
1) **목록 수집기**: `page=1..` 순회, `/recipe/{id}` 링크 수집, 다음 페이지 이동, 중복 제거  
2) **상세 파서**: 메타(분량/시간/난이도), 재료[], 조리순서[], 태그[], 이미지[] 추출  
3) **적재/로그**: Supabase `upsert(source_url)`, `crawl_runs`에 범위·카운트 기록  
4) **보호장치**: 1–2 rps + 랜덤 sleep(0.5–2s), 요청 타임아웃 10s, 상세 파싱 가드 30s  
5) **증분 종료**: **새 URL 미발견 연속 K페이지(예: 3)** 또는 **MAX_PAGES(예: 50)** 도달 시 종료  
6) **테스트**: HTML 스냅샷 단위 테스트(제목/재료/스텝), 2–3페이지 통합 실행으로 필드 비율 확인

## 5) 구현 팁
- **UPSERT 키**: `on_conflict (source_url)` 유지 👍
- **증분 종료**: "새 URL 미발견 연속 K페이지(예: 3)" → 성능에 큰 도움
- **테스트**: 목록 3~5p 스모크 후 전체 실행
- **파서 내구성**: DOM 변동 대비 셀렉터 1~2개 대안 준비

## 6) 수용 기준(AC)
- 최초 전체 실행에서 **≥ 200건** 저장(사이트 공개 분량 기준)
- `title/ingredients/steps/source_url` **≥ 95% non-null**
- 중복 0%(source_url unique), 재시도 후 실패율 **≤ 3%**

## 7) 컴플라이언스
- robots.txt/이용약관 준수, 부하 방지(야간 실행 권장), 원문 출처 URL 보존

## 8) 스타트 가이드
- DDL 실행 → 목록 3–5페이지 시범 수집 → 품질 확인 → 전체 실행
- 이슈 시: requests+BS4 → **Playwright** 폴백(무작위 UA/지연)
```