-- 현실적인 메뉴 풍부화 스키마 (단계별 구현 가능)
CREATE TABLE menus (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    
    -- 🎯 기본 정보 (크롤링으로 수집 - 90%+ 달성 가능)
    name TEXT NOT NULL,                    -- "닭개장" (크롤링 기본)
    price INTEGER,                         -- 8000 (대부분 사이트에서 제공)
    description TEXT,                      -- "얼큰하고 시원한 닭고기 국물요리" (80% 가능)
    
    -- 🎯 규칙 기반 풍부화 (85%+ 달성 가능)
    category TEXT,                         -- "국물요리", "볶음요리", "구이" 등 (메뉴명 패턴 매칭)
    cuisine_type TEXT,                     -- "한식", "중식", "양식", "일식" 등 (식당 카테고리 기반)
    spice_level INTEGER CHECK (spice_level BETWEEN 1 AND 5), -- 1(안매움) ~ 5(매우매움) (키워드 매칭)
    temperature TEXT CHECK (temperature IN ('뜨거운', '차가운', '실온')), -- 메뉴명/설명 기반
    cooking_method TEXT,                   -- "끓임", "볶음", "구이", "튀김" (메뉴명 패턴)
    
    -- 🎯 검색 풍부화 (70%+ 달성 가능)
    main_ingredients TEXT[],               -- ["닭고기", "대파", "콩나물", "고춧가루"] (검색 보완)
    dietary_tags TEXT[],                   -- ["단백질", "국물", "매운맛", "든든한"] (규칙 + 검색)
    allergens TEXT[],                      -- ["없음"] 또는 ["견과류", "유제품"] (검색으로 보완)
    serving_size TEXT,                     -- "1인분", "2-3인분" (설명에서 추출)
    
    -- 🎯 고도화 필드 (40-60% 달성 가능)
    meal_time TEXT[],                      -- ["점심", "저녁", "해장"] (추가 로직 필요)
    
    -- 🎯 검색용 텍스트 (90%+ 달성 가능)
    menu_text TEXT,                        -- 풍부해진 검색용 텍스트 (다른 필드 조합)
    menu_text_hash TEXT,                   -- 텍스트 변경 감지용 해시
    
    -- 🎯 기타 정보
    image_url TEXT,                        -- 이미지 URL (크롤링으로 수집)
    
    -- 🎯 풍부화 메타데이터
    enrichment_source TEXT CHECK (enrichment_source IN ('raw', 'rule', 'search', 'llm', 'hybrid')), -- 풍부화 소스 추적
    enrichment_confidence DECIMAL(3,2) CHECK (enrichment_confidence BETWEEN 0.0 AND 1.0), -- 풍부화 신뢰도
    enrichment_updated_at TIMESTAMPTZ,     -- 풍부화 마지막 업데이트 시간
    
    -- 🎯 시스템 필드
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_menus_restaurant_id ON menus(restaurant_id);
CREATE INDEX idx_menus_category ON menus(category);
CREATE INDEX idx_menus_cuisine_type ON menus(cuisine_type);
CREATE INDEX idx_menus_spice_level ON menus(spice_level);
CREATE INDEX idx_menus_cooking_method ON menus(cooking_method);
CREATE INDEX idx_menus_enrichment_confidence ON menus(enrichment_confidence);
CREATE INDEX idx_menus_created_at ON menus(created_at);

-- 임베딩 테이블 (별도 분리)
CREATE TABLE menu_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_id UUID NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    
    -- 임베딩 메타데이터
    model_name TEXT NOT NULL DEFAULT 'text-embedding-3-small', -- 임베딩 모델명
    model_version TEXT,                                        -- 모델 버전
    dimension INTEGER NOT NULL DEFAULT 1536,                   -- 벡터 차원
    algorithm_version TEXT DEFAULT 'RAG-v1.0',                -- 알고리즘 버전
    
    -- 임베딩 데이터
    embedding VECTOR(1536) NOT NULL,                          -- 실제 벡터 데이터
    content_hash TEXT NOT NULL,                               -- 원본 텍스트 해시
    
    -- 시스템 필드
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 제약조건
    UNIQUE(menu_id, model_name, algorithm_version)            -- 메뉴당 모델별 유니크
);

-- 임베딩 테이블 인덱스
CREATE INDEX idx_menu_embeddings_menu_id ON menu_embeddings(menu_id);
CREATE INDEX idx_menu_embeddings_model ON menu_embeddings(model_name);
CREATE INDEX idx_menu_embeddings_content_hash ON menu_embeddings(content_hash);
CREATE INDEX idx_menu_embeddings_created_at ON menu_embeddings(created_at);

-- 벡터 인덱스 (pgvector) - 임베딩 테이블에만
CREATE INDEX idx_menu_embeddings_vector ON menu_embeddings USING hnsw (embedding vector_cosine_ops);

-- 풍부화 품질 점수 계산 함수
CREATE OR REPLACE FUNCTION calculate_enrichment_quality(menu_row menus) 
RETURNS INTEGER AS $$
DECLARE
    quality_score INTEGER := 0;
BEGIN
    -- 기본 필드 점수 (40점)
    IF menu_row.name IS NOT NULL THEN quality_score := quality_score + 10; END IF;
    IF menu_row.price IS NOT NULL THEN quality_score := quality_score + 10; END IF;
    IF menu_row.description IS NOT NULL THEN quality_score := quality_score + 10; END IF;
    IF menu_row.category IS NOT NULL THEN quality_score := quality_score + 10; END IF;
    
    -- 풍부화 필드 점수 (60점)
    IF menu_row.cuisine_type IS NOT NULL THEN quality_score := quality_score + 10; END IF;
    IF menu_row.spice_level IS NOT NULL THEN quality_score := quality_score + 10; END IF;
    IF menu_row.cooking_method IS NOT NULL THEN quality_score := quality_score + 10; END IF;
    IF menu_row.main_ingredients IS NOT NULL AND array_length(menu_row.main_ingredients, 1) >= 2 THEN 
        quality_score := quality_score + 15; 
    END IF;
    IF menu_row.dietary_tags IS NOT NULL AND array_length(menu_row.dietary_tags, 1) >= 1 THEN 
        quality_score := quality_score + 10; 
    END IF;
    IF menu_row.allergens IS NOT NULL THEN quality_score := quality_score + 5; END IF;
    
    RETURN quality_score;
END;
$$ LANGUAGE plpgsql;

-- 풍부화 품질 뷰
CREATE VIEW menu_enrichment_quality AS
SELECT 
    id,
    name,
    category,
    cuisine_type,
    spice_level,
    cooking_method,
    array_length(main_ingredients, 1) as ingredient_count,
    array_length(dietary_tags, 1) as tag_count,
    enrichment_source,
    enrichment_confidence,
    calculate_enrichment_quality(menus.*) as quality_score,
    CASE 
        WHEN calculate_enrichment_quality(menus.*) >= 80 THEN 'High'
        WHEN calculate_enrichment_quality(menus.*) >= 60 THEN 'Medium'
        ELSE 'Low'
    END as quality_grade
FROM menus;

-- 풍부화 통계 뷰
CREATE VIEW menu_enrichment_stats AS
SELECT 
    enrichment_source,
    quality_grade,
    COUNT(*) as count,
    ROUND(AVG(quality_score), 2) as avg_quality_score,
    ROUND(AVG(enrichment_confidence), 3) as avg_confidence
FROM menu_enrichment_quality
GROUP BY enrichment_source, quality_grade
ORDER BY enrichment_source, quality_grade;

-- 풍부화 업데이트 트리거
CREATE OR REPLACE FUNCTION update_menu_enrichment_metadata()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.enrichment_updated_at = NOW();
    
    -- 풍부화 신뢰도 자동 계산
    NEW.enrichment_confidence = LEAST(calculate_enrichment_quality(NEW.*) / 100.0, 1.0);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_menu_enrichment
    BEFORE UPDATE ON menus
    FOR EACH ROW
    EXECUTE FUNCTION update_menu_enrichment_metadata();

-- 풍부화 품질 기준
COMMENT ON TABLE menus IS '메뉴 정보 및 풍부화된 메타데이터 저장';
COMMENT ON COLUMN menus.enrichment_source IS '풍부화 소스: raw(원본), rule(규칙), search(검색), llm(LLM), hybrid(혼합)';
COMMENT ON COLUMN menus.enrichment_confidence IS '풍부화 신뢰도 (0.0-1.0)';
COMMENT ON COLUMN menus.quality_score IS '품질 점수: 0-100 (80+ High, 60+ Medium, <60 Low)';

-- 풍부화 목표 달성률
/*
🎯 풍부화 목표 달성률 (현실적 예상):

Phase 1 (기본 풍부화):
- name: 100% (크롤링 기본)
- price: 90% (대부분 사이트에서 제공)
- description: 80% (식신, 다이닝코드에서 제공)
- category: 85% (메뉴명 패턴 매칭)
- cuisine_type: 90% (식당 카테고리 기반)
- spice_level: 75% (키워드 매칭)
- temperature: 80% (메뉴명/설명 기반)
- cooking_method: 85% (메뉴명 패턴)

Phase 2 (검색 풍부화):
- main_ingredients: 70% → 85% (검색 보완)
- dietary_tags: 60% (규칙 + 검색)
- allergens: 50% (검색으로 보완)
- serving_size: 65% (설명에서 추출)

Phase 3 (고도화):
- meal_time: 40% (추가 로직 필요)
- menu_text: 90% (다른 필드 조합)
- menu_embeddings: 100% (menu_text 기반, 별도 테이블)

전체 품질 점수 목표: 70점 이상 (Medium 등급)
*/
