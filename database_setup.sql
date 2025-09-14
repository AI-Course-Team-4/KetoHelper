-- 만개의레시피 키토 크롤링 데이터베이스 스키마
-- Supabase SQL 에디터에서 실행

-- 기존 테이블 삭제 (완전 초기화)
drop table if exists recipes_keto_raw cascade;
drop table if exists crawl_runs cascade;
drop function if exists generate_search_blob(text, text[], text, jsonb, jsonb);
drop function if exists update_search_blob();

-- 확장 설치
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
  -- 임베딩용 텍스트 (양 정보 제거된 깔끔한 텍스트)
  embedding_blob text,
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


-- embedding_blob 생성 함수 (양 정보 완전 제거)
create or replace function generate_embedding_blob(
  p_title text,
  p_tags text[],
  p_summary text,
  p_ingredients jsonb
) returns text as $$
declare
  ingredients_text text := '';
  title_clean text := '';
  summary_clean text := '';
  final_text text := '';
begin
  -- 1) 재료 처리
  if p_ingredients is not null and jsonb_typeof(p_ingredients) = 'array' then
    -- JSON 배열 -> 문자열 (name 필드만 추출)
    select string_agg(
      case 
        when jsonb_typeof(value) = 'object' then coalesce(value->>'name','')
        else value::text 
      end, ' '
    )
    into ingredients_text
    from (
      select distinct 
        case 
          when jsonb_typeof(value) = 'object' then coalesce(value->>'name','')
          else trim(value::text) 
        end as value
      from jsonb_array_elements(p_ingredients)
    ) t;

    -- 괄호 속 설명 제거
    ingredients_text := regexp_replace(ingredients_text, '\([^)]*\)', ' ', 'gi');

    -- 구분자 단순화 (- ~ | + / ,)
    ingredients_text := regexp_replace(ingredients_text, '[-~|+/,]', ' ', 'g');

    -- 숫자 + 단위 제거
    ingredients_text := regexp_replace(
      ingredients_text,
      '\d+(?:[./]\d+)?\s*(g|kg|mg|ml|l|컵|큰술|작은술|스푼|티스푼|tsp|tbsp|개|장|쪽|줌|봉|캔|조각|꼬집|근)?',
      ' ',
      'gi'
    );

    -- 단독 단위 제거 (숫자 없이 남은 경우)
    ingredients_text := regexp_replace(
      ingredients_text,
      '\b(개|g|kg|ml|l|컵|큰술|작은술|스푼|티스푼|tsp|tbsp|꼬집|조금|약간|T|t)\b',
      ' ',
      'gi'
    );

    -- 저신호 재료 제거 (최소화: 소금, 후추, 식용유, 양념만)
    ingredients_text := regexp_replace(ingredients_text, '\b(소금|후추|식용유|양념)\b', ' ', 'gi');

    -- 합성 표현 정규화
    ingredients_text := regexp_replace(ingredients_text, '\b김밥\s*용\s*김\b', '김', 'gi');
    ingredients_text := regexp_replace(ingredients_text, '\b씨\s*없는\s+([^\s]+)', '\1', 'gi');
    ingredients_text := regexp_replace(ingredients_text, '\b통\s+([^\s]+)', '\1', 'gi');

    -- 공백 정리
    ingredients_text := regexp_replace(ingredients_text, '\s+', ' ', 'g');
    ingredients_text := trim(ingredients_text);
  end if;

  -- 2) 제목 정리
  title_clean := coalesce(p_title,'');
  -- 괄호, 대괄호, 슬래시 안 텍스트 제거
  title_clean := regexp_replace(title_clean, '\[[^]]*\]', ' ', 'g');
  title_clean := regexp_replace(title_clean, '\([^)]*\)', ' ', 'g');
  title_clean := regexp_replace(title_clean, '/+', ' ', 'g');
  -- 자주 쓰이는 불필요 단어 제거
  title_clean := regexp_replace(title_clean, '(만들기|레시피)', ' ', 'gi');
  title_clean := regexp_replace(title_clean, '\s+', ' ', 'g');
  title_clean := trim(title_clean);

  -- 3) 요약은 너무 길면 100자까지만
  summary_clean := coalesce(p_summary,'');
  summary_clean := substring(summary_clean from 1 for 100);

  -- 4) 최종 조립 (레시피명 제외)
  final_text := lower(
    coalesce(array_to_string(p_tags,' '),'') || ' ' ||
    coalesce(summary_clean,'') || ' ' ||
    coalesce(ingredients_text,'')
  );
  
  -- 5) 최종 공백 정리
  final_text := regexp_replace(final_text, '\s+', ' ', 'g');
  final_text := trim(final_text);
  
  return final_text;
end;
$$ language plpgsql;

-- embedding_blob 업데이트 함수
create or replace function update_embedding_blob() returns trigger as $$
begin
  new.embedding_blob = generate_embedding_blob(
    new.title,
    new.tags,
    new.summary,
    new.ingredients
  );
  return new;
end;
$$ language plpgsql;

-- 트리거 생성 (INSERT/UPDATE 시 자동으로 embedding_blob 생성)
create trigger trigger_update_embedding_blob
  before insert or update on recipes_keto_raw
  for each row execute function update_embedding_blob();

-- 인덱스 생성 (검색 성능 향상)
create index if not exists idx_recipes_tags on recipes_keto_raw using gin(tags);
create index if not exists idx_recipes_ingredients on recipes_keto_raw using gin(ingredients);
-- 임베딩 텍스트 검색용 인덱스 (pg_trgm)
create index if not exists idx_recipes_embedding_trgm on recipes_keto_raw using gin (embedding_blob gin_trgm_ops);
-- source_url은 UNIQUE 자체가 인덱스라 별도 인덱스 불필요

-- Row Level Security (RLS) 설정 (선택사항)
-- alter table recipes_keto_raw enable row level security;
-- alter table crawl_runs enable row level security;

-- 기본 정책 (모든 사용자가 읽기/쓰기 가능)
-- create policy "Enable all access for recipes_keto_raw" on recipes_keto_raw for all using (true);
-- create policy "Enable all access for crawl_runs" on crawl_runs for all using (true);

-- 확장 예정: 개인화 기능용 테이블 (주석 처리)
/*
-- 사용자 개인화 정보 테이블
create table if not exists user_preferences (
  user_id uuid primary key,
  disliked_ingredients text[],
  allergies text[],
  preference_embedding vector(1536),  -- OpenAI embedding 차원
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 개인화 관련 인덱스
create index if not exists idx_user_preferences_ingredients on user_preferences using gin(disliked_ingredients);
create index if not exists idx_user_preferences_allergies on user_preferences using gin(allergies);
create index if not exists idx_user_preferences_embedding on user_preferences using ivfflat (preference_embedding vector_cosine_ops);
*/

-- 데이터 확인용 뷰 (division by zero 방지)
create or replace view recipe_summary as
select
  count(*) as total_recipes,
  count(title) as has_title,
  count(ingredients) as has_ingredients,
  count(steps) as has_steps,
  count(author) as has_author,
  case 
    when count(*) > 0 then round(count(title)::numeric / count(*) * 100, 2)
    else 0
  end as title_completeness_pct,
  case 
    when count(*) > 0 then round(count(ingredients)::numeric / count(*) * 100, 2)
    else 0
  end as ingredients_completeness_pct,
  case 
    when count(*) > 0 then round(count(steps)::numeric / count(*) * 100, 2)
    else 0
  end as steps_completeness_pct,
  max(fetched_at) as last_crawl
from recipes_keto_raw;