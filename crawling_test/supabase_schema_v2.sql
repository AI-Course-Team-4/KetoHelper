-- 정규화된 3개 테이블 구조로 업데이트된 Supabase 스키마
-- 이 스크립트를 Supabase 대시보드의 SQL Editor에서 실행하세요

-- 1. pgvector extension 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. restaurants 테이블 (식당 기본 정보)
CREATE TABLE IF NOT EXISTS restaurants (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    jibun_address TEXT,
    category TEXT,
    rating DECIMAL(2,1),
    phone TEXT,
    image_url TEXT,
    source TEXT DEFAULT 'manual',  -- 'manual', 'siksin_crawler', 'naver' 등
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. menus 테이블 (메뉴 정보 + 임베딩)
CREATE TABLE IF NOT EXISTS menus (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    price INTEGER,
    description TEXT,
    menu_text TEXT,  -- 검색용: "restaurant_name + menu_name + address"
    embedding VECTOR(1536),
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. crawling_logs 테이블 (크롤링 이력 관리)
CREATE TABLE IF NOT EXISTS crawling_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    site TEXT NOT NULL,  -- 'siksin', 'naver', 'kakao'
    status TEXT DEFAULT 'success',  -- 'success', 'failed', 'partial'
    menus_count INTEGER DEFAULT 0,
    error_message TEXT,
    crawled_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. 인덱스 생성
-- restaurants 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_restaurants_name ON restaurants (name);
CREATE INDEX IF NOT EXISTS idx_restaurants_source ON restaurants (source);
CREATE INDEX IF NOT EXISTS idx_restaurants_created_at ON restaurants (created_at);

-- menus 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_menus_restaurant_id ON menus (restaurant_id);
CREATE INDEX IF NOT EXISTS idx_menus_name ON menus (name);
CREATE INDEX IF NOT EXISTS idx_menus_price ON menus (price);

-- crawling_logs 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_crawling_logs_restaurant_id ON crawling_logs (restaurant_id);
CREATE INDEX IF NOT EXISTS idx_crawling_logs_site ON crawling_logs (site);
CREATE INDEX IF NOT EXISTS idx_crawling_logs_status ON crawling_logs (status);
CREATE INDEX IF NOT EXISTS idx_crawling_logs_crawled_at ON crawling_logs (crawled_at);

-- 6. 벡터 검색 함수 업데이트 (JOIN 포함)
CREATE OR REPLACE FUNCTION vector_search_with_restaurant(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.0,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    menu_id UUID,
    menu_name TEXT,
    menu_price INTEGER,
    restaurant_id UUID,
    restaurant_name TEXT,
    restaurant_address TEXT,
    restaurant_category TEXT,
    menu_text TEXT,
    similarity FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        m.id AS menu_id,
        m.name AS menu_name,
        m.price AS menu_price,
        r.id AS restaurant_id,
        r.name AS restaurant_name,
        r.address AS restaurant_address,
        r.category AS restaurant_category,
        m.menu_text,
        1 - (m.embedding <=> query_embedding) AS similarity
    FROM menus m
    JOIN restaurants r ON m.restaurant_id = r.id
    WHERE m.embedding IS NOT NULL
        AND 1 - (m.embedding <=> query_embedding) > match_threshold
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- 7. RLS (Row Level Security) 설정 (선택사항)
-- ALTER TABLE restaurants ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE menus ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE crawling_logs ENABLE ROW LEVEL SECURITY;

-- 8. 테스트 쿼리
SELECT 'Supabase V2 스키마 설정 완료!' AS status;

-- 기존 menus 테이블이 있다면 백업 후 제거
-- (주의: 데이터 손실 가능성 있음. 필요시 수동으로 마이그레이션)
-- DROP TABLE IF EXISTS menus_old;
-- ALTER TABLE menus RENAME TO menus_old;
