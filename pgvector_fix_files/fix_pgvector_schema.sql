-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 기존 테이블에 올바른 vector 컬럼 추가
ALTER TABLE recipes_hybrid_ingredient_llm ADD COLUMN embedding_vec vector(1536);

-- 기존 embedding 컬럼의 데이터를 vector 타입으로 변환
-- JSON 배열 문자열을 vector로 변환
UPDATE recipes_hybrid_ingredient_llm 
SET embedding_vec = (
  SELECT array_agg((e)::float4)::vector
  FROM jsonb_array_elements_text(embedding::jsonb) AS x(e)
)
WHERE embedding IS NOT NULL;

-- 기존 embedding 컬럼 삭제
ALTER TABLE recipes_hybrid_ingredient_llm DROP COLUMN embedding;

-- 새로운 컬럼을 embedding으로 이름 변경
ALTER TABLE recipes_hybrid_ingredient_llm RENAME COLUMN embedding_vec TO embedding;

-- 올바른 ivfflat 인덱스 생성 (코사인 유사도 기준)
CREATE INDEX IF NOT EXISTS recipes_hybrid_ingredient_llm_embedding_ivfflat
ON recipes_hybrid_ingredient_llm USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 기존 search_hybrid_recipes 함수도 vector 타입에 맞게 수정
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
