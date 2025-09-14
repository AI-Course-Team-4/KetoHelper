-- 임베딩 테스트용 테이블 생성

-- 방법1: 레시피명 포함 blob 임베딩 테스트
CREATE TABLE IF NOT EXISTS recipes_keto_method1 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    rating DECIMAL(3,2),
    views INTEGER,
    servings INTEGER,
    cook_time INTEGER,
    difficulty TEXT,
    summary TEXT,
    tags TEXT[],
    ingredients JSONB,
    steps JSONB,
    embedding_blob TEXT,  -- 레시피명 포함
    embedding VECTOR(1536),
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 방법2: 레시피명 제외 blob 임베딩 테스트
CREATE TABLE IF NOT EXISTS recipes_keto_method2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    rating DECIMAL(3,2),
    views INTEGER,
    servings INTEGER,
    cook_time INTEGER,
    difficulty TEXT,
    summary TEXT,
    tags TEXT[],
    ingredients JSONB,
    steps JSONB,
    embedding_blob TEXT,  -- 레시피명 제외
    embedding VECTOR(1536),
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 방법3: LLM 전처리 정규화 임베딩 테스트
CREATE TABLE IF NOT EXISTS recipes_keto_method3 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    rating DECIMAL(3,2),
    views INTEGER,
    servings INTEGER,
    cook_time INTEGER,
    difficulty TEXT,
    summary TEXT,
    tags TEXT[],
    ingredients JSONB,
    steps JSONB,
    embedding_blob TEXT,  -- LLM 전처리된 blob
    embedding VECTOR(1536),
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_recipes_keto_method1_embedding ON recipes_keto_method1 USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_recipes_keto_method1_embedding_blob ON recipes_keto_method1 USING gin (embedding_blob gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_recipes_keto_method1_tags ON recipes_keto_method1 USING gin (tags);
CREATE INDEX IF NOT EXISTS idx_recipes_keto_method1_ingredients ON recipes_keto_method1 USING gin (ingredients);

CREATE INDEX IF NOT EXISTS idx_recipes_keto_method2_embedding ON recipes_keto_method2 USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_recipes_keto_method2_embedding_blob ON recipes_keto_method2 USING gin (embedding_blob gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_recipes_keto_method2_tags ON recipes_keto_method2 USING gin (tags);
CREATE INDEX IF NOT EXISTS idx_recipes_keto_method2_ingredients ON recipes_keto_method2 USING gin (ingredients);

CREATE INDEX IF NOT EXISTS idx_recipes_keto_method3_embedding ON recipes_keto_method3 USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_recipes_keto_method3_embedding_blob ON recipes_keto_method3 USING gin (embedding_blob gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_recipes_keto_method3_tags ON recipes_keto_method3 USING gin (tags);
CREATE INDEX IF NOT EXISTS idx_recipes_keto_method3_ingredients ON recipes_keto_method3 USING gin (ingredients);

-- 테스트 결과 저장용 테이블
CREATE TABLE IF NOT EXISTS embedding_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    method_name TEXT NOT NULL,
    test_query TEXT NOT NULL,
    expected_recipe_id UUID,
    predicted_recipe_id UUID,
    predicted_score DECIMAL(5,4),
    rank_position INTEGER,
    is_correct BOOLEAN,
    test_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 골든셋 저장용 테이블
CREATE TABLE IF NOT EXISTS golden_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    method_name TEXT NOT NULL,
    query TEXT NOT NULL,
    correct_recipe_id UUID NOT NULL,
    correct_recipe_title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 테스트 질의셋 저장용 테이블
CREATE TABLE IF NOT EXISTS test_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    category TEXT,
    difficulty TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
