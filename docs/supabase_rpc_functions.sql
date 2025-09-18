-- Supabase RPC 함수들 (한글 검색 최적화)
-- Supabase SQL Editor에서 실행

-- 1) 벡터 검색 RPC 함수
CREATE OR REPLACE FUNCTION vector_search(
  query_embedding VECTOR(1536),
  match_count INTEGER DEFAULT 5,
  similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  similarity_score FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    r.id,
    r.title,
    r.content,
    1 - (re.embedding <=> query_embedding) as similarity_score
  FROM recipes r
  JOIN recipe_embeddings re ON r.id = re.recipe_id
  WHERE 1 - (re.embedding <=> query_embedding) > similarity_threshold
  ORDER BY re.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 2) Trigram 유사도 검색 RPC 함수
CREATE OR REPLACE FUNCTION trigram_search(
  query_text TEXT,
  match_count INTEGER DEFAULT 5,
  similarity_threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  similarity_score FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    r.id,
    r.title,
    r.content,
    GREATEST(
      similarity(r.search_title, query_text),
      similarity(r.search_content, query_text)
    ) as similarity_score
  FROM recipes r
  WHERE r.search_title % query_text 
     OR r.search_content % query_text
  ORDER BY similarity_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 3) Full-Text Search RPC 함수
CREATE OR REPLACE FUNCTION fts_search(
  query_text TEXT,
  match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  fts_score FLOAT
) AS $$
BEGIN
  RETURN QUERY
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
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 4) 통합 하이브리드 검색 RPC 함수 (개선된 버전)
CREATE OR REPLACE FUNCTION hybrid_search_v2(
  query_text TEXT,
  query_embedding VECTOR(1536),
  match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  vector_score FLOAT,
  fts_score FLOAT,
  trigram_score FLOAT,
  ilike_score FLOAT,
  final_score FLOAT,
  search_type TEXT
) AS $$
DECLARE
  vector_weight FLOAT := 0.4;
  fts_weight FLOAT := 0.3;
  trigram_weight FLOAT := 0.2;
  ilike_weight FLOAT := 0.1;
BEGIN
  RETURN QUERY
  WITH vector_results AS (
    SELECT 
      r.id,
      r.title,
      r.content,
      1 - (re.embedding <=> query_embedding) as vector_score,
      0.0::FLOAT as fts_score,
      0.0::FLOAT as trigram_score,
      0.0::FLOAT as ilike_score,
      'vector'::TEXT as search_type
    FROM recipes r
    JOIN recipe_embeddings re ON r.id = re.recipe_id
    ORDER BY re.embedding <=> query_embedding
    LIMIT match_count
  ),
  fts_results AS (
    SELECT 
      r.id,
      r.title,
      r.content,
      0.0::FLOAT as vector_score,
      ts_rank(to_tsvector('korean', r.search_title), plainto_tsquery('korean', query_text)) +
      ts_rank(to_tsvector('korean', r.search_content), plainto_tsquery('korean', query_text)) as fts_score,
      0.0::FLOAT as trigram_score,
      0.0::FLOAT as ilike_score,
      'fts'::TEXT as search_type
    FROM recipes r
    WHERE to_tsvector('korean', r.search_title) @@ plainto_tsquery('korean', query_text)
       OR to_tsvector('korean', r.search_content) @@ plainto_tsquery('korean', query_text)
    ORDER BY fts_score DESC
    LIMIT match_count
  ),
  trigram_results AS (
    SELECT 
      r.id,
      r.title,
      r.content,
      0.0::FLOAT as vector_score,
      0.0::FLOAT as fts_score,
      GREATEST(
        similarity(r.search_title, query_text),
        similarity(r.search_content, query_text)
      ) as trigram_score,
      0.0::FLOAT as ilike_score,
      'trigram'::TEXT as search_type
    FROM recipes r
    WHERE r.search_title % query_text 
       OR r.search_content % query_text
    ORDER BY trigram_score DESC
    LIMIT match_count
  ),
  ilike_results AS (
    SELECT 
      r.id,
      r.title,
      r.content,
      0.0::FLOAT as vector_score,
      0.0::FLOAT as fts_score,
      0.0::FLOAT as trigram_score,
      CASE 
        WHEN r.title ILIKE '%' || query_text || '%' THEN 0.8
        WHEN r.content ILIKE '%' || query_text || '%' THEN 0.6
        ELSE 0.4
      END as ilike_score,
      'ilike'::TEXT as search_type
    FROM recipes r
    WHERE r.title ILIKE '%' || query_text || '%'
       OR r.content ILIKE '%' || query_text || '%'
    ORDER BY ilike_score DESC
    LIMIT match_count
  ),
  combined_results AS (
    SELECT * FROM vector_results
    UNION ALL
    SELECT * FROM fts_results
    UNION ALL
    SELECT * FROM trigram_results
    UNION ALL
    SELECT * FROM ilike_results
  )
  SELECT 
    cr.id,
    cr.title,
    cr.content,
    cr.vector_score,
    cr.fts_score,
    cr.trigram_score,
    cr.ilike_score,
    (cr.vector_score * vector_weight + 
     cr.fts_score * fts_weight + 
     cr.trigram_score * trigram_weight + 
     cr.ilike_score * ilike_weight) as final_score,
    cr.search_type
  FROM combined_results cr
  ORDER BY final_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 5) 검색 성능 테스트 함수
CREATE OR REPLACE FUNCTION test_search_performance(
  test_query TEXT DEFAULT '키토 불고기'
)
RETURNS TABLE (
  search_method TEXT,
  execution_time_ms FLOAT,
  result_count INTEGER,
  avg_score FLOAT
) AS $$
DECLARE
  start_time TIMESTAMP;
  end_time TIMESTAMP;
  result_count INTEGER;
  avg_score FLOAT;
BEGIN
  -- 벡터 검색 테스트
  start_time := clock_timestamp();
  SELECT COUNT(*), AVG(1 - (re.embedding <=> (SELECT embedding FROM recipe_embeddings LIMIT 1)))
  INTO result_count, avg_score
  FROM recipes r
  JOIN recipe_embeddings re ON r.id = re.recipe_id
  WHERE 1 - (re.embedding <=> (SELECT embedding FROM recipe_embeddings LIMIT 1)) > 0.7;
  end_time := clock_timestamp();
  
  search_method := 'Vector Search';
  execution_time_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time));
  result_count := result_count;
  avg_score := COALESCE(avg_score, 0.0);
  RETURN NEXT;

  -- FTS 검색 테스트
  start_time := clock_timestamp();
  SELECT COUNT(*), AVG(ts_rank(to_tsvector('korean', r.search_title), plainto_tsquery('korean', test_query)))
  INTO result_count, avg_score
  FROM recipes r
  WHERE to_tsvector('korean', r.search_title) @@ plainto_tsquery('korean', test_query);
  end_time := clock_timestamp();
  
  search_method := 'Full-Text Search';
  execution_time_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time));
  result_count := result_count;
  avg_score := COALESCE(avg_score, 0.0);
  RETURN NEXT;

  -- Trigram 검색 테스트
  start_time := clock_timestamp();
  SELECT COUNT(*), AVG(similarity(r.search_title, test_query))
  INTO result_count, avg_score
  FROM recipes r
  WHERE r.search_title % test_query;
  end_time := clock_timestamp();
  
  search_method := 'Trigram Similarity';
  execution_time_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time));
  result_count := result_count;
  avg_score := COALESCE(avg_score, 0.0);
  RETURN NEXT;

  -- ILIKE 검색 테스트
  start_time := clock_timestamp();
  SELECT COUNT(*), 0.5::FLOAT
  INTO result_count, avg_score
  FROM recipes r
  WHERE r.title ILIKE '%' || test_query || '%';
  end_time := clock_timestamp();
  
  search_method := 'ILIKE Pattern';
  execution_time_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time));
  result_count := result_count;
  avg_score := avg_score;
  RETURN NEXT;

END;
$$ LANGUAGE plpgsql;

-- 6) 완료 메시지
SELECT 'Supabase RPC 함수들 설정 완료!' as result;
