-- 한글 검색 최적화를 위한 PostgreSQL 확장 및 인덱스 설정
-- Supabase SQL Editor에서 실행

-- 1) pg_trgm 확장 설치 (유사도 검색용)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2) 한국어 Full-Text Search 설정
-- PostgreSQL의 기본 한국어 설정 사용 (simple, korean 등)
-- 참고: PostgreSQL 12+ 에서는 'korean' 설정이 기본 제공됨

-- 3) 레시피 테이블에 검색용 컬럼 추가 (선택사항)
-- 기존 content 컬럼을 활용하거나 별도 검색용 컬럼 생성
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS search_content TEXT;
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS search_title TEXT;

-- 4) 검색용 컬럼 업데이트 (기존 데이터 반영)
UPDATE recipes SET 
  search_content = COALESCE(title, '') || ' ' || 
                   COALESCE(array_to_string(tags, ' '), '') || ' ' ||
                   COALESCE(array_to_string(steps, ' '), '') || ' ' ||
                   COALESCE(array_to_string(tips, ' '), ''),
  search_title = COALESCE(title, '')
WHERE search_content IS NULL;

-- 5) Full-Text Search용 GIN 인덱스 생성
-- 제목 검색용
CREATE INDEX IF NOT EXISTS idx_recipes_title_fts 
  ON recipes USING gin(to_tsvector('korean', search_title));

-- 내용 검색용  
CREATE INDEX IF NOT EXISTS idx_recipes_content_fts 
  ON recipes USING gin(to_tsvector('korean', search_content));

-- 6) Trigram 유사도 검색용 인덱스 생성
-- 제목 유사도 검색용
CREATE INDEX IF NOT EXISTS idx_recipes_title_trgm 
  ON recipes USING gin(search_title gin_trgm_ops);

-- 내용 유사도 검색용
CREATE INDEX IF NOT EXISTS idx_recipes_content_trgm 
  ON recipes USING gin(search_content gin_trgm_ops);

-- 7) 기존 ILIKE 검색용 인덱스 (호환성 유지)
CREATE INDEX IF NOT EXISTS idx_recipes_title_ilike 
  ON recipes (title);

CREATE INDEX IF NOT EXISTS idx_recipes_content_ilike 
  ON recipes (content);

-- 8) 하이브리드 검색용 RPC 함수 개선
CREATE OR REPLACE FUNCTION hybrid_search_optimized(
  query_text TEXT,
  query_embedding VECTOR(1536),
  match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  vector_score FLOAT,
  keyword_score FLOAT,
  hybrid_score FLOAT,
  search_type TEXT
) AS $$
DECLARE
  vector_results RECORD;
  keyword_results RECORD;
  fts_results RECORD;
  trigram_results RECORD;
  combined_score FLOAT;
BEGIN
  -- 1. 벡터 검색 (기존)
  FOR vector_results IN
    SELECT 
      r.id,
      r.title,
      r.content,
      1 - (re.embedding <=> query_embedding) as vector_score
    FROM recipes r
    JOIN recipe_embeddings re ON r.id = re.recipe_id
    ORDER BY re.embedding <=> query_embedding
    LIMIT match_count
  LOOP
    id := vector_results.id;
    title := vector_results.title;
    content := vector_results.content;
    vector_score := vector_results.vector_score;
    keyword_score := 0.0;
    hybrid_score := vector_score * 0.7; -- 벡터 검색 가중치 70%
    search_type := 'vector';
    RETURN NEXT;
  END LOOP;

  -- 2. Full-Text Search (한글 최적화)
  FOR fts_results IN
    SELECT 
      r.id,
      r.title,
      r.content,
      ts_rank(to_tsvector('korean', r.search_title), plainto_tsquery('korean', query_text)) +
      ts_rank(to_tsvector('korean', r.search_content), plainto_tsquery('korean', query_text)) as fts_score
    FROM recipes r
    WHERE to_tsvector('korean', r.search_title) @@ plainto_tsquery('korean', query_text)
       OR to_tsvector('korean', r.search_content) @@ plainto_tsquery('korean', query_text)
    ORDER BY fts_score DESC
    LIMIT match_count
  LOOP
    id := fts_results.id;
    title := fts_results.title;
    content := fts_results.content;
    vector_score := 0.0;
    keyword_score := LEAST(fts_results.fts_score, 1.0);
    hybrid_score := keyword_score * 0.3; -- FTS 검색 가중치 30%
    search_type := 'fts';
    RETURN NEXT;
  END LOOP;

  -- 3. Trigram 유사도 검색 (한글 유사도)
  FOR trigram_results IN
    SELECT 
      r.id,
      r.title,
      r.content,
      similarity(r.search_title, query_text) +
      similarity(r.search_content, query_text) as trigram_score
    FROM recipes r
    WHERE r.search_title % query_text 
       OR r.search_content % query_text
    ORDER BY trigram_score DESC
    LIMIT match_count
  LOOP
    id := trigram_results.id;
    title := trigram_results.title;
    content := trigram_results.content;
    vector_score := 0.0;
    keyword_score := LEAST(trigram_results.trigram_score, 1.0);
    hybrid_score := keyword_score * 0.2; -- Trigram 검색 가중치 20%
    search_type := 'trigram';
    RETURN NEXT;
  END LOOP;

  -- 4. 기존 ILIKE 검색 (폴백)
  FOR keyword_results IN
    SELECT 
      r.id,
      r.title,
      r.content,
      CASE 
        WHEN r.title ILIKE '%' || query_text || '%' THEN 0.8
        WHEN r.content ILIKE '%' || query_text || '%' THEN 0.6
        ELSE 0.4
      END as ilike_score
    FROM recipes r
    WHERE r.title ILIKE '%' || query_text || '%'
       OR r.content ILIKE '%' || query_text || '%'
    ORDER BY ilike_score DESC
    LIMIT match_count
  LOOP
    id := keyword_results.id;
    title := keyword_results.title;
    content := keyword_results.content;
    vector_score := 0.0;
    keyword_score := keyword_results.ilike_score;
    hybrid_score := keyword_score * 0.1; -- ILIKE 검색 가중치 10%
    search_type := 'ilike';
    RETURN NEXT;
  END LOOP;

END;
$$ LANGUAGE plpgsql;

-- 9) 성능 모니터링용 뷰 생성
CREATE OR REPLACE VIEW search_performance_stats AS
SELECT 
  'recipes' as table_name,
  COUNT(*) as total_records,
  pg_size_pretty(pg_total_relation_size('recipes')) as table_size,
  pg_size_pretty(pg_indexes_size('recipes')) as indexes_size
FROM recipes;

-- 10) 검색 성능 테스트 함수
CREATE OR REPLACE FUNCTION test_korean_search_performance()
RETURNS TABLE (
  search_method TEXT,
  query_time_ms FLOAT,
  result_count INTEGER
) AS $$
DECLARE
  start_time TIMESTAMP;
  end_time TIMESTAMP;
  test_query TEXT := '키토 불고기';
  result_count INTEGER;
BEGIN
  -- FTS 검색 테스트
  start_time := clock_timestamp();
  SELECT COUNT(*) INTO result_count
  FROM recipes r
  WHERE to_tsvector('korean', r.search_title) @@ plainto_tsquery('korean', test_query)
     OR to_tsvector('korean', r.search_content) @@ plainto_tsquery('korean', test_query);
  end_time := clock_timestamp();
  
  search_method := 'Full-Text Search';
  query_time_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time));
  result_count := result_count;
  RETURN NEXT;

  -- Trigram 검색 테스트
  start_time := clock_timestamp();
  SELECT COUNT(*) INTO result_count
  FROM recipes r
  WHERE r.search_title % test_query 
     OR r.search_content % test_query;
  end_time := clock_timestamp();
  
  search_method := 'Trigram Similarity';
  query_time_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time));
  result_count := result_count;
  RETURN NEXT;

  -- ILIKE 검색 테스트
  start_time := clock_timestamp();
  SELECT COUNT(*) INTO result_count
  FROM recipes r
  WHERE r.title ILIKE '%' || test_query || '%'
     OR r.content ILIKE '%' || test_query || '%';
  end_time := clock_timestamp();
  
  search_method := 'ILIKE Pattern';
  query_time_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time));
  result_count := result_count;
  RETURN NEXT;

END;
$$ LANGUAGE plpgsql;

-- 11) 완료 메시지
SELECT '한글 검색 최적화 설정 완료!' as result;
