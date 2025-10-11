-- =========================================
-- 골든셋 레시피 30개 (5 카테고리 × 6개)
-- 카테고리: 닭고기, 돼지고기, 계란, 샐러드, 볶음
-- =========================================

-- 정규화 재료 추가 (먼저 실행 필요)
INSERT INTO ingredient_normalization (korean, english, name_norm, category) VALUES
  -- 단백질
  ('닭가슴살', 'chicken breast', 'chicken_breast', 'protein'),
  ('닭다리살', 'chicken thigh', 'chicken_thigh', 'protein'),
  ('삼겹살', 'pork belly', 'pork_belly', 'protein'),
  ('목살', 'pork neck', 'pork_neck', 'protein'),
  ('계란', 'egg', 'egg', 'protein'),
  ('베이컨', 'bacon', 'bacon', 'protein'),
  ('소고기', 'beef', 'beef', 'protein'),
  ('새우', 'shrimp', 'shrimp', 'protein'),
  ('연어', 'salmon', 'salmon', 'protein'),
  ('참치', 'tuna', 'tuna', 'protein'),
  
  -- 채소
  ('로메인', 'romaine lettuce', 'romaine_lettuce', 'vegetable'),
  ('시금치', 'spinach', 'spinach', 'vegetable'),
  ('케일', 'kale', 'kale', 'vegetable'),
  ('양배추', 'cabbage', 'cabbage', 'vegetable'),
  ('브로콜리', 'broccoli', 'broccoli', 'vegetable'),
  ('콜리플라워', 'cauliflower', 'cauliflower', 'vegetable'),
  ('애호박', 'zucchini', 'zucchini', 'vegetable'),
  ('파프리카', 'bell pepper', 'bell_pepper', 'vegetable'),
  ('양파', 'onion', 'onion', 'vegetable'),
  ('마늘', 'garlic', 'garlic', 'vegetable'),
  ('버섯', 'mushroom', 'mushroom', 'vegetable'),
  
  -- 지방
  ('올리브오일', 'olive oil', 'olive_oil', 'fat'),
  ('버터', 'butter', 'butter', 'fat'),
  ('아보카도', 'avocado', 'avocado', 'fat'),
  ('코코넛오일', 'coconut oil', 'coconut_oil', 'fat'),
  ('치즈', 'cheese', 'cheese', 'fat'),
  ('크림치즈', 'cream cheese', 'cream_cheese', 'fat'),
  ('모짜렐라', 'mozzarella', 'mozzarella', 'fat'),
  ('아몬드', 'almond', 'almond', 'fat'),
  ('호두', 'walnut', 'walnut', 'fat'),
  
  -- 저탄수 대체재
  ('두부면', 'tofu noodles', 'tofu_noodles', 'carb_substitute'),
  ('곤약면', 'konjac noodles', 'konjac_noodles', 'carb_substitute'),
  ('곤약밥', 'konjac rice', 'konjac_rice', 'carb_substitute'),
  ('코코넛가루', 'coconut flour', 'coconut_flour', 'carb_substitute'),
  ('아몬드가루', 'almond flour', 'almond_flour', 'carb_substitute'),
  
  -- 양념
  ('소금', 'salt', 'salt', 'seasoning'),
  ('후추', 'pepper', 'pepper', 'seasoning'),
  ('간장', 'soy sauce', 'soy_sauce', 'seasoning'),
  ('고춧가루', 'red pepper powder', 'red_pepper_powder', 'seasoning'),
  ('참기름', 'sesame oil', 'sesame_oil', 'seasoning')
ON CONFLICT (name_norm) DO NOTHING;

-- =========================================
-- 카테고리 1: 닭고기 (6개)
-- =========================================

INSERT INTO golden_recipes (title, servings, ingredients_json, steps_json, tags, macros_json) VALUES
-- 1. 버터치킨 샐러드
('버터치킨 샐러드', 1,
 '[
   {"name_norm": "chicken_breast", "amount_g": 120},
   {"name_norm": "romaine_lettuce", "amount_g": 80},
   {"name_norm": "olive_oil", "amount_g": 15},
   {"name_norm": "butter", "amount_g": 10},
   {"name_norm": "salt", "amount_g": 2},
   {"name_norm": "pepper", "amount_g": 1}
 ]'::jsonb,
 '["닭 가슴살을 소금, 후추로 간한다", "버터를 두른 팬에 닭고기를 굽는다", "로메인을 한입 크기로 자른다", "올리브오일 드레싱을 뿌린다", "구운 닭고기를 샐러드 위에 올린다"]'::jsonb,
 ARRAY['keto', 'high_protein', 'salad', 'chicken'],
 '{"carb_g": 6, "protein_g": 35, "fat_g": 28, "kcal": 430}'::jsonb),

-- 2. 닭다리 구이
('닭다리 구이', 1,
 '[
   {"name_norm": "chicken_thigh", "amount_g": 150},
   {"name_norm": "olive_oil", "amount_g": 10},
   {"name_norm": "garlic", "amount_g": 5},
   {"name_norm": "salt", "amount_g": 2},
   {"name_norm": "pepper", "amount_g": 1}
 ]'::jsonb,
 '["닭다리에 소금, 후추, 다진 마늘로 밑간한다", "올리브오일을 두른 팬에 굽는다", "겉은 바삭하고 속은 촉촉하게 익힌다"]'::jsonb,
 ARRAY['keto', 'high_protein', 'grilled', 'chicken'],
 '{"carb_g": 3, "protein_g": 32, "fat_g": 22, "kcal": 350}'::jsonb),

-- 3. 닭가슴살 스테이크
('닭가슴살 스테이크', 1,
 '[
   {"name_norm": "chicken_breast", "amount_g": 130},
   {"name_norm": "butter", "amount_g": 15},
   {"name_norm": "mushroom", "amount_g": 50},
   {"name_norm": "spinach", "amount_g": 40},
   {"name_norm": "salt", "amount_g": 2},
   {"name_norm": "pepper", "amount_g": 1}
 ]'::jsonb,
 '["닭가슴살을 두들겨 펴준다", "소금, 후추로 간한다", "버터를 두른 팬에 스테이크처럼 굽는다", "버섯과 시금치를 곁들인다"]'::jsonb,
 ARRAY['keto', 'high_protein', 'steak', 'chicken'],
 '{"carb_g": 5, "protein_g": 38, "fat_g": 20, "kcal": 380}'::jsonb),

-- 4. 닭고기 아보카도 볼
('닭고기 아보카도 볼', 1,
 '[
   {"name_norm": "chicken_breast", "amount_g": 100},
   {"name_norm": "avocado", "amount_g": 80},
   {"name_norm": "romaine_lettuce", "amount_g": 60},
   {"name_norm": "olive_oil", "amount_g": 10},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["닭가슴살을 구워 잘게 찢는다", "아보카도를 슬라이스한다", "로메인과 함께 볼에 담는다", "올리브오일과 소금으로 간한다"]'::jsonb,
 ARRAY['keto', 'salad', 'chicken', 'avocado'],
 '{"carb_g": 8, "protein_g": 30, "fat_g": 32, "kcal": 450}'::jsonb),

-- 5. 닭고기 케일 샐러드
('닭고기 케일 샐러드', 1,
 '[
   {"name_norm": "chicken_breast", "amount_g": 110},
   {"name_norm": "kale", "amount_g": 70},
   {"name_norm": "olive_oil", "amount_g": 12},
   {"name_norm": "almond", "amount_g": 15},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["닭가슴살을 구워 슬라이스한다", "케일을 한입 크기로 자른다", "아몬드를 곁들인다", "올리브오일로 버무린다"]'::jsonb,
 ARRAY['keto', 'salad', 'chicken', 'kale'],
 '{"carb_g": 7, "protein_g": 33, "fat_g": 26, "kcal": 410}'::jsonb),

-- 6. 닭가슴살 브로콜리 볶음
('닭가슴살 브로콜리 볶음', 1,
 '[
   {"name_norm": "chicken_breast", "amount_g": 120},
   {"name_norm": "broccoli", "amount_g": 100},
   {"name_norm": "olive_oil", "amount_g": 12},
   {"name_norm": "garlic", "amount_g": 5},
   {"name_norm": "soy_sauce", "amount_g": 8},
   {"name_norm": "salt", "amount_g": 1}
 ]'::jsonb,
 '["닭가슴살을 한입 크기로 자른다", "브로콜리를 데친다", "올리브오일에 마늘을 볶는다", "닭고기와 브로콜리를 넣고 간장으로 볶는다"]'::jsonb,
 ARRAY['keto', 'stir_fry', 'chicken', 'broccoli'],
 '{"carb_g": 9, "protein_g": 36, "fat_g": 18, "kcal": 380}'::jsonb);

-- =========================================
-- 카테고리 2: 돼지고기 (6개)
-- =========================================

INSERT INTO golden_recipes (title, servings, ingredients_json, steps_json, tags, macros_json) VALUES
-- 7. 삼겹살 구이
('삼겹살 구이', 1,
 '[
   {"name_norm": "pork_belly", "amount_g": 150},
   {"name_norm": "romaine_lettuce", "amount_g": 50},
   {"name_norm": "sesame_oil", "amount_g": 5},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["삼겹살을 팬에 굽는다", "기름기가 빠지도록 충분히 굽는다", "로메인에 싸서 먹는다", "참기름과 소금으로 간한다"]'::jsonb,
 ARRAY['keto', 'high_fat', 'grilled', 'pork'],
 '{"carb_g": 2, "protein_g": 25, "fat_g": 45, "kcal": 520}'::jsonb),

-- 8. 목살 스테이크
('목살 스테이크', 1,
 '[
   {"name_norm": "pork_neck", "amount_g": 140},
   {"name_norm": "butter", "amount_g": 12},
   {"name_norm": "mushroom", "amount_g": 60},
   {"name_norm": "salt", "amount_g": 2},
   {"name_norm": "pepper", "amount_g": 1}
 ]'::jsonb,
 '["목살을 두툼하게 자른다", "소금, 후추로 간한다", "버터를 두른 팬에 스테이크처럼 굽는다", "버섯을 곁들인다"]'::jsonb,
 ARRAY['keto', 'high_protein', 'steak', 'pork'],
 '{"carb_g": 4, "protein_g": 30, "fat_g": 35, "kcal": 450}'::jsonb),

-- 9. 베이컨 샐러드
('베이컨 샐러드', 1,
 '[
   {"name_norm": "bacon", "amount_g": 80},
   {"name_norm": "romaine_lettuce", "amount_g": 100},
   {"name_norm": "avocado", "amount_g": 60},
   {"name_norm": "olive_oil", "amount_g": 10},
   {"name_norm": "salt", "amount_g": 1}
 ]'::jsonb,
 '["베이컨을 바삭하게 굽는다", "로메인과 아보카도를 자른다", "베이컨을 부숴서 올린다", "올리브오일과 소금으로 간한다"]'::jsonb,
 ARRAY['keto', 'salad', 'bacon', 'high_fat'],
 '{"carb_g": 6, "protein_g": 22, "fat_g": 38, "kcal": 450}'::jsonb),

-- 10. 돼지고기 애호박 볶음
('돼지고기 애호박 볶음', 1,
 '[
   {"name_norm": "pork_belly", "amount_g": 120},
   {"name_norm": "zucchini", "amount_g": 100},
   {"name_norm": "olive_oil", "amount_g": 10},
   {"name_norm": "garlic", "amount_g": 5},
   {"name_norm": "soy_sauce", "amount_g": 8},
   {"name_norm": "salt", "amount_g": 1}
 ]'::jsonb,
 '["돼지고기를 한입 크기로 자른다", "애호박을 슬라이스한다", "올리브오일에 마늘을 볶는다", "돼지고기와 애호박을 넣고 간장으로 볶는다"]'::jsonb,
 ARRAY['keto', 'stir_fry', 'pork', 'zucchini'],
 '{"carb_g": 7, "protein_g": 28, "fat_g": 40, "kcal": 490}'::jsonb),

-- 11. 삼겹살 김치찌개 (저탄수 버전)
('삼겹살 김치찌개', 1,
 '[
   {"name_norm": "pork_belly", "amount_g": 100},
   {"name_norm": "cabbage", "amount_g": 80},
   {"name_norm": "tofu_noodles", "amount_g": 50},
   {"name_norm": "sesame_oil", "amount_g": 5},
   {"name_norm": "red_pepper_powder", "amount_g": 3}
 ]'::jsonb,
 '["삼겹살을 볶는다", "배추를 넣고 볶는다", "물을 붓고 끓인다", "두부면을 넣는다", "참기름과 고춧가루로 마무리한다"]'::jsonb,
 ARRAY['keto', 'soup', 'pork', 'low_carb'],
 '{"carb_g": 8, "protein_g": 24, "fat_g": 42, "kcal": 480}'::jsonb),

-- 12. 베이컨 아보카도
('베이콘 아보카도', 1,
 '[
   {"name_norm": "bacon", "amount_g": 60},
   {"name_norm": "avocado", "amount_g": 100},
   {"name_norm": "egg", "amount_g": 50},
   {"name_norm": "salt", "amount_g": 1},
   {"name_norm": "pepper", "amount_g": 1}
 ]'::jsonb,
 '["베이콘을 바삭하게 굽는다", "아보카도를 반으로 갈라 씨를 제거한다", "계란을 스크램블로 만든다", "아보카도에 계란과 베이콘을 올린다"]'::jsonb,
 ARRAY['keto', 'breakfast', 'bacon', 'avocado'],
 '{"carb_g": 7, "protein_g": 20, "fat_g": 42, "kcal": 480}'::jsonb);

-- =========================================
-- 카테고리 3: 계란 (6개)
-- =========================================

INSERT INTO golden_recipes (title, servings, ingredients_json, steps_json, tags, macros_json) VALUES
-- 13. 스크램블 에그
('스크램블 에그', 1,
 '[
   {"name_norm": "egg", "amount_g": 100},
   {"name_norm": "butter", "amount_g": 12},
   {"name_norm": "cheese", "amount_g": 20},
   {"name_norm": "salt", "amount_g": 2},
   {"name_norm": "pepper", "amount_g": 1}
 ]'::jsonb,
 '["계란을 잘 풀어준다", "버터를 두른 팬에 넣는다", "약불에서 저어가며 익힌다", "치즈를 올려 녹인다", "소금, 후추로 간한다"]'::jsonb,
 ARRAY['keto', 'breakfast', 'egg', 'quick'],
 '{"carb_g": 2, "protein_g": 18, "fat_g": 28, "kcal": 340}'::jsonb),

-- 14. 시금치 오믈렛
('시금치 오믈렛', 1,
 '[
   {"name_norm": "egg", "amount_g": 100},
   {"name_norm": "spinach", "amount_g": 50},
   {"name_norm": "butter", "amount_g": 10},
   {"name_norm": "mozzarella", "amount_g": 25},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["계란을 잘 풀어준다", "시금치를 볶는다", "버터를 두른 팬에 계란을 부어 익힌다", "시금치와 모짜렐라를 넣고 반으로 접는다"]'::jsonb,
 ARRAY['keto', 'breakfast', 'egg', 'omelette'],
 '{"carb_g": 3, "protein_g": 22, "fat_g": 26, "kcal": 350}'::jsonb),

-- 15. 계란찜
('계란찜', 1,
 '[
   {"name_norm": "egg", "amount_g": 100},
   {"name_norm": "butter", "amount_g": 8},
   {"name_norm": "cheese", "amount_g": 15},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["계란을 잘 풀어준다", "버터와 소금을 넣는다", "약불에서 저어가며 찐다", "치즈를 올린다"]'::jsonb,
 ARRAY['keto', 'breakfast', 'egg', 'steamed'],
 '{"carb_g": 2, "protein_g": 20, "fat_g": 24, "kcal": 320}'::jsonb),

-- 16. 아보카도 계란
('아보카도 계란', 1,
 '[
   {"name_norm": "egg", "amount_g": 50},
   {"name_norm": "avocado", "amount_g": 100},
   {"name_norm": "olive_oil", "amount_g": 5},
   {"name_norm": "salt", "amount_g": 1},
   {"name_norm": "pepper", "amount_g": 1}
 ]'::jsonb,
 '["아보카도를 반으로 갈라 씨를 제거한다", "계란을 삶는다", "아보카도에 계란을 올린다", "올리브오일, 소금, 후추로 간한다"]'::jsonb,
 ARRAY['keto', 'breakfast', 'egg', 'avocado'],
 '{"carb_g": 6, "protein_g": 12, "fat_g": 32, "kcal": 360}'::jsonb),

-- 17. 베이컨 계란 볶음
('베이컨 계란 볶음', 1,
 '[
   {"name_norm": "bacon", "amount_g": 60},
   {"name_norm": "egg", "amount_g": 100},
   {"name_norm": "butter", "amount_g": 8},
   {"name_norm": "salt", "amount_g": 1},
   {"name_norm": "pepper", "amount_g": 1}
 ]'::jsonb,
 '["베이콘을 잘게 자른다", "베이콘을 먼저 볶는다", "계란을 풀어 넣는다", "버터를 추가하고 볶는다", "소금, 후추로 간한다"]'::jsonb,
 ARRAY['keto', 'breakfast', 'egg', 'bacon'],
 '{"carb_g": 2, "protein_g": 26, "fat_g": 36, "kcal": 440}'::jsonb),

-- 18. 계란 버섯 볶음
('계란 버섯 볶음', 1,
 '[
   {"name_norm": "egg", "amount_g": 100},
   {"name_norm": "mushroom", "amount_g": 80},
   {"name_norm": "butter", "amount_g": 12},
   {"name_norm": "garlic", "amount_g": 5},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["버섯을 슬라이스한다", "버터에 마늘과 버섯을 볶는다", "계란을 풀어 넣는다", "볶아서 익힌다"]'::jsonb,
 ARRAY['keto', 'breakfast', 'egg', 'mushroom'],
 '{"carb_g": 4, "protein_g": 20, "fat_g": 26, "kcal": 340}'::jsonb);

-- =========================================
-- 카테고리 4: 샐러드 (6개)
-- =========================================

INSERT INTO golden_recipes (title, servings, ingredients_json, steps_json, tags, macros_json) VALUES
-- 19. 그린 샐러드
('그린 샐러드', 1,
 '[
   {"name_norm": "romaine_lettuce", "amount_g": 100},
   {"name_norm": "spinach", "amount_g": 50},
   {"name_norm": "olive_oil", "amount_g": 15},
   {"name_norm": "avocado", "amount_g": 50},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["로메인과 시금치를 씻는다", "한입 크기로 자른다", "아보카도를 슬라이스한다", "올리브오일과 소금으로 간한다"]'::jsonb,
 ARRAY['keto', 'salad', 'vegetarian', 'green'],
 '{"carb_g": 8, "protein_g": 4, "fat_g": 24, "kcal": 260}'::jsonb),

-- 20. 케일 아몬드 샐러드
('케일 아몬드 샐러드', 1,
 '[
   {"name_norm": "kale", "amount_g": 80},
   {"name_norm": "almond", "amount_g": 20},
   {"name_norm": "olive_oil", "amount_g": 12},
   {"name_norm": "cheese", "amount_g": 20},
   {"name_norm": "salt", "amount_g": 1}
 ]'::jsonb,
 '["케일을 한입 크기로 자른다", "아몬드를 곁들인다", "치즈를 올린다", "올리브오일과 소금으로 간한다"]'::jsonb,
 ARRAY['keto', 'salad', 'kale', 'almond'],
 '{"carb_g": 7, "protein_g": 10, "fat_g": 28, "kcal": 320}'::jsonb),

-- 21. 새우 샐러드
('새우 샐러드', 1,
 '[
   {"name_norm": "shrimp", "amount_g": 100},
   {"name_norm": "romaine_lettuce", "amount_g": 80},
   {"name_norm": "avocado", "amount_g": 50},
   {"name_norm": "olive_oil", "amount_g": 10},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["새우를 삶는다", "로메인을 자른다", "아보카도를 슬라이스한다", "모두 섞어 올리브오일과 소금으로 간한다"]'::jsonb,
 ARRAY['keto', 'salad', 'shrimp', 'seafood'],
 '{"carb_g": 7, "protein_g": 26, "fat_g": 22, "kcal": 340}'::jsonb),

-- 22. 연어 샐러드
('연어 샐러드', 1,
 '[
   {"name_norm": "salmon", "amount_g": 120},
   {"name_norm": "spinach", "amount_g": 70},
   {"name_norm": "olive_oil", "amount_g": 12},
   {"name_norm": "avocado", "amount_g": 40},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["연어를 구워 플레이크로 만든다", "시금치를 준비한다", "아보카도를 슬라이스한다", "올리브오일과 소금으로 버무린다"]'::jsonb,
 ARRAY['keto', 'salad', 'salmon', 'omega3'],
 '{"carb_g": 6, "protein_g": 32, "fat_g": 28, "kcal": 420}'::jsonb),

-- 23. 참치 샐러드
('참치 샐러드', 1,
 '[
   {"name_norm": "tuna", "amount_g": 100},
   {"name_norm": "romaine_lettuce", "amount_g": 90},
   {"name_norm": "olive_oil", "amount_g": 15},
   {"name_norm": "cheese", "amount_g": 20},
   {"name_norm": "salt", "amount_g": 1}
 ]'::jsonb,
 '["참치를 준비한다", "로메인을 자른다", "치즈를 올린다", "올리브오일과 소금으로 간한다"]'::jsonb,
 ARRAY['keto', 'salad', 'tuna', 'quick'],
 '{"carb_g": 5, "protein_g": 30, "fat_g": 24, "kcal": 370}'::jsonb),

-- 24. 콜리플라워 샐러드
('콜리플라워 샐러드', 1,
 '[
   {"name_norm": "cauliflower", "amount_g": 100},
   {"name_norm": "bacon", "amount_g": 40},
   {"name_norm": "olive_oil", "amount_g": 12},
   {"name_norm": "cheese", "amount_g": 20},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["콜리플라워를 데친다", "베이콘을 바삭하게 굽는다", "치즈를 올린다", "올리브오일과 소금으로 버무린다"]'::jsonb,
 ARRAY['keto', 'salad', 'cauliflower', 'bacon'],
 '{"carb_g": 6, "protein_g": 16, "fat_g": 28, "kcal": 340}'::jsonb);

-- =========================================
-- 카테고리 5: 볶음 (6개)
-- =========================================

INSERT INTO golden_recipes (title, servings, ingredients_json, steps_json, tags, macros_json) VALUES
-- 25. 소고기 브로콜리 볶음
('소고기 브로콜리 볶음', 1,
 '[
   {"name_norm": "beef", "amount_g": 120},
   {"name_norm": "broccoli", "amount_g": 100},
   {"name_norm": "olive_oil", "amount_g": 12},
   {"name_norm": "garlic", "amount_g": 5},
   {"name_norm": "soy_sauce", "amount_g": 8}
 ]'::jsonb,
 '["소고기를 한입 크기로 자른다", "브로콜리를 데친다", "올리브오일에 마늘을 볶는다", "소고기를 넣고 볶는다", "브로콜리를 넣고 간장으로 간한다"]'::jsonb,
 ARRAY['keto', 'stir_fry', 'beef', 'broccoli'],
 '{"carb_g": 8, "protein_g": 32, "fat_g": 24, "kcal": 400}'::jsonb),

-- 26. 새우 애호박 볶음
('새우 애호박 볶음', 1,
 '[
   {"name_norm": "shrimp", "amount_g": 120},
   {"name_norm": "zucchini", "amount_g": 100},
   {"name_norm": "olive_oil", "amount_g": 12},
   {"name_norm": "garlic", "amount_g": 5},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["새우의 내장을 제거한다", "애호박을 슬라이스한다", "올리브오일에 마늘을 볶는다", "새우와 애호박을 넣고 볶는다", "소금으로 간한다"]'::jsonb,
 ARRAY['keto', 'stir_fry', 'shrimp', 'zucchini'],
 '{"carb_g": 6, "protein_g": 28, "fat_g": 18, "kcal": 320}'::jsonb),

-- 27. 버섯 볶음
('버섯 볶음', 1,
 '[
   {"name_norm": "mushroom", "amount_g": 150},
   {"name_norm": "butter", "amount_g": 15},
   {"name_norm": "garlic", "amount_g": 5},
   {"name_norm": "salt", "amount_g": 2},
   {"name_norm": "pepper", "amount_g": 1}
 ]'::jsonb,
 '["버섯을 슬라이스한다", "버터를 두른 팬에 마늘을 볶는다", "버섯을 넣고 볶는다", "소금, 후추로 간한다"]'::jsonb,
 ARRAY['keto', 'stir_fry', 'mushroom', 'vegetarian'],
 '{"carb_g": 5, "protein_g": 6, "fat_g": 16, "kcal": 200}'::jsonb),

-- 28. 양배추 볶음
('양배추 볶음', 1,
 '[
   {"name_norm": "cabbage", "amount_g": 120},
   {"name_norm": "bacon", "amount_g": 60},
   {"name_norm": "olive_oil", "amount_g": 10},
   {"name_norm": "garlic", "amount_g": 5},
   {"name_norm": "salt", "amount_g": 2}
 ]'::jsonb,
 '["양배추를 한입 크기로 자른다", "베이콘을 잘게 자른다", "올리브오일에 마늘을 볶는다", "베이콘을 볶는다", "양배추를 넣고 볶는다"]'::jsonb,
 ARRAY['keto', 'stir_fry', 'cabbage', 'bacon'],
 '{"carb_g": 7, "protein_g": 18, "fat_g": 32, "kcal": 400}'::jsonb),

-- 29. 파프리카 소고기 볶음
('파프리카 소고기 볶음', 1,
 '[
   {"name_norm": "beef", "amount_g": 110},
   {"name_norm": "bell_pepper", "amount_g": 100},
   {"name_norm": "olive_oil", "amount_g": 12},
   {"name_norm": "onion", "amount_g": 30},
   {"name_norm": "soy_sauce", "amount_g": 8}
 ]'::jsonb,
 '["소고기를 한입 크기로 자른다", "파프리카와 양파를 자른다", "올리브오일에 양파를 볶는다", "소고기를 넣고 볶는다", "파프리카를 넣고 간장으로 간한다"]'::jsonb,
 ARRAY['keto', 'stir_fry', 'beef', 'bell_pepper'],
 '{"carb_g": 9, "protein_g": 30, "fat_g": 22, "kcal": 380}'::jsonb),

-- 30. 두부면 볶음
('두부면 볶음', 1,
 '[
   {"name_norm": "tofu_noodles", "amount_g": 100},
   {"name_norm": "chicken_breast", "amount_g": 80},
   {"name_norm": "zucchini", "amount_g": 60},
   {"name_norm": "olive_oil", "amount_g": 12},
   {"name_norm": "soy_sauce", "amount_g": 8},
   {"name_norm": "garlic", "amount_g": 5}
 ]'::jsonb,
 '["두부면을 물에 헹군다", "닭고기와 애호박을 자른다", "올리브오일에 마늘을 볶는다", "닭고기를 볶는다", "애호박과 두부면을 넣고 간장으로 볶는다"]'::jsonb,
 ARRAY['keto', 'stir_fry', 'tofu_noodles', 'low_carb'],
 '{"carb_g": 8, "protein_g": 26, "fat_g": 18, "kcal": 320}'::jsonb);

-- =========================================
-- 공통 변형 규칙 추가
-- =========================================

-- 모든 골든셋에 공통 변형 규칙 적용
INSERT INTO transform_rules (base_recipe_id, swaps_json, amount_limits_json, forbidden_json)
SELECT 
  id,
  '[
    {"from": "wheat_noodles", "to": "tofu_noodles", "ratio": 1.0},
    {"from": "rice", "to": "konjac_rice", "ratio": 1.0},
    {"from": "wheat_flour", "to": "almond_flour", "ratio": 0.8}
  ]'::jsonb,
  '[
    {"name_norm": "olive_oil", "min_g": 5, "max_g": 25},
    {"name_norm": "butter", "min_g": 5, "max_g": 20},
    {"name_norm": "salt", "min_g": 1, "max_g": 5},
    {"name_norm": "soy_sauce", "min_g": 5, "max_g": 15}
  ]'::jsonb,
  '["sugar", "honey", "rice", "wheat_flour", "noodle_wheat", "potato", "sweet_potato", "corn", "bread"]'::jsonb
FROM golden_recipes
WHERE NOT EXISTS (
  SELECT 1 FROM transform_rules WHERE base_recipe_id = golden_recipes.id
);

-- =========================================
-- 완료 메시지
-- =========================================

DO $$
DECLARE
  recipe_count INTEGER;
  rule_count INTEGER;
  ingredient_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO recipe_count FROM golden_recipes WHERE is_active = true;
  SELECT COUNT(*) INTO rule_count FROM transform_rules;
  SELECT COUNT(*) INTO ingredient_count FROM ingredient_normalization;
  
  RAISE NOTICE '✅ 골든셋 데이터 삽입 완료';
  RAISE NOTICE '📊 골든셋 레시피: %개', recipe_count;
  RAISE NOTICE '📊 변형 규칙: %개', rule_count;
  RAISE NOTICE '📊 정규화 재료: %개', ingredient_count;
END $$;

