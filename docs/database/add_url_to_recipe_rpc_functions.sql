-- =========================================================
-- 레시피 검색 RPC 함수에 URL 필드 추가
-- 2025-01-11: 레시피 검색 결과에 출처 URL 포함
--
-- ⚠️ 주의사항:
-- 1. 이 스크립트는 기존 함수를 삭제하고 재생성합니다
-- 2. CASCADE 없이 삭제하므로 의존성이 있으면 오류가 발생합니다
-- 3. 만약 의존성 오류가 발생하면 의존 객체를 먼저 확인하세요
-- 4. 백업 환경에서 먼저 테스트하는 것을 권장합니다
-- 5. 프로덕션 환경에서는 트래픽이 적은 시간에 실행하세요
-- =========================================================

-- 의존성 확인 쿼리 (실행 전 확인용)
-- SELECT 
--     dependent_ns.nspname as dependent_schema,
--     dependent_view.relname as dependent_view,
--     source_table.relname as source_table
-- FROM pg_depend 
-- JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid 
-- JOIN pg_class as dependent_view ON pg_rewrite.ev_class = dependent_view.oid 
-- JOIN pg_class as source_table ON pg_depend.refobjid = source_table.oid 
-- JOIN pg_namespace dependent_ns ON dependent_ns.oid = dependent_view.relnamespace
-- JOIN pg_namespace source_ns ON source_ns.oid = source_table.relnamespace
-- JOIN pg_proc ON pg_depend.refobjid = pg_proc.oid
-- WHERE pg_proc.proname IN ('vector_search', 'ilike_search', 'fts_search', 'trgm_search');

-- 1. vector_search 함수 수정 (벡터 검색)
-- 기존 함수를 DROP하고 url 필드를 포함하여 재생성
-- 모든 오버로드를 동적으로 삭제
DO $$
DECLARE
    func_signature text;
BEGIN
    FOR func_signature IN
        SELECT format('%s(%s)', p.proname, pg_get_function_identity_arguments(p.oid))
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE p.proname = 'vector_search'
          AND n.nspname = 'public'
    LOOP
        -- CASCADE 제거: 의존성이 있으면 오류 발생하도록 (안전)
        EXECUTE format('DROP FUNCTION IF EXISTS %s', func_signature);
    END LOOP;
END $$;

CREATE OR REPLACE FUNCTION vector_search(
    query_embedding vector(1536),
    match_count integer DEFAULT 5,
    similarity_threshold float DEFAULT 0.0,
    exclude_allergens_embedding vector(1536) DEFAULT NULL,
    exclude_dislikes_embedding vector(1536) DEFAULT NULL,
    exclude_allergens_names text[] DEFAULT NULL,
    exclude_dislikes_names text[] DEFAULT NULL,
    meal_type_filter text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    title text,
    content text,
    ingredients text[],
    allergens text[],
    tags text[],
    meal_type text,
    url text,  -- URL 필드 추가
    similarity_score float,
    search_score float
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rbe.id,
        rbe.title,
        rbe.blob::text as content,
        rbe.ingredients,
        rbe.allergens,
        rbe.tags,
        rbe.meal_type,
        rbe.url,  -- URL 필드 추가
        1 - (rbe.embedding <=> query_embedding) as similarity_score,
        1 - (rbe.embedding <=> query_embedding) as search_score
    FROM recipe_blob_emb rbe
    WHERE 
        (meal_type_filter IS NULL OR rbe.meal_type = meal_type_filter)
        AND (1 - (rbe.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY rbe.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 2. ilike_search 함수 수정 (ILIKE 검색)
DO $$
DECLARE
    func_signature text;
BEGIN
    FOR func_signature IN
        SELECT format('%s(%s)', p.proname, pg_get_function_identity_arguments(p.oid))
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE p.proname = 'ilike_search'
          AND n.nspname = 'public'
    LOOP
        -- CASCADE 제거: 의존성이 있으면 오류 발생하도록 (안전)
        EXECUTE format('DROP FUNCTION IF EXISTS %s', func_signature);
    END LOOP;
END $$;

CREATE OR REPLACE FUNCTION ilike_search(
    query_text text,
    match_count integer DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    title text,
    content text,
    ingredients text[],
    allergens text[],
    tags text[],
    meal_type text,
    url text,  -- URL 필드 추가
    search_score float
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rbe.id,
        rbe.title,
        rbe.blob::text as content,
        rbe.ingredients,
        rbe.allergens,
        rbe.tags,
        rbe.meal_type,
        rbe.url,  -- URL 필드 추가
        1.0 as search_score
    FROM recipe_blob_emb rbe
    WHERE rbe.title ILIKE '%' || query_text || '%'
    ORDER BY 
        CASE WHEN rbe.title ILIKE query_text THEN 1
             WHEN rbe.title ILIKE query_text || '%' THEN 2
             WHEN rbe.title ILIKE '%' || query_text THEN 3
             ELSE 4 
        END
    LIMIT match_count;
END;
$$;

-- 3. fts_search 함수 수정 (Full-Text Search)
DO $$
DECLARE
    func_signature text;
BEGIN
    FOR func_signature IN
        SELECT format('%s(%s)', p.proname, pg_get_function_identity_arguments(p.oid))
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE p.proname = 'fts_search'
          AND n.nspname = 'public'
    LOOP
        -- CASCADE 제거: 의존성이 있으면 오류 발생하도록 (안전)
        EXECUTE format('DROP FUNCTION IF EXISTS %s', func_signature);
    END LOOP;
END $$;

CREATE OR REPLACE FUNCTION fts_search(
    query_text text,
    match_count integer DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    title text,
    content text,
    ingredients text[],
    allergens text[],
    tags text[],
    meal_type text,
    url text,  -- URL 필드 추가
    search_score float,
    fts_score float
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rbe.id,
        rbe.title,
        rbe.blob::text as content,
        rbe.ingredients,
        rbe.allergens,
        rbe.tags,
        rbe.meal_type,
        rbe.url,  -- URL 필드 추가
        ts_rank(to_tsvector('korean', rbe.title), plainto_tsquery('korean', query_text)) as search_score,
        ts_rank(to_tsvector('korean', rbe.title), plainto_tsquery('korean', query_text)) as fts_score
    FROM recipe_blob_emb rbe
    WHERE to_tsvector('korean', rbe.title) @@ plainto_tsquery('korean', query_text)
    ORDER BY fts_score DESC
    LIMIT match_count;
END;
$$;

-- 4. trgm_search 함수 수정 (Trigram 유사도 검색)
DO $$
DECLARE
    func_signature text;
BEGIN
    FOR func_signature IN
        SELECT format('%s(%s)', p.proname, pg_get_function_identity_arguments(p.oid))
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE p.proname = 'trgm_search'
          AND n.nspname = 'public'
    LOOP
        -- CASCADE 제거: 의존성이 있으면 오류 발생하도록 (안전)
        EXECUTE format('DROP FUNCTION IF EXISTS %s', func_signature);
    END LOOP;
END $$;

CREATE OR REPLACE FUNCTION trgm_search(
    query_text text,
    match_count integer DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    title text,
    content text,
    ingredients text[],
    allergens text[],
    tags text[],
    meal_type text,
    url text,  -- URL 필드 추가
    search_score float,
    similarity_score float
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rbe.id,
        rbe.title,
        rbe.blob::text as content,
        rbe.ingredients,
        rbe.allergens,
        rbe.tags,
        rbe.meal_type,
        rbe.url,  -- URL 필드 추가
        similarity(rbe.title, query_text) as search_score,
        similarity(rbe.title, query_text) as similarity_score
    FROM recipe_blob_emb rbe
    WHERE similarity(rbe.title, query_text) > 0.3
    ORDER BY similarity_score DESC
    LIMIT match_count;
END;
$$;

-- 권한 부여
GRANT EXECUTE ON FUNCTION vector_search TO anon, authenticated;
GRANT EXECUTE ON FUNCTION ilike_search TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fts_search TO anon, authenticated;
GRANT EXECUTE ON FUNCTION trgm_search TO anon, authenticated;

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '✅ 레시피 검색 RPC 함수에 URL 필드 추가 완료';
    RAISE NOTICE '   - vector_search';
    RAISE NOTICE '   - ilike_search';
    RAISE NOTICE '   - fts_search';
    RAISE NOTICE '   - trgm_search';
END $$;

