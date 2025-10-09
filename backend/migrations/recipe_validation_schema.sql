-- =========================================
-- 골든셋 기반 레시피 검증 시스템 스키마
-- Phase 1: 개별 메뉴 검증 (Option A)
-- =========================================

-- 1) 검증된 골든셋 레시피
CREATE TABLE IF NOT EXISTS golden_recipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  servings INTEGER NOT NULL DEFAULT 1,
  ingredients_json JSONB NOT NULL,   -- [{name_norm, amount_g}]
  steps_json JSONB NOT NULL,         -- ["...", "..."]
  tags TEXT[] DEFAULT '{}',          -- 카테고리 태그 (예: keto, high_protein, salad)
  macros_json JSONB,                 -- {carb_g, protein_g, fat_g, kcal}
  version INTEGER NOT NULL DEFAULT 1,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 골든셋 버전 관리 인덱스
CREATE INDEX IF NOT EXISTS idx_golden_active ON golden_recipes(id, version DESC) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_golden_tags ON golden_recipes USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_golden_title ON golden_recipes(title);

-- 2) 변형(치환/범위/금지) 규칙
CREATE TABLE IF NOT EXISTS transform_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  base_recipe_id UUID REFERENCES golden_recipes(id) ON DELETE CASCADE,
  swaps_json JSONB NOT NULL,         -- [{from, to, ratio}]
  amount_limits_json JSONB NOT NULL, -- [{name_norm, min_g, max_g}]
  forbidden_json JSONB NOT NULL,     -- ["sugar","honey","rice"...]
  version INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 규칙 조회 인덱스
CREATE INDEX IF NOT EXISTS idx_transform_base_recipe ON transform_rules(base_recipe_id);

-- 3) 생성 결과 + 심사 리포트(프로비넌스)
CREATE TABLE IF NOT EXISTS generated_recipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,                      -- 사용자 ID (옵션)
  base_recipe_id UUID REFERENCES golden_recipes(id) ON DELETE SET NULL,
  deltas_json JSONB NOT NULL,        -- [{op: "swap"|"scale", ...}]
  final_ingredients_json JSONB NOT NULL,
  final_steps_json JSONB NOT NULL,
  judge_report_json JSONB NOT NULL,  -- {passed, reasons[], suggested_fixes[]}
  passed BOOLEAN NOT NULL,
  attempts INTEGER DEFAULT 1,        -- 재시도 횟수
  response_time_ms INTEGER,          -- 응답 시간 (밀리초)
  model_gen TEXT,                    -- Generator 모델명
  model_judge TEXT,                  -- Judge 모델명
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 성능 분석용 인덱스
CREATE INDEX IF NOT EXISTS idx_generated_created_at ON generated_recipes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generated_passed ON generated_recipes(passed);
CREATE INDEX IF NOT EXISTS idx_generated_user_id ON generated_recipes(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_generated_base_recipe ON generated_recipes(base_recipe_id);

-- 4) 재료 정규화 테이블 (CSV 대신 DB 사용)
CREATE TABLE IF NOT EXISTS ingredient_normalization (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  korean TEXT NOT NULL,
  english TEXT NOT NULL,
  name_norm TEXT NOT NULL UNIQUE,    -- 정규화된 이름 (예: chicken_breast)
  category TEXT NOT NULL,             -- 카테고리 (예: protein, fat, vegetable)
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 정규화 조회 인덱스
CREATE INDEX IF NOT EXISTS idx_ingredient_korean ON ingredient_normalization(korean);
CREATE INDEX IF NOT EXISTS idx_ingredient_english ON ingredient_normalization(english);
CREATE INDEX IF NOT EXISTS idx_ingredient_category ON ingredient_normalization(category);

-- =========================================
-- 초기 샘플 데이터 (테스트용)
-- =========================================

-- 샘플 골든셋 레시피 1: 버터치킨 샐러드
INSERT INTO golden_recipes (title, servings, ingredients_json, steps_json, tags, macros_json, is_active)
VALUES (
  '버터치킨 샐러드',
  1,
  '[
    {"name_norm": "chicken_breast", "amount_g": 120},
    {"name_norm": "romaine_lettuce", "amount_g": 80},
    {"name_norm": "olive_oil", "amount_g": 15},
    {"name_norm": "butter", "amount_g": 10}
  ]'::jsonb,
  '["닭 가슴살을 소금, 후추로 간하고 버터에 굽는다", "로메인을 한입 크기로 자른다", "올리브오일 드레싱을 만든다", "구운 닭고기를 샐러드 위에 올린다"]'::jsonb,
  ARRAY['keto', 'high_protein', 'salad'],
  '{"carb_g": 6, "protein_g": 35, "fat_g": 28, "kcal": 430}'::jsonb,
  true
) ON CONFLICT DO NOTHING;

-- 샘플 변형 규칙
INSERT INTO transform_rules (base_recipe_id, swaps_json, amount_limits_json, forbidden_json)
SELECT 
  id,
  '[
    {"from": "wheat_noodles", "to": "tofu_noodles", "ratio": 1.0},
    {"from": "rice", "to": "konjac_rice", "ratio": 1.0}
  ]'::jsonb,
  '[
    {"name_norm": "olive_oil", "min_g": 5, "max_g": 25},
    {"name_norm": "butter", "min_g": 5, "max_g": 15}
  ]'::jsonb,
  '["sugar", "honey", "rice", "wheat_flour", "noodle_wheat"]'::jsonb
FROM golden_recipes
WHERE title = '버터치킨 샐러드'
LIMIT 1
ON CONFLICT DO NOTHING;

-- 샘플 재료 정규화 데이터
INSERT INTO ingredient_normalization (korean, english, name_norm, category) VALUES
  ('닭가슴살', 'chicken breast', 'chicken_breast', 'protein'),
  ('올리브오일', 'olive oil', 'olive_oil', 'fat'),
  ('두부면', 'tofu noodles', 'tofu_noodles', 'carb_substitute'),
  ('곤약밥', 'konjac rice', 'konjac_rice', 'carb_substitute'),
  ('로메인', 'romaine lettuce', 'romaine_lettuce', 'vegetable'),
  ('버터', 'butter', 'butter', 'fat'),
  ('계란', 'egg', 'egg', 'protein'),
  ('아보카도', 'avocado', 'avocado', 'fat'),
  ('시금치', 'spinach', 'spinach', 'vegetable'),
  ('베이컨', 'bacon', 'bacon', 'protein')
ON CONFLICT (name_norm) DO NOTHING;

-- =========================================
-- 유틸리티 함수
-- =========================================

-- 재료 정규화 함수
CREATE OR REPLACE FUNCTION normalize_ingredient(ingredient_name TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN (
    SELECT name_norm
    FROM ingredient_normalization
    WHERE korean = ingredient_name OR english = ingredient_name
    LIMIT 1
  );
END;
$$ LANGUAGE plpgsql;

-- 골든셋 검색 함수 (태그 기반)
CREATE OR REPLACE FUNCTION search_golden_recipes(search_tags TEXT[])
RETURNS TABLE (
  id UUID,
  title TEXT,
  tags TEXT[],
  macros_json JSONB,
  similarity_score FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    gr.id,
    gr.title,
    gr.tags,
    gr.macros_json,
    -- 태그 일치도 계산 (공통 태그 수 / 전체 태그 수)
    CASE 
      WHEN cardinality(search_tags) = 0 THEN 0.0
      ELSE cardinality(ARRAY(SELECT unnest(gr.tags) INTERSECT SELECT unnest(search_tags)))::FLOAT / cardinality(search_tags)::FLOAT
    END as similarity_score
  FROM golden_recipes gr
  WHERE gr.is_active = true
  ORDER BY similarity_score DESC, gr.created_at DESC
  LIMIT 10;
END;
$$ LANGUAGE plpgsql;

-- =========================================
-- 마이그레이션 완료 로그
-- =========================================

DO $$
BEGIN
  RAISE NOTICE '✅ Recipe Validation Schema Migration Completed';
  RAISE NOTICE '📊 Tables created: golden_recipes, transform_rules, generated_recipes, ingredient_normalization';
  RAISE NOTICE '🔧 Functions created: normalize_ingredient, search_golden_recipes';
END $$;

