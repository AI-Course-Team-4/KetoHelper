-- Supabase 설정 SQL 스크립트
-- 이 스크립트를 Supabase 대시보드의 SQL Editor에서 실행하세요

-- 1. pgvector extension 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. menus 테이블 생성
CREATE TABLE IF NOT EXISTS menus (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    restaurant_name TEXT NOT NULL,
    address TEXT NOT NULL,
    menu_name TEXT NOT NULL,
    price INTEGER,
    menu_text TEXT,
    embedding vector(1536),
    source TEXT DEFAULT 'manual',
    category TEXT,
    rating DECIMAL(2,1),
    image_url TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 인덱스 생성
CREATE UNIQUE INDEX IF NOT EXISTS idx_menus_unique 
ON menus (restaurant_name, address, menu_name);

CREATE INDEX IF NOT EXISTS idx_menus_source ON menus (source);
CREATE INDEX IF NOT EXISTS idx_menus_category ON menus (category);

-- 4. 벡터 검색 함수 생성
CREATE OR REPLACE FUNCTION vector_search(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.0,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    restaurant_name text,
    address text,
    menu_name text,
    price integer,
    category text,
    menu_text text,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        menus.id,
        menus.restaurant_name,
        menus.address,
        menus.menu_name,
        menus.price,
        menus.category,
        menus.menu_text,
        1 - (menus.embedding <=> query_embedding) AS similarity
    FROM menus
    WHERE menus.embedding IS NOT NULL
        AND 1 - (menus.embedding <=> query_embedding) > match_threshold
    ORDER BY menus.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- 5. RLS (Row Level Security) 설정 (선택사항)
-- ALTER TABLE menus ENABLE ROW LEVEL SECURITY;

-- 6. 테스트 쿼리
SELECT 'Supabase 설정 완료!' AS status;
