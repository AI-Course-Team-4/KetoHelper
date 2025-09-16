-- 완전한 RPC 함수들 (기존 테이블 사용)

-- 1. vector_search 함수 (recipes_keto_raw 테이블 사용)
CREATE OR REPLACE FUNCTION vector_search(
  query_embedding VECTOR(1536),
  match_count INTEGER DEFAULT 5,
  similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  similarity_score DOUBLE PRECISION
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    r.id,
    r.title,
    r.blob as content,
    (1 - (r.embedding <=> query_embedding))::DOUBLE PRECISION as similarity_score
  FROM recipes_keto_raw r
  WHERE r.embedding IS NOT NULL
    AND (1 - (r.embedding <=> query_embedding)) > similarity_threshold
  ORDER BY r.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 2. ilike_search 함수 (recipes_keto_raw 테이블 사용)
CREATE OR REPLACE FUNCTION ilike_search(
  query_text TEXT,
  match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  search_score DOUBLE PRECISION
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
    END::DOUBLE PRECISION as search_score
  FROM recipes_keto_raw r
  WHERE r.title ILIKE '%' || query_text || '%'
     OR r.blob ILIKE '%' || query_text || '%'
  ORDER BY search_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 3. trgm_search 함수 (recipes_keto_raw 테이블 사용)
CREATE OR REPLACE FUNCTION trgm_search(
  query_text TEXT,
  match_count INTEGER DEFAULT 5,
  similarity_threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  similarity_score DOUBLE PRECISION
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
    )::DOUBLE PRECISION as similarity_score
  FROM recipes_keto_raw r
  WHERE r.title % query_text
     OR r.blob % query_text
  ORDER BY similarity_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 4. fts_search 함수 (recipes_keto_raw 테이블 사용)
CREATE OR REPLACE FUNCTION fts_search(
  query_text TEXT,
  match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  fts_score DOUBLE PRECISION
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    r.id,
    r.title,
    r.blob as content,
    (ts_rank(to_tsvector('simple', r.title), plainto_tsquery('simple', query_text)) +
     ts_rank(to_tsvector('simple', r.blob), plainto_tsquery('simple', query_text)))::DOUBLE PRECISION as fts_score
  FROM recipes_keto_raw r
  WHERE to_tsvector('simple', r.title) @@ plainto_tsquery('simple', query_text)
     OR to_tsvector('simple', r.blob) @@ plainto_tsquery('simple', query_text)
  ORDER BY fts_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
