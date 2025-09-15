-- Enhanced Blob Approach 테이블 생성
-- 더 풍부한 콘텐츠로 임베딩하여 검색 정확도 향상

-- 1. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Enhanced Blob 테이블 생성
CREATE TABLE recipes_enhanced_blob (
    id BIGSERIAL PRIMARY KEY,
    recipe_id TEXT UNIQUE,
    title TEXT,
    description TEXT,
    tags JSONB,
    ingredients JSONB,
    cooking_method TEXT,
    enhanced_blob TEXT,  -- 개선된 blob 콘텐츠
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);

-- 3. 벡터 검색을 위한 ivfflat 인덱스 생성
CREATE INDEX recipes_enhanced_blob_embedding_ivfflat
ON recipes_enhanced_blob USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 4. Enhanced Blob 검색 함수 생성
CREATE OR REPLACE FUNCTION search_enhanced_recipes(
  query_embedding vector(1536),
  match_count int DEFAULT 10
)
RETURNS TABLE (
  recipe_id text,
  title text,
  enhanced_blob text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT r.recipe_id, r.title, r.enhanced_blob, r.metadata,
         1 - (r.embedding <=> $1) as similarity
  FROM recipes_enhanced_blob r
  ORDER BY r.embedding <=> $1
  LIMIT $2;
END;
$$;

-- 5. 키워드 검색을 위한 GIN 인덱스 생성 (기본 설정 사용)
CREATE INDEX recipes_enhanced_blob_enhanced_blob_gin
ON recipes_enhanced_blob USING gin (to_tsvector('english', enhanced_blob));
