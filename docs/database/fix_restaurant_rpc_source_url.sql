-- =========================================================
-- 식당 RPC 함수 수정: source_url 필드 추가
-- 작성일: 2025년 10월 10일
-- 목적: 모든 식당 검색 RPC 함수에서 source_url을 반환하도록 수정하여 N+1 쿼리 제거
-- 
-- 대상 함수:
--   1. restaurant_menu_vector_search (벡터 검색)
--   2. restaurant_ilike_search (ILIKE 키워드 검색) ⭐ 주요 수정
--   3. restaurant_trgm_search (Trigram 유사도 검색) ⭐ 주요 수정
-- 
-- 실행 환경: Supabase SQL Editor
-- 실행 방법: Supabase SQL Editor에서 전체 스크립트 실행
-- =========================================================

-- 1️⃣ 벡터 검색 RPC 함수 (source_url 포함)
-- 기존 함수 삭제 (반환 타입 변경을 위해 필요)
DROP FUNCTION IF EXISTS restaurant_menu_vector_search(vector, integer, double precision);

CREATE OR REPLACE FUNCTION restaurant_menu_vector_search(
  query_embedding vector(1536),
  match_count int DEFAULT 10,
  similarity_threshold float DEFAULT 0.4
)
RETURNS TABLE (
  restaurant_id uuid,
  restaurant_name text,
  restaurant_category text,
  addr_road text,
  addr_jibun text,
  lat double precision,
  lng double precision,
  phone text,
  menu_id uuid,
  menu_name text,
  menu_description text,
  menu_price integer,
  keto_score integer,
  keto_reasons jsonb,
  similarity_score float,
  source_url text  -- ✅ 추가된 필드
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    r.id AS restaurant_id,
    r.name AS restaurant_name,
    r.category AS restaurant_category,
    r.addr_road,
    r.addr_jibun,
    r.lat,
    r.lng,
    r.phone,
    m.id AS menu_id,
    m.name AS menu_name,
    m.description AS menu_description,
    m.price AS menu_price,
    ks.score AS keto_score,
    ks.reasons_json AS keto_reasons,
    (1 - (me.embedding <=> query_embedding)) AS similarity_score,
    r.source_url  -- ✅ source_url 추가
  FROM menu_embedding me
  JOIN menu m ON me.menu_id = m.id
  JOIN restaurant r ON m.restaurant_id = r.id
  LEFT JOIN keto_scores ks ON ks.menu_id = m.id
  WHERE (1 - (me.embedding <=> query_embedding)) >= similarity_threshold
  ORDER BY me.embedding <=> query_embedding ASC
  LIMIT match_count;
$$;

-- 권한 설정 (anon, authenticated 사용자 모두 사용 가능)
GRANT EXECUTE ON FUNCTION restaurant_menu_vector_search TO anon;
GRANT EXECUTE ON FUNCTION restaurant_menu_vector_search TO authenticated;

COMMENT ON FUNCTION restaurant_menu_vector_search IS 
'식당 메뉴 벡터 검색 (source_url 포함) - 임베딩 기반 의미 검색';


-- 2️⃣ ILIKE 키워드 검색 RPC 함수 (source_url 포함) ⭐ 주요 수정
-- 백엔드에서 실제로 호출하는 함수
DROP FUNCTION IF EXISTS restaurant_ilike_search(text, integer);

CREATE OR REPLACE FUNCTION restaurant_ilike_search(
  query_text text,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  restaurant_id uuid,
  restaurant_name text,
  restaurant_category text,
  addr_road text,
  addr_jibun text,
  lat double precision,
  lng double precision,
  phone text,
  menu_id uuid,
  menu_name text,
  menu_description text,
  menu_price integer,
  keto_score integer,
  keto_reasons jsonb,
  ilike_score float,
  source_url text  -- ✅ 추가된 필드
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    r.id AS restaurant_id,
    r.name AS restaurant_name,
    r.category AS restaurant_category,
    r.addr_road,
    r.addr_jibun,
    r.lat,
    r.lng,
    r.phone,
    m.id AS menu_id,
    m.name AS menu_name,
    m.description AS menu_description,
    m.price AS menu_price,
    ks.score AS keto_score,
    ks.reasons_json AS keto_reasons,
    1.0 AS ilike_score,
    r.source_url  -- ✅ source_url 추가
  FROM menu m
  JOIN restaurant r ON m.restaurant_id = r.id
  LEFT JOIN keto_scores ks ON ks.menu_id = m.id
  WHERE m.name ILIKE '%' || query_text || '%'
     OR r.name ILIKE '%' || query_text || '%'
     OR r.category ILIKE '%' || query_text || '%'
  LIMIT match_count;
$$;

-- 권한 설정
GRANT EXECUTE ON FUNCTION restaurant_ilike_search TO anon;
GRANT EXECUTE ON FUNCTION restaurant_ilike_search TO authenticated;

COMMENT ON FUNCTION restaurant_ilike_search IS 
'식당 메뉴 ILIKE 검색 (source_url 포함) - 백엔드 키워드 검색에서 사용';


-- 3️⃣ Trigram 유사도 검색 RPC 함수 (source_url 포함) ⭐ 주요 수정
-- 백엔드에서 실제로 호출하는 함수
DROP FUNCTION IF EXISTS restaurant_trgm_search(text, integer, double precision);

CREATE OR REPLACE FUNCTION restaurant_trgm_search(
  query_text text,
  match_count int DEFAULT 10,
  similarity_threshold float DEFAULT 0.3
)
RETURNS TABLE (
  restaurant_id uuid,
  restaurant_name text,
  restaurant_category text,
  addr_road text,
  addr_jibun text,
  lat double precision,
  lng double precision,
  phone text,
  menu_id uuid,
  menu_name text,
  menu_description text,
  menu_price integer,
  keto_score integer,
  keto_reasons jsonb,
  trigram_score float,
  source_url text  -- ✅ 추가된 필드
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    r.id AS restaurant_id,
    r.name AS restaurant_name,
    r.category AS restaurant_category,
    r.addr_road,
    r.addr_jibun,
    r.lat,
    r.lng,
    r.phone,
    m.id AS menu_id,
    m.name AS menu_name,
    m.description AS menu_description,
    m.price AS menu_price,
    ks.score AS keto_score,
    ks.reasons_json AS keto_reasons,
    similarity(m.name, query_text) AS trigram_score,
    r.source_url  -- ✅ source_url 추가
  FROM menu m
  JOIN restaurant r ON m.restaurant_id = r.id
  LEFT JOIN keto_scores ks ON ks.menu_id = m.id
  WHERE similarity(m.name, query_text) >= similarity_threshold
  ORDER BY similarity(m.name, query_text) DESC
  LIMIT match_count;
$$;

-- 권한 설정
GRANT EXECUTE ON FUNCTION restaurant_trgm_search TO anon;
GRANT EXECUTE ON FUNCTION restaurant_trgm_search TO authenticated;

COMMENT ON FUNCTION restaurant_trgm_search IS 
'식당 메뉴 Trigram 검색 (source_url 포함) - 백엔드 키워드 검색에서 사용';


-- 4️⃣ 검증 쿼리
-- 벡터 검색 테스트 (더미 임베딩 사용)
SELECT 
  restaurant_name, 
  menu_name, 
  source_url,
  similarity_score
FROM restaurant_menu_vector_search(
  (SELECT embedding FROM menu_embedding LIMIT 1),  -- 샘플 임베딩
  5,  -- 결과 5개
  0.4  -- 임계값 0.4
)
LIMIT 5;

-- ILIKE 키워드 검색 테스트 ⭐ 주요 검증
SELECT 
  restaurant_name, 
  menu_name, 
  source_url,
  ilike_score
FROM restaurant_ilike_search('삼겹살', 5)
LIMIT 5;

-- Trigram 유사도 검색 테스트 ⭐ 주요 검증
SELECT 
  restaurant_name, 
  menu_name, 
  source_url,
  trigram_score
FROM restaurant_trgm_search('삼겹살', 5, 0.3)
LIMIT 5;

-- =========================================================
-- 실행 완료 후 확인사항
-- =========================================================
-- ✅ 1. source_url 필드가 NULL이 아닌지 확인
-- ✅ 2. 백엔드 로그에서 "📎 ... source_url 보완:" 메시지가 사라지는지 확인
-- ✅ 3. 네트워크 탭에서 /rest/v1/restaurant?select=source_url&id=... GET 호출이 없는지 확인
-- ✅ 4. 기존 백엔드 코드에서 fallback 로직(260-274줄) 제거 가능
-- 
-- 예상 성능 개선:
-- - DB 호출 횟수: N+1회 → 1회 (N = 식당 개수)
-- - 식당 3개 추천: 250ms → 120ms (52% 개선)
-- - 식당 10개 추천: 600ms → 150ms (75% 개선)
-- 
-- 근본 원인 해결:
-- - restaurant_ilike_search와 restaurant_trgm_search의 RETURNS TABLE에 source_url 추가
-- - SELECT 절에 r.source_url 추가로 N+1 문제 완전 해결
-- =========================================================

