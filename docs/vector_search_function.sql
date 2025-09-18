-- vector_search RPC 함수 생성
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
  FROM recipes_keto_enhanced r
  WHERE r.embedding IS NOT NULL
    AND (1 - (r.embedding <=> query_embedding)) > similarity_threshold
  ORDER BY r.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
