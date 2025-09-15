-- 1. pgvector 확장 활성화 (이미 활성화되어 있을 수 있음)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 현재 embedding 컬럼이 vector 타입인지 확인
-- (이미 vector 타입이므로 추가 작업 불필요)

-- 3. 올바른 ivfflat 인덱스 생성 (기존 인덱스가 있다면 삭제 후 재생성)
DROP INDEX IF EXISTS recipes_hybrid_ingredient_llm_embedding_ivfflat;
CREATE INDEX recipes_hybrid_ingredient_llm_embedding_ivfflat
ON recipes_hybrid_ingredient_llm USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 4. search_hybrid_recipes 함수 수정 (vector 타입에 맞게)
CREATE OR REPLACE FUNCTION search_hybrid_recipes(
  query_embedding vector(1536),
  match_count int DEFAULT 10
)
RETURNS TABLE (
  recipe_id text,
  title text,
  structured_blob text,
  llm_metadata jsonb,
  basic_metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT r.recipe_id, r.title, r.structured_blob, r.llm_metadata, r.basic_metadata,
         1 - (r.embedding <=> $1) as similarity
  FROM recipes_hybrid_ingredient_llm r
  ORDER BY r.embedding <=> $1
  LIMIT $2;
END;
$$;

-- 5. 테스트 쿼리 (선택사항)
-- SELECT * FROM search_hybrid_recipes('[0.1,0.2,0.3]'::vector, 5);
