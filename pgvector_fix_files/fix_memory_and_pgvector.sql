-- 1. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 메모리 설정 임시 증가 (인덱스 생성용)
SET maintenance_work_mem = '128MB';

-- 3. 기존 인덱스 삭제
DROP INDEX IF EXISTS recipes_hybrid_ingredient_llm_embedding_ivfflat;

-- 4. 올바른 ivfflat 인덱스 생성 (메모리 증가 후)
CREATE INDEX recipes_hybrid_ingredient_llm_embedding_ivfflat
ON recipes_hybrid_ingredient_llm USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 5. search_hybrid_recipes 함수 수정
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

-- 6. 메모리 설정 원복 (선택사항)
-- SET maintenance_work_mem = '32MB';
