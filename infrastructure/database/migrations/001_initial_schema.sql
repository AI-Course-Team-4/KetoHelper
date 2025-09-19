-- 초기 데이터베이스 스키마
-- PostgreSQL 14+ 기준

-- 확장 기능 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 텍스트 유사도 검색
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- GIN 인덱스 최적화

-- 열거형 정의
DO $$
BEGIN
    -- 탄수화물 베이스 타입
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'carb_base') THEN
        CREATE TYPE carb_base AS ENUM (
            'rice',           -- 밥류
            'noodle',         -- 면류
            'bread',          -- 빵류
            'none',           -- 탄수화물 없음
            'konjac_rice',    -- 곤약밥
            'cauli_rice',     -- 콜리플라워 라이스
            'tofu_noodle',    -- 두부면
            'unknown'         -- 알 수 없음
        );
    END IF;

    -- 소스 타입
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'source_type') THEN
        CREATE TYPE source_type AS ENUM (
            'diningcode',
            'siksin',
            'mangoplate',
            'yogiyo',
            'manual'
        );
    END IF;

    -- 메뉴 카테고리 타입
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'menu_category') THEN
        CREATE TYPE menu_category AS ENUM (
            'main',           -- 메인 메뉴
            'side',           -- 사이드 메뉴
            'drink',          -- 음료
            'dessert',        -- 디저트
            'set',            -- 세트 메뉴
            'unknown'
        );
    END IF;

    -- 재료 역할 타입
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ingredient_role') THEN
        CREATE TYPE ingredient_role AS ENUM (
            'main',           -- 주재료
            'aux',            -- 부재료
            'seasoning',      -- 조미료
            'garnish'         -- 고명
        );
    END IF;

    -- 재료 소스 타입
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ingredient_source') THEN
        CREATE TYPE ingredient_source AS ENUM (
            'rule',           -- 룰 기반 추정
            'manual',         -- 수동 입력
            'llm',            -- LLM 추정
            'crawled'         -- 크롤링 수집
        );
    END IF;

    -- 크롤링 작업 상태
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'crawl_job_status') THEN
        CREATE TYPE crawl_job_status AS ENUM (
            'pending',
            'running',
            'completed',
            'failed',
            'cancelled'
        );
    END IF;

    -- 크롤링 작업 타입
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'crawl_job_type') THEN
        CREATE TYPE crawl_job_type AS ENUM (
            'full',           -- 전체 크롤링
            'incremental',    -- 증분 크롤링
            'manual',         -- 수동 크롤링
            'retry'           -- 재시도
        );
    END IF;
END $$;

-- =============================================================================
-- 1. 식당 관련 테이블
-- =============================================================================

-- 식당 기본 정보
CREATE TABLE IF NOT EXISTS restaurants (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 기본 정보
    name                TEXT NOT NULL,
    phone               TEXT,
    business_hours      JSONB,               -- 영업시간 JSON

    -- 주소 정보
    addr_original       TEXT NOT NULL,
    addr_norm           TEXT,                -- 표준화된 주소
    lat                 NUMERIC(10,7),       -- 위도 (소수점 7자리)
    lng                 NUMERIC(10,7),       -- 경도 (소수점 7자리)
    geohash6            TEXT,                -- 6자리 지오해시

    -- 메타데이터
    cuisine_type        TEXT[],              -- 요리 종류 배열
    price_range         TEXT,                -- 가격대 (저렴/보통/비쌈)
    rating_avg          NUMERIC(3,2),        -- 평균 평점
    review_count        INTEGER DEFAULT 0,

    -- 시스템 필드
    canonical_key       TEXT,                -- 중복 제거용 키
    is_active           BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- 식당 소스 매핑 (다중 소스 지원)
CREATE TABLE IF NOT EXISTS restaurant_sources (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id       UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,

    -- 소스 정보
    source_name         source_type NOT NULL,
    source_url          TEXT NOT NULL,
    source_id           TEXT,                -- 소스별 고유 ID

    -- 원본 데이터
    name_raw            TEXT NOT NULL,
    addr_raw            TEXT NOT NULL,
    phone_raw           TEXT,
    data_raw            JSONB,               -- 전체 원본 데이터

    -- 메타데이터
    first_seen_at       TIMESTAMPTZ DEFAULT NOW(),
    last_updated_at     TIMESTAMPTZ DEFAULT NOW(),
    is_primary          BOOLEAN DEFAULT false, -- 주 소스 여부

    CONSTRAINT unique_source_url UNIQUE (source_url),
    CONSTRAINT unique_source_id_per_source UNIQUE (source_name, source_id)
);

-- =============================================================================
-- 2. 메뉴 관련 테이블
-- =============================================================================

-- 메뉴 기본 정보
CREATE TABLE IF NOT EXISTS menus (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id       UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,

    -- 기본 정보
    name                TEXT NOT NULL,
    name_norm           TEXT,                -- 정규화된 이름
    description         TEXT,
    price               INTEGER,             -- KRW 단위

    -- 분류 정보
    category            menu_category DEFAULT 'unknown',
    menu_type           TEXT,                -- 세트/단품/코스 등
    is_signature        BOOLEAN DEFAULT false, -- 대표 메뉴 여부

    -- 영양 정보 (추정치 포함)
    estimated_calories  INTEGER,
    estimated_carbs     NUMERIC(5,2),        -- 탄수화물 (g)
    estimated_protein   NUMERIC(5,2),        -- 단백질 (g)
    estimated_fat       NUMERIC(5,2),        -- 지방 (g)

    -- 알러지 정보
    allergens           TEXT[],              -- 알러지 유발 요소
    spice_level         INTEGER CHECK (spice_level BETWEEN 0 AND 5), -- 매운 정도

    -- 시스템 필드
    is_available        BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- 메뉴-재료 관계 (추정 재료 포함)
CREATE TABLE IF NOT EXISTS menu_ingredients (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    menu_id             UUID NOT NULL REFERENCES menus(id) ON DELETE CASCADE,

    -- 재료 정보
    ingredient_name     TEXT NOT NULL,
    role                ingredient_role DEFAULT 'main',
    quantity            TEXT,                -- 양 (추정치)

    -- 신뢰도 정보
    source              ingredient_source NOT NULL,
    confidence          NUMERIC(4,3) CHECK (confidence BETWEEN 0 AND 1),

    -- 메타데이터
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_menu_ingredient UNIQUE (menu_id, ingredient_name)
);

-- =============================================================================
-- 3. 키토 점수화 시스템
-- =============================================================================

-- 키토 점수 테이블
CREATE TABLE IF NOT EXISTS keto_scores (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    menu_id                 UUID NOT NULL REFERENCES menus(id) ON DELETE CASCADE,

    -- 점수 정보
    score                   INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    confidence_score        NUMERIC(4,3),        -- 점수 신뢰도

    -- 상세 분석
    reasons_json            JSONB NOT NULL,      -- 점수 산출 근거
    detected_keywords       TEXT[],              -- 감지된 키워드들
    penalty_keywords        TEXT[],              -- 감점 키워드들
    bonus_keywords          TEXT[],              -- 가점 키워드들

    -- 대체/예외 처리
    substitution_tags       JSONB,               -- 대체 재료 태그
    negation_detected       BOOLEAN DEFAULT false, -- 부정 표현 감지

    -- 최종 판정
    final_carb_base         carb_base,
    override_reason         TEXT,                -- 수동 조정 사유

    -- 품질 관리
    needs_review            BOOLEAN DEFAULT false,
    reviewed_at             TIMESTAMPTZ,
    reviewed_by             TEXT,

    -- 시스템 정보
    rule_version            TEXT NOT NULL,       -- 룰 엔진 버전
    ingredients_confidence  NUMERIC(5,2),        -- 재료 추정 신뢰도
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_menu_score_version UNIQUE (menu_id, rule_version)
);

-- =============================================================================
-- 4. 캐시 및 시스템 테이블
-- =============================================================================

-- 지오코딩 캐시
CREATE TABLE IF NOT EXISTS geocoding_cache (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 입력/출력
    input_address       TEXT NOT NULL UNIQUE,
    output_address      TEXT,
    lat                 NUMERIC(10,7),
    lng                 NUMERIC(10,7),
    geohash6            TEXT,

    -- 메타데이터
    provider            TEXT NOT NULL,       -- 'kakao'/'naver'/'google'
    confidence          NUMERIC(4,3),
    error_message       TEXT,

    -- 캐시 관리
    hit_count           INTEGER DEFAULT 0,
    last_used_at        TIMESTAMPTZ DEFAULT NOW(),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    expires_at          TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '30 days')
);

-- 크롤링 작업 로그
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 작업 정보
    source_name         source_type NOT NULL,
    job_type            crawl_job_type NOT NULL,
    status              crawl_job_status NOT NULL,

    -- 통계
    total_urls          INTEGER DEFAULT 0,
    processed_urls      INTEGER DEFAULT 0,
    successful_urls     INTEGER DEFAULT 0,
    failed_urls         INTEGER DEFAULT 0,

    -- 결과
    restaurants_found   INTEGER DEFAULT 0,
    menus_found         INTEGER DEFAULT 0,
    new_restaurants     INTEGER DEFAULT 0,
    updated_restaurants INTEGER DEFAULT 0,

    -- 에러 정보
    error_message       TEXT,
    error_details       JSONB,

    -- 타이밍
    started_at          TIMESTAMPTZ DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    duration_seconds    INTEGER
);

-- =============================================================================
-- 5. 인덱스 최적화
-- =============================================================================

-- 식당 검색 최적화
CREATE INDEX IF NOT EXISTS idx_restaurants_name_trgm ON restaurants USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_restaurants_geohash ON restaurants (geohash6) WHERE geohash6 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_restaurants_location ON restaurants (lat, lng) WHERE lat IS NOT NULL AND lng IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_restaurants_canonical ON restaurants (canonical_key) WHERE canonical_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_restaurants_active ON restaurants (is_active, created_at) WHERE is_active = true;

-- 소스 매핑 최적화
CREATE INDEX IF NOT EXISTS idx_restaurant_sources_restaurant_id ON restaurant_sources (restaurant_id);
CREATE INDEX IF NOT EXISTS idx_restaurant_sources_source ON restaurant_sources (source_name, source_id);
CREATE INDEX IF NOT EXISTS idx_restaurant_sources_primary ON restaurant_sources (restaurant_id, is_primary) WHERE is_primary = true;

-- 메뉴 검색 최적화
CREATE INDEX IF NOT EXISTS idx_menus_restaurant_id ON menus (restaurant_id);
CREATE INDEX IF NOT EXISTS idx_menus_name_trgm ON menus USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_menus_name_norm_trgm ON menus USING gin (name_norm gin_trgm_ops) WHERE name_norm IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_menus_category ON menus (category, is_available) WHERE is_available = true;
CREATE INDEX IF NOT EXISTS idx_menus_price ON menus (price) WHERE price IS NOT NULL;

-- 재료 관계 최적화
CREATE INDEX IF NOT EXISTS idx_menu_ingredients_menu_id ON menu_ingredients (menu_id);
CREATE INDEX IF NOT EXISTS idx_menu_ingredients_name ON menu_ingredients (ingredient_name);
CREATE INDEX IF NOT EXISTS idx_menu_ingredients_source_confidence ON menu_ingredients (source, confidence);

-- 키토 점수 최적화
CREATE INDEX IF NOT EXISTS idx_keto_scores_menu_id ON keto_scores (menu_id);
CREATE INDEX IF NOT EXISTS idx_keto_scores_score ON keto_scores (score DESC);
CREATE INDEX IF NOT EXISTS idx_keto_scores_needs_review ON keto_scores (needs_review, score) WHERE needs_review = true;
CREATE INDEX IF NOT EXISTS idx_keto_scores_rule_version ON keto_scores (rule_version, created_at);
CREATE INDEX IF NOT EXISTS idx_keto_scores_carb_base ON keto_scores (final_carb_base) WHERE final_carb_base IS NOT NULL;

-- GIN 인덱스 (JSON 검색 최적화)
CREATE INDEX IF NOT EXISTS idx_keto_scores_reasons ON keto_scores USING gin (reasons_json);
CREATE INDEX IF NOT EXISTS idx_keto_scores_substitutions ON keto_scores USING gin (substitution_tags) WHERE substitution_tags IS NOT NULL;

-- 캐시 최적화
CREATE INDEX IF NOT EXISTS idx_geocoding_cache_address ON geocoding_cache (input_address);
CREATE INDEX IF NOT EXISTS idx_geocoding_cache_expires ON geocoding_cache (expires_at) WHERE expires_at > NOW();

-- 크롤링 로그 최적화
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_source_status ON crawl_jobs (source_name, status, started_at);

-- =============================================================================
-- 6. 트리거 설정
-- =============================================================================

-- updated_at 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- updated_at 트리거 적용
DROP TRIGGER IF EXISTS update_restaurants_updated_at ON restaurants;
CREATE TRIGGER update_restaurants_updated_at
    BEFORE UPDATE ON restaurants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_menus_updated_at ON menus;
CREATE TRIGGER update_menus_updated_at
    BEFORE UPDATE ON menus
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_keto_scores_updated_at ON keto_scores;
CREATE TRIGGER update_keto_scores_updated_at
    BEFORE UPDATE ON keto_scores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 스키마 설정 완료
-- =============================================================================

COMMENT ON DATABASE CURRENT_DATABASE() IS '식당/메뉴 수집 및 키토 점수화 시스템 DB (초기 스키마)';