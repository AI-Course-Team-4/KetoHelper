-- 🏗️ MVP 크롤링 시스템 초기 스키마 v1.0
-- 단순하고 확장 가능한 구조로 설계

-- 확장 프로그램 설치
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 📍 식당 테이블 (restaurants)
CREATE TABLE restaurants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 🎯 기본 정보 (크롤링으로 수집)
    name TEXT NOT NULL,                    -- "강남 맛집" (필수)
    address_road TEXT,                     -- "서울시 강남구 테헤란로 123" (도로명)
    address_jibun TEXT,                    -- "서울시 강남구 역삼동 123-45" (지번)
    lat DECIMAL(9,6),                      -- 위도 (37.123456)
    lng DECIMAL(9,6),                      -- 경도 (127.123456)
    
    -- 📞 연락 정보
    phone TEXT,                            -- "02-1234-5678"
    homepage_url TEXT,                     -- 홈페이지 URL
    
    -- 🍽️ 카테고리 정보
    category TEXT,                         -- "한식", "중식", "양식" 등
    cuisine_type TEXT,                     -- 더 세분화된 요리 타입
    
    -- ⭐ 평점 정보
    rating DECIMAL(3,2),                   -- 평점 (0.00-5.00)
    review_count INTEGER DEFAULT 0,        -- 리뷰 개수
    
    -- 🕐 운영 정보
    business_hours TEXT,                   -- 영업시간 정보
    
    -- 🔍 크롤링 메타데이터
    source TEXT NOT NULL,                  -- "siksin", "diningcode", "mangoplate"
    source_url TEXT NOT NULL,              -- 원본 페이지 URL
    source_id TEXT,                        -- 사이트 내 식당 ID
    
    -- 📊 데이터 품질
    quality_score INTEGER DEFAULT 0,       -- 데이터 품질 점수 (0-100)
    last_verified_at TIMESTAMPTZ,          -- 마지막 검증 시간
    
    -- 🕒 시스템 필드
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT restaurants_lat_check CHECK (lat BETWEEN -90 AND 90),
    CONSTRAINT restaurants_lng_check CHECK (lng BETWEEN -180 AND 180),
    CONSTRAINT restaurants_rating_check CHECK (rating BETWEEN 0 AND 5),
    CONSTRAINT restaurants_quality_score_check CHECK (quality_score BETWEEN 0 AND 100)
);

-- 🍜 메뉴 테이블 (menus)
CREATE TABLE menus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    
    -- 🎯 기본 메뉴 정보
    name TEXT NOT NULL,                    -- "김치찌개" (필수)
    price INTEGER,                         -- 가격 (원 단위, NULL 허용)
    currency TEXT DEFAULT 'KRW',           -- 통화
    description TEXT,                      -- 메뉴 설명
    
    -- 🏷️ 메뉴 분류
    category TEXT,                         -- "메인요리", "사이드메뉴", "음료" 등
    is_signature BOOLEAN DEFAULT FALSE,    -- 대표 메뉴 여부
    is_recommended BOOLEAN DEFAULT FALSE,  -- 추천 메뉴 여부
    
    -- 🖼️ 이미지 정보  
    image_url TEXT,                        -- 메뉴 이미지 URL
    
    -- 📊 메뉴 인기도
    popularity_score INTEGER DEFAULT 0,    -- 인기도 점수 (0-100)
    order_count INTEGER DEFAULT 0,         -- 주문 횟수 (추정)
    
    -- 🕒 시스템 필드
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT menus_price_check CHECK (price IS NULL OR price > 0),
    CONSTRAINT menus_popularity_check CHECK (popularity_score BETWEEN 0 AND 100)
);

-- 📋 크롤링 작업 테이블 (crawl_jobs)
CREATE TABLE crawl_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 🎯 작업 정보
    job_type TEXT NOT NULL,                -- "search", "detail"
    site TEXT NOT NULL,                    -- "siksin", "diningcode"
    url TEXT NOT NULL,                     -- 크롤링 대상 URL
    keyword TEXT,                          -- 검색 키워드 (search 타입의 경우)
    
    -- 📊 작업 상태
    status TEXT NOT NULL DEFAULT 'queued', -- "queued", "running", "completed", "failed"
    priority INTEGER DEFAULT 0,            -- 우선순위 (높을수록 먼저 처리)
    attempts INTEGER DEFAULT 0,            -- 시도 횟수
    max_attempts INTEGER DEFAULT 3,        -- 최대 시도 횟수
    
    -- ❌ 오류 정보
    last_error_code TEXT,                  -- 마지막 오류 코드
    last_error_message TEXT,               -- 마지막 오류 메시지
    last_error_at TIMESTAMPTZ,             -- 마지막 오류 발생 시간
    
    -- ⏱️ 시간 정보
    scheduled_at TIMESTAMPTZ DEFAULT NOW(), -- 예약 시간
    started_at TIMESTAMPTZ,                -- 시작 시간
    completed_at TIMESTAMPTZ,              -- 완료 시간
    
    -- 🕒 시스템 필드
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT crawl_jobs_status_check CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT crawl_jobs_job_type_check CHECK (job_type IN ('search', 'detail', 'batch')),
    CONSTRAINT crawl_jobs_attempts_check CHECK (attempts >= 0 AND attempts <= max_attempts)
);

-- 💾 원본 스냅샷 테이블 (raw_snapshots) - 백업용
CREATE TABLE raw_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 🎯 엔터티 정보
    entity_type TEXT NOT NULL,             -- "restaurant", "menu", "search_result"
    entity_id UUID,                        -- 연결된 엔터티 ID
    
    -- 📄 원본 데이터
    source TEXT NOT NULL,                  -- "siksin", "diningcode"
    source_url TEXT NOT NULL,              -- 원본 URL
    raw_html TEXT,                         -- 원본 HTML
    parsed_data JSONB,                     -- 파싱된 JSON 데이터
    
    -- 📊 메타데이터
    content_hash TEXT,                     -- 콘텐츠 해시 (중복 감지용)
    content_length INTEGER,                -- 콘텐츠 길이
    parsing_success BOOLEAN DEFAULT TRUE,  -- 파싱 성공 여부
    
    -- 🕒 시스템 필드
    fetched_at TIMESTAMPTZ DEFAULT NOW(),  -- 크롤링 시간
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT raw_snapshots_entity_type_check CHECK (entity_type IN ('restaurant', 'menu', 'search_result'))
);

-- 📊 크롤링 통계 테이블 (crawl_stats)
CREATE TABLE crawl_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 📅 통계 기간
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    hour INTEGER,                          -- 시간별 통계 (NULL이면 일별)
    site TEXT NOT NULL,                    -- 사이트명
    
    -- 📈 크롤링 통계
    total_requests INTEGER DEFAULT 0,      -- 총 요청 수
    successful_requests INTEGER DEFAULT 0, -- 성공 요청 수
    failed_requests INTEGER DEFAULT 0,     -- 실패 요청 수
    blocked_requests INTEGER DEFAULT 0,    -- 차단된 요청 수
    
    -- 📊 데이터 수집 통계
    restaurants_collected INTEGER DEFAULT 0, -- 수집된 식당 수
    menus_collected INTEGER DEFAULT 0,       -- 수집된 메뉴 수
    duplicates_found INTEGER DEFAULT 0,      -- 발견된 중복 수
    
    -- ⏱️ 성능 통계
    avg_response_time DECIMAL(5,2),        -- 평균 응답시간 (초)
    max_response_time DECIMAL(5,2),        -- 최대 응답시간 (초)
    
    -- 🕒 시스템 필드
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 제약 조건
    UNIQUE(date, hour, site)
);

-- 📋 인덱스 생성
-- restaurants 테이블 인덱스
CREATE INDEX idx_restaurants_name ON restaurants(name);
CREATE INDEX idx_restaurants_location ON restaurants(lat, lng);
CREATE INDEX idx_restaurants_source ON restaurants(source);
CREATE INDEX idx_restaurants_category ON restaurants(category);
CREATE INDEX idx_restaurants_rating ON restaurants(rating DESC);
CREATE INDEX idx_restaurants_created_at ON restaurants(created_at);
CREATE INDEX idx_restaurants_quality_score ON restaurants(quality_score DESC);

-- 중복 방지를 위한 복합 인덱스
CREATE UNIQUE INDEX idx_restaurants_source_unique ON restaurants(source, source_url);
CREATE INDEX idx_restaurants_dedup ON restaurants(name, address_road) WHERE address_road IS NOT NULL;

-- menus 테이블 인덱스
CREATE INDEX idx_menus_restaurant_id ON menus(restaurant_id);
CREATE INDEX idx_menus_name ON menus(name);
CREATE INDEX idx_menus_price ON menus(price);
CREATE INDEX idx_menus_category ON menus(category);
CREATE INDEX idx_menus_signature ON menus(is_signature) WHERE is_signature = true;

-- 중복 방지를 위한 복합 인덱스
CREATE UNIQUE INDEX idx_menus_unique ON menus(restaurant_id, name);

-- crawl_jobs 테이블 인덱스
CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_jobs_site_status ON crawl_jobs(site, status);
CREATE INDEX idx_crawl_jobs_priority ON crawl_jobs(priority DESC, created_at);
CREATE INDEX idx_crawl_jobs_scheduled ON crawl_jobs(scheduled_at) WHERE status = 'queued';

-- raw_snapshots 테이블 인덱스
CREATE INDEX idx_raw_snapshots_entity ON raw_snapshots(entity_type, entity_id);
CREATE INDEX idx_raw_snapshots_source ON raw_snapshots(source, fetched_at);
CREATE INDEX idx_raw_snapshots_hash ON raw_snapshots(content_hash);

-- crawl_stats 테이블 인덱스
CREATE INDEX idx_crawl_stats_date_site ON crawl_stats(date, site);
CREATE INDEX idx_crawl_stats_site_hour ON crawl_stats(site, date, hour);

-- 📊 뷰 생성 - 크롤링 대시보드용
CREATE VIEW crawl_dashboard AS
SELECT 
    source as site,
    COUNT(*) as total_restaurants,
    COUNT(CASE WHEN lat IS NOT NULL AND lng IS NOT NULL THEN 1 END) as restaurants_with_coords,
    ROUND(AVG(quality_score), 2) as avg_quality_score,
    COUNT(CASE WHEN quality_score >= 70 THEN 1 END) as high_quality_count,
    MAX(created_at) as last_crawl_time
FROM restaurants 
GROUP BY source;

-- 메뉴 통계 뷰
CREATE VIEW menu_stats AS
SELECT 
    r.source as site,
    COUNT(m.*) as total_menus,
    COUNT(CASE WHEN m.price IS NOT NULL THEN 1 END) as menus_with_price,
    ROUND(AVG(m.price), 0) as avg_price,
    COUNT(CASE WHEN m.is_signature THEN 1 END) as signature_menus
FROM restaurants r
LEFT JOIN menus m ON r.id = m.restaurant_id
GROUP BY r.source;

-- 📋 트리거 생성 - updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- restaurants 테이블 트리거
CREATE TRIGGER update_restaurants_updated_at 
    BEFORE UPDATE ON restaurants 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- menus 테이블 트리거
CREATE TRIGGER update_menus_updated_at 
    BEFORE UPDATE ON menus 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- crawl_jobs 테이블 트리거
CREATE TRIGGER update_crawl_jobs_updated_at 
    BEFORE UPDATE ON crawl_jobs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- crawl_stats 테이블 트리거
CREATE TRIGGER update_crawl_stats_updated_at 
    BEFORE UPDATE ON crawl_stats 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 💡 데이터 품질 함수
CREATE OR REPLACE FUNCTION calculate_restaurant_quality(restaurant_row restaurants)
RETURNS INTEGER AS $$
DECLARE
    score INTEGER := 0;
BEGIN
    -- 기본 정보 점수 (70점)
    IF restaurant_row.name IS NOT NULL THEN score := score + 20; END IF;
    IF restaurant_row.address_road IS NOT NULL THEN score := score + 15; END IF;
    IF restaurant_row.lat IS NOT NULL AND restaurant_row.lng IS NOT NULL THEN score := score + 20; END IF;
    IF restaurant_row.phone IS NOT NULL THEN score := score + 10; END IF;
    IF restaurant_row.category IS NOT NULL THEN score := score + 5; END IF;
    
    -- 추가 정보 점수 (30점)
    IF restaurant_row.rating IS NOT NULL THEN score := score + 10; END IF;
    IF restaurant_row.business_hours IS NOT NULL THEN score := score + 5; END IF;
    IF restaurant_row.homepage_url IS NOT NULL THEN score := score + 5; END IF;
    
    -- 메뉴 정보 보너스
    IF (SELECT COUNT(*) FROM menus WHERE restaurant_id = restaurant_row.id) > 0 THEN 
        score := score + 10;
    END IF;
    
    RETURN LEAST(score, 100); -- 최대 100점
END;
$$ LANGUAGE plpgsql;

-- 🔄 품질 점수 업데이트 트리거
CREATE OR REPLACE FUNCTION update_restaurant_quality()
RETURNS TRIGGER AS $$
BEGIN
    NEW.quality_score := calculate_restaurant_quality(NEW.*);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_restaurant_quality
    BEFORE INSERT OR UPDATE ON restaurants
    FOR EACH ROW
    EXECUTE FUNCTION update_restaurant_quality();

-- 📝 초기 설정 완료 로그
INSERT INTO crawl_stats (date, site, total_requests) 
VALUES (CURRENT_DATE, 'system', 0)
ON CONFLICT DO NOTHING;

-- 🎉 스키마 생성 완료
COMMENT ON DATABASE restaurant_crawler IS 'MVP 식당 크롤링 시스템 - v1.0';

-- 테이블 설명
COMMENT ON TABLE restaurants IS '식당 기본 정보 - 크롤링으로 수집';
COMMENT ON TABLE menus IS '메뉴 정보 - 식당별 메뉴 리스트';  
COMMENT ON TABLE crawl_jobs IS '크롤링 작업 큐 - 비동기 처리용';
COMMENT ON TABLE raw_snapshots IS '원본 데이터 스냅샷 - 백업 및 디버깅용';
COMMENT ON TABLE crawl_stats IS '크롤링 통계 - 모니터링용';