-- 레스토랑 메뉴 벡터 검색 데이터베이스 설정
-- 새로운 Supabase 프로젝트에서 실행

-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- restaurants 테이블 생성
CREATE TABLE restaurants (
    id SERIAL PRIMARY KEY,
    restaurant_name VARCHAR(255) NOT NULL,
    menu_name VARCHAR(255) NOT NULL,
    key_ingredients TEXT[],
    short_description TEXT,
    combined_text TEXT,
    embedding VECTOR(1536),
    search_vector tsvector,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- search_vector 자동 업데이트를 위한 함수
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.restaurant_name, '') || ' ' ||
        COALESCE(NEW.menu_name, '') || ' ' ||
        COALESCE(array_to_string(NEW.key_ingredients, ' '), '') || ' ' ||
        COALESCE(NEW.short_description, '')
    );
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
CREATE TRIGGER restaurants_search_vector_trigger
    BEFORE INSERT OR UPDATE ON restaurants
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- 벡터 검색 함수
CREATE OR REPLACE FUNCTION vector_search(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id INT,
    restaurant_name VARCHAR(255),
    menu_name VARCHAR(255),
    key_ingredients TEXT[],
    short_description TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.restaurant_name,
        r.menu_name,
        r.key_ingredients,
        r.short_description,
        1 - (r.embedding <-> query_embedding) AS similarity
    FROM restaurants r
    WHERE r.embedding IS NOT NULL
    AND 1 - (r.embedding <-> query_embedding) > match_threshold
    ORDER BY r.embedding <-> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 키워드 검색 함수
CREATE OR REPLACE FUNCTION keyword_search(
    search_query TEXT,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id INT,
    restaurant_name VARCHAR(255),
    menu_name VARCHAR(255),
    key_ingredients TEXT[],
    short_description TEXT,
    rank FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.restaurant_name,
        r.menu_name,
        r.key_ingredients,
        r.short_description,
        ts_rank(r.search_vector, to_tsquery('english', search_query)) AS rank
    FROM restaurants r
    WHERE r.search_vector @@ to_tsquery('english', search_query)
    ORDER BY ts_rank(r.search_vector, to_tsquery('english', search_query)) DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 키워드 검색을 위한 GIN 인덱스
CREATE INDEX restaurants_search_vector_idx 
ON restaurants USING gin(search_vector);

-- 일반적인 검색을 위한 인덱스들
CREATE INDEX restaurants_restaurant_name_idx ON restaurants(restaurant_name);
CREATE INDEX restaurants_menu_name_idx ON restaurants(menu_name);
CREATE INDEX restaurants_created_at_idx ON restaurants(created_at);

-- 데이터 확인용 뷰
CREATE OR REPLACE VIEW restaurant_summary AS
SELECT 
    restaurant_name,
    COUNT(*) as menu_count,
    array_agg(menu_name ORDER BY menu_name) as menu_names
FROM restaurants
GROUP BY restaurant_name
ORDER BY restaurant_name;

-- 통계 정보 확인용 뷰
CREATE OR REPLACE VIEW database_stats AS
SELECT 
    'Total Restaurants' as metric,
    COUNT(DISTINCT restaurant_name)::TEXT as value
FROM restaurants
UNION ALL
SELECT 
    'Total Menu Items' as metric,
    COUNT(*)::TEXT as value
FROM restaurants
UNION ALL
SELECT 
    'Items with Embeddings' as metric,
    COUNT(*)::TEXT as value
FROM restaurants
WHERE embedding IS NOT NULL;

-- 설정 완료 확인
SELECT 'Database setup completed successfully!' as status;
SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_name = 'restaurants';
SELECT COUNT(*) as function_count FROM information_schema.routines WHERE routine_name IN ('vector_search', 'keyword_search');
SELECT COUNT(*) as view_count FROM information_schema.views WHERE table_name IN ('restaurant_summary', 'database_stats');
