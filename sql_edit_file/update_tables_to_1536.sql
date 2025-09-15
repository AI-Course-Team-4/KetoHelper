-- OpenAI text-embedding-3-small (1536차원)으로 테이블 업데이트
-- Supabase SQL Editor에서 실행

-- 기존 테이블들 삭제
DROP TABLE IF EXISTS recipes_title_blob CASCADE;
DROP TABLE IF EXISTS recipes_no_title_blob CASCADE;
DROP TABLE IF EXISTS recipes_llm_preprocessing CASCADE;

-- 1536차원으로 새 테이블 생성
CREATE TABLE recipes_title_blob (
    id BIGSERIAL PRIMARY KEY,
    recipe_id TEXT UNIQUE,
    title TEXT,
    processed_content TEXT,
    raw_content JSONB,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE recipes_no_title_blob (
    id BIGSERIAL PRIMARY KEY,
    recipe_id TEXT UNIQUE,
    title TEXT,
    processed_content TEXT,
    raw_content JSONB,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE recipes_llm_preprocessing (
    id BIGSERIAL PRIMARY KEY,
    recipe_id TEXT UNIQUE,
    title TEXT,
    processed_content TEXT,
    raw_content JSONB,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);

-- 벡터 검색 인덱스 생성
CREATE INDEX ON recipes_title_blob USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON recipes_no_title_blob USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON recipes_llm_preprocessing USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 벡터 검색 함수 업데이트 (1536차원)
CREATE OR REPLACE FUNCTION search_recipes(
  query_embedding vector(1536),
  table_name text,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  recipe_id text,
  title text,
  processed_content text,
  raw_content jsonb,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  EXECUTE format('
    SELECT r.recipe_id, r.title, r.processed_content, r.raw_content, r.metadata,
           1 - (r.embedding <=> $1) as similarity
    FROM %I r
    ORDER BY r.embedding <=> $1
    LIMIT $2
  ', table_name)
  USING query_embedding, match_count;
END;
$$;
