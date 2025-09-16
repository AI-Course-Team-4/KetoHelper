-- Supabase RPC 함수들 (recipes_keto_enhanced 테이블 참조로 수정)
-- Supabase SQL Editor에서 실행

-- 1) 벡터 검색 RPC 함수 (recipes_keto_enhanced 테이블 참조)
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
    r.blob as content,
    1 - (r.embedding <=> query_embedding) as similarity_score
  FROM recipes_keto_enhanced r
  WHERE r.embedding IS NOT NULL
    AND 1 - (r.embedding <=> query_embedding) > similarity_threshold
  ORDER BY r.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 2) Trigram 유사도 검색 RPC 함수 (recipes_keto_enhanced 테이블 참조)
CREATE OR REPLACE FUNCTION trgm_search(
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
    r.blob as content,
    GREATEST(
      similarity(r.title, query_text),
      similarity(r.blob, query_text)
    ) as similarity_score
  FROM recipes_keto_enhanced r
  WHERE r.title % query_text 
     OR r.blob % query_text
  ORDER BY similarity_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 3) Full-Text Search RPC 함수 (recipes_keto_enhanced 테이블 참조)
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
    r.blob as content,
    ts_rank(to_tsvector('korean', r.title), plainto_tsquery('korean', query_text)) +
    ts_rank(to_tsvector('korean', r.blob), plainto_tsquery('korean', query_text)) as fts_score
  FROM recipes_keto_enhanced r
  WHERE to_tsvector('korean', r.title) @@ plainto_tsquery('korean', query_text)
     OR to_tsvector('korean', r.blob) @@ plainto_tsquery('korean', query_text)
  ORDER BY fts_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 4) ILIKE 검색 RPC 함수 (recipes_keto_enhanced 테이블 참조)
CREATE OR REPLACE FUNCTION ilike_search(
  query_text TEXT,
  match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  search_score FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    r.id,
    r.title,
    r.blob as content,
    CASE 
      WHEN r.title ILIKE '%' || query_text || '%' THEN 0.8
      WHEN r.blob ILIKE '%' || query_text || '%' THEN 0.6
      ELSE 0.4
    END as search_score
  FROM recipes_keto_enhanced r
  WHERE r.title ILIKE '%' || query_text || '%'
     OR r.blob ILIKE '%' || query_text || '%'
  ORDER BY search_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 5) 통합 하이브리드 검색 RPC 함수 (recipes_keto_enhanced 테이블 참조)
CREATE OR REPLACE FUNCTION hybrid_search(
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
  hybrid_score FLOAT
) AS $$
DECLARE
  vector_weight FLOAT := 0.4;
  keyword_weight FLOAT := 0.6;
BEGIN
  RETURN QUERY
  WITH vector_results AS (
    SELECT 
      r.id,
      r.title,
      r.blob as content,
      1 - (r.embedding <=> query_embedding) as vector_score,
      0.0::FLOAT as keyword_score
    FROM recipes_keto_enhanced r
    WHERE r.embedding IS NOT NULL
    ORDER BY r.embedding <=> query_embedding
    LIMIT match_count
  ),
  keyword_results AS (
    SELECT 
      r.id,
      r.title,
      r.blob as content,
      0.0::FLOAT as vector_score,
      GREATEST(
        CASE WHEN r.title ILIKE '%' || query_text || '%' THEN 0.8 ELSE 0.0 END,
        CASE WHEN r.blob ILIKE '%' || query_text || '%' THEN 0.6 ELSE 0.0 END,
        similarity(r.title, query_text),
        similarity(r.blob, query_text)
      ) as keyword_score
    FROM recipes_keto_enhanced r
    WHERE r.title ILIKE '%' || query_text || '%'
       OR r.blob ILIKE '%' || query_text || '%'
       OR r.title % query_text
       OR r.blob % query_text
    ORDER BY keyword_score DESC
    LIMIT match_count
  ),
  combined_results AS (
    SELECT * FROM vector_results
    UNION ALL
    SELECT * FROM keyword_results
  )
  SELECT 
    cr.id,
    cr.title,
    cr.content,
    cr.vector_score,
    cr.keyword_score,
    (cr.vector_score * vector_weight + cr.keyword_score * keyword_weight) as hybrid_score
  FROM combined_results cr
  ORDER BY hybrid_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 6) PGroonga 검색 RPC 함수 (recipes_keto_enhanced 테이블 참조)
CREATE OR REPLACE FUNCTION groonga_search(
  query_text TEXT,
  match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  search_score FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    r.id,
    r.title,
    r.blob as content,
    GREATEST(
      CASE WHEN r.title ILIKE '%' || query_text || '%' THEN 0.8 ELSE 0.0 END,
      CASE WHEN r.blob ILIKE '%' || query_text || '%' THEN 0.6 ELSE 0.0 END
    ) as search_score
  FROM recipes_keto_enhanced r
  WHERE r.title ILIKE '%' || query_text || '%'
     OR r.blob ILIKE '%' || query_text || '%'
  ORDER BY search_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 7) 완료 메시지
SELECT 'Supabase RPC 함수들 수정 완료! (recipes_keto_enhanced 테이블 참조)' as result;
