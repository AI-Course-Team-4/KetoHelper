-- 키토 코치 데이터베이스 스키마 (Supabase PostgreSQL + pgvector)
-- 실행 순서: Supabase SQL Editor에서 이 파일을 순서대로 실행

-- 1) pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- 2) 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nickname TEXT,
  goals_kcal INTEGER,
  goals_carbs_g INTEGER,
  allergies TEXT[] DEFAULT '{}',
  dislikes TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3) 레시피 테이블
CREATE TABLE IF NOT EXISTS recipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  tags TEXT[] DEFAULT '{}',
  ketoized BOOLEAN DEFAULT FALSE,
  macros JSONB,                 -- {kcal,carb,protein,fat}
  source TEXT,
  ingredients JSONB,            -- [{name,amount,unit}]
  steps TEXT[],
  tips TEXT[],
  allergen_flags TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4) 레시피 임베딩 테이블 (pgvector)
CREATE TABLE IF NOT EXISTS recipe_embeddings (
  recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
  chunk_idx INTEGER NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1536) NOT NULL,  -- OpenAI text-embedding-3-small 차원
  PRIMARY KEY (recipe_id, chunk_idx)
);

-- 5) 레시피 임베딩 코사인 유사도 검색 인덱스 (IVFFLAT)
CREATE INDEX IF NOT EXISTS recipe_embeddings_cosine_idx
  ON recipe_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 6) 장소 캐시 테이블 (카카오 검색 결과 보관)
CREATE TABLE IF NOT EXISTS places_cache (
  place_id TEXT PRIMARY KEY,
  name TEXT,
  address TEXT,
  category TEXT,
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  keto_score INTEGER,
  last_seen_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7) 대화 로그 테이블
CREATE TABLE IF NOT EXISTS messages (
  id BIGSERIAL PRIMARY KEY,
  session_id UUID,
  user_id UUID,
  role TEXT CHECK (role IN ('user','assistant')),
  content TEXT,
  tool_calls JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8) 캘린더/플랜 테이블
CREATE TABLE IF NOT EXISTS plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  slot TEXT NOT NULL CHECK (slot IN ('breakfast','lunch','dinner','snack')),
  type TEXT NOT NULL CHECK (type IN ('recipe','place')),
  ref_id TEXT NOT NULL,
  title TEXT NOT NULL,
  location JSONB,   -- {name,address}
  macros JSONB,     -- {kcal,carb,protein,fat}
  notes TEXT,
  status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN ('planned','done','skipped')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9) 플랜 유니크 제약 조건 (사용자별 날짜/슬롯 유니크)
CREATE UNIQUE INDEX IF NOT EXISTS uniq_plan_user_date_slot 
  ON plans(user_id, date, slot);

-- 10) 체중 기록 테이블 (선택)
CREATE TABLE IF NOT EXISTS weights (
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  weight_kg NUMERIC(5,2),
  PRIMARY KEY (user_id, date)
);

-- 11) 성능 향상을 위한 추가 인덱스들
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_plans_user_date ON plans(user_id, date);
CREATE INDEX IF NOT EXISTS idx_plans_date_slot ON plans(date, slot);
CREATE INDEX IF NOT EXISTS idx_places_cache_location ON places_cache(lat, lng);

-- 12) 샘플 사용자 데이터 (테스트용)
INSERT INTO users (id, nickname, goals_kcal, goals_carbs_g, allergies, dislikes) 
VALUES (
  '00000000-0000-0000-0000-000000000001',
  '키토 테스터',
  1500,
  25,
  ARRAY['갑각류', '견과류'],
  ARRAY['매운음식', '달콤한음식']
) ON CONFLICT (id) DO NOTHING;

-- 13) 샘플 레시피 데이터
INSERT INTO recipes (
  id, title, tags, ketoized, macros, ingredients, steps, tips, allergen_flags
) VALUES (
  '00000000-0000-0000-0000-000000000001',
  '키토 불고기',
  ARRAY['한식', '고기', '키토'],
  TRUE,
  '{"kcal": 450, "carb": 8, "protein": 35, "fat": 30}',
  '[
    {"name": "소고기 불고기용", "amount": 200, "unit": "g"},
    {"name": "양파", "amount": 50, "unit": "g"},
    {"name": "마늘", "amount": 10, "unit": "g"},
    {"name": "간장", "amount": 2, "unit": "tbsp"},
    {"name": "에리스리톨", "amount": 1, "unit": "tsp"},
    {"name": "참기름", "amount": 1, "unit": "tbsp"}
  ]',
  ARRAY[
    '소고기를 얇게 썰어 준비한다',
    '양파와 마늘을 슬라이스한다', 
    '간장, 에리스리톨, 참기름으로 양념을 만든다',
    '고기에 양념을 발라 30분간 재운다',
    '팬에 고기와 야채를 볶아낸다',
    '상추에 싸서 드신다'
  ],
  ARRAY[
    '설탕 대신 에리스리톨 사용으로 탄수화물 절약',
    '상추쌈으로 밥 대신 섭취',
    '추가 지방으로 아보카도나 치즈 토핑 가능'
  ],
  ARRAY['soy']
) ON CONFLICT (id) DO NOTHING;

-- 14) 성공 메시지
SELECT 'Keto Coach 데이터베이스 스키마 설정 완료!' as result;
