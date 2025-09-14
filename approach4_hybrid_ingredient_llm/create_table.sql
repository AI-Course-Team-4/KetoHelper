-- Approach 4: 하이브리드 식재료 LLM 전처리 테이블 생성
-- Supabase SQL Editor에서 실행

CREATE TABLE recipes_hybrid_ingredient_llm (
    id BIGSERIAL PRIMARY KEY,
    recipe_id TEXT UNIQUE,
    title TEXT,
    raw_ingredients JSONB,           -- 원본 식재료 데이터
    normalized_ingredients JSONB,    -- 정규화된 식재료
    llm_metadata JSONB,              -- LLM 분석 결과
    basic_metadata JSONB,            -- 방식2 기본 정보
    structured_blob TEXT,            -- 최종 구조화된 blob
    embedding vector(1536),          -- OpenAI text-embedding-3-small
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);

-- 벡터 검색 인덱스 생성
CREATE INDEX ON recipes_hybrid_ingredient_llm USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 검색 성능을 위한 추가 인덱스
CREATE INDEX ON recipes_hybrid_ingredient_llm (recipe_id);
CREATE INDEX ON recipes_hybrid_ingredient_llm (title);

-- JSONB 컬럼 인덱스 (LLM 메타데이터 검색용)
CREATE INDEX ON recipes_hybrid_ingredient_llm USING gin (llm_metadata);
CREATE INDEX ON recipes_hybrid_ingredient_llm USING gin (raw_ingredients);

-- 벡터 검색 함수 (1536차원)
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

-- 테이블 구조 확인
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'recipes_hybrid_ingredient_llm'
ORDER BY ordinal_position;
