-- 식당 하이브리드 검색용 Supabase RPC 함수들
-- 실제 스키마 기반: restaurant, menu, menu_embedding, keto_scores

-- 1. 식당 메뉴 벡터 검색 함수
CREATE OR REPLACE FUNCTION restaurant_menu_vector_search(
  query_embedding VECTOR(1536),
  match_count INTEGER DEFAULT 5,
  similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
  restaurant_id UUID,
  restaurant_name TEXT,
  restaurant_category TEXT,
  addr_road TEXT,
  addr_jibun TEXT,
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  phone TEXT,
  menu_id UUID,
  menu_name TEXT,
  menu_description TEXT,
  menu_price INTEGER,
  keto_score INTEGER,
  keto_reasons JSONB,
  vector_score DOUBLE PRECISION,
  search_type TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    r.id as restaurant_id,
    r.name as restaurant_name,
    r.category as restaurant_category,
    r.addr_road,
    r.addr_jibun,
    r.lat,
    r.lng,
    r.phone,
    m.id as menu_id,
    m.name as menu_name,
    m.description as menu_description,
    m.price as menu_price,
    COALESCE(ks.score, 0) as keto_score,
    ks.reasons_json as keto_reasons,
    (1 - (me.embedding <=> query_embedding))::DOUBLE PRECISION as vector_score,
    'vector'::TEXT as search_type
  FROM menu_embedding me
  JOIN menu m ON me.menu_id = m.id
  JOIN restaurant r ON m.restaurant_id = r.id
  LEFT JOIN keto_scores ks ON m.id = ks.menu_id
  WHERE me.embedding IS NOT NULL
    AND (1 - (me.embedding <=> query_embedding)) > similarity_threshold
  ORDER BY me.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 2. 식당 키워드 검색 함수 (ILIKE)
CREATE OR REPLACE FUNCTION restaurant_ilike_search(
  query_text TEXT,
  match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
  restaurant_id UUID,
  restaurant_name TEXT,
  restaurant_category TEXT,
  addr_road TEXT,
  addr_jibun TEXT,
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  phone TEXT,
  menu_id UUID,
  menu_name TEXT,
  menu_description TEXT,
  menu_price INTEGER,
  keto_score INTEGER,
  keto_reasons JSONB,
  ilike_score DOUBLE PRECISION,
  search_type TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    r.id as restaurant_id,
    r.name as restaurant_name,
    r.category as restaurant_category,
    r.addr_road,
    r.addr_jibun,
    r.lat,
    r.lng,
    r.phone,
    m.id as menu_id,
    m.name as menu_name,
    m.description as menu_description,
    m.price as menu_price,
    COALESCE(ks.score, 0) as keto_score,
    ks.reasons_json as keto_reasons,
    CASE
      WHEN r.name ILIKE '%' || query_text || '%' THEN 0.9
      WHEN m.name ILIKE '%' || query_text || '%' THEN 0.8
      WHEN r.category ILIKE '%' || query_text || '%' THEN 0.7
      WHEN m.description ILIKE '%' || query_text || '%' THEN 0.6
      WHEN r.addr_road ILIKE '%' || query_text || '%' THEN 0.5
      ELSE 0.4
    END::DOUBLE PRECISION as ilike_score,
    'ilike'::TEXT as search_type
  FROM restaurant r
  JOIN menu m ON r.id = m.restaurant_id
  LEFT JOIN keto_scores ks ON m.id = ks.menu_id
  WHERE r.name ILIKE '%' || query_text || '%'
     OR m.name ILIKE '%' || query_text || '%'
     OR r.category ILIKE '%' || query_text || '%'
     OR m.description ILIKE '%' || query_text || '%'
     OR r.addr_road ILIKE '%' || query_text || '%'
  ORDER BY ilike_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 3. 식당 Trigram 유사도 검색 함수
CREATE OR REPLACE FUNCTION restaurant_trgm_search(
  query_text TEXT,
  match_count INTEGER DEFAULT 5,
  similarity_threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE (
  restaurant_id UUID,
  restaurant_name TEXT,
  restaurant_category TEXT,
  addr_road TEXT,
  addr_jibun TEXT,
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  phone TEXT,
  menu_id UUID,
  menu_name TEXT,
  menu_description TEXT,
  menu_price INTEGER,
  keto_score INTEGER,
  keto_reasons JSONB,
  trigram_score DOUBLE PRECISION,
  search_type TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    r.id as restaurant_id,
    r.name as restaurant_name,
    r.category as restaurant_category,
    r.addr_road,
    r.addr_jibun,
    r.lat,
    r.lng,
    r.phone,
    m.id as menu_id,
    m.name as menu_name,
    m.description as menu_description,
    m.price as menu_price,
    COALESCE(ks.score, 0) as keto_score,
    ks.reasons_json as keto_reasons,
    GREATEST(
      similarity(r.name, query_text),
      similarity(m.name, query_text),
      similarity(COALESCE(r.category, ''), query_text),
      similarity(COALESCE(m.description, ''), query_text)
    )::DOUBLE PRECISION as trigram_score,
    'trigram'::TEXT as search_type
  FROM restaurant r
  JOIN menu m ON r.id = m.restaurant_id
  LEFT JOIN keto_scores ks ON m.id = ks.menu_id
  WHERE r.name % query_text
     OR m.name % query_text
     OR COALESCE(r.category, '') % query_text
     OR COALESCE(m.description, '') % query_text
  ORDER BY trigram_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 4. 통합 하이브리드 검색 함수
CREATE OR REPLACE FUNCTION restaurant_hybrid_search(
  query_text TEXT,
  query_embedding VECTOR(1536),
  match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
  restaurant_id UUID,
  restaurant_name TEXT,
  restaurant_category TEXT,
  addr_road TEXT,
  addr_jibun TEXT,
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  phone TEXT,
  menu_id UUID,
  menu_name TEXT,
  menu_description TEXT,
  menu_price INTEGER,
  keto_score INTEGER,
  keto_reasons JSONB,
  vector_score DOUBLE PRECISION,
  ilike_score DOUBLE PRECISION,
  trigram_score DOUBLE PRECISION,
  final_score DOUBLE PRECISION,
  search_type TEXT
) AS $$
DECLARE
  vector_weight FLOAT := 0.5;
  ilike_weight FLOAT := 0.3;
  trigram_weight FLOAT := 0.2;
  keto_bonus FLOAT := 0.1;
BEGIN
  RETURN QUERY
  WITH vector_results AS (
    SELECT * FROM restaurant_menu_vector_search(query_embedding, match_count * 2)
  ),
  ilike_results AS (
    SELECT * FROM restaurant_ilike_search(query_text, match_count * 2)
  ),
  trigram_results AS (
    SELECT * FROM restaurant_trgm_search(query_text, match_count * 2)
  ),
  combined_results AS (
    SELECT
      COALESCE(v.restaurant_id, i.restaurant_id, t.restaurant_id) as restaurant_id,
      COALESCE(v.restaurant_name, i.restaurant_name, t.restaurant_name) as restaurant_name,
      COALESCE(v.restaurant_category, i.restaurant_category, t.restaurant_category) as restaurant_category,
      COALESCE(v.addr_road, i.addr_road, t.addr_road) as addr_road,
      COALESCE(v.addr_jibun, i.addr_jibun, t.addr_jibun) as addr_jibun,
      COALESCE(v.lat, i.lat, t.lat) as lat,
      COALESCE(v.lng, i.lng, t.lng) as lng,
      COALESCE(v.phone, i.phone, t.phone) as phone,
      COALESCE(v.menu_id, i.menu_id, t.menu_id) as menu_id,
      COALESCE(v.menu_name, i.menu_name, t.menu_name) as menu_name,
      COALESCE(v.menu_description, i.menu_description, t.menu_description) as menu_description,
      COALESCE(v.menu_price, i.menu_price, t.menu_price) as menu_price,
      COALESCE(v.keto_score, i.keto_score, t.keto_score, 0) as keto_score,
      COALESCE(v.keto_reasons, i.keto_reasons, t.keto_reasons) as keto_reasons,
      COALESCE(v.vector_score, 0.0) as vector_score,
      COALESCE(i.ilike_score, 0.0) as ilike_score,
      COALESCE(t.trigram_score, 0.0) as trigram_score
    FROM vector_results v
    FULL OUTER JOIN ilike_results i ON v.menu_id = i.menu_id
    FULL OUTER JOIN trigram_results t ON COALESCE(v.menu_id, i.menu_id) = t.menu_id
  )
  SELECT
    cr.restaurant_id,
    cr.restaurant_name,
    cr.restaurant_category,
    cr.addr_road,
    cr.addr_jibun,
    cr.lat,
    cr.lng,
    cr.phone,
    cr.menu_id,
    cr.menu_name,
    cr.menu_description,
    cr.menu_price,
    cr.keto_score,
    cr.keto_reasons,
    cr.vector_score,
    cr.ilike_score,
    cr.trigram_score,
    (cr.vector_score * vector_weight + 
     cr.ilike_score * ilike_weight + 
     cr.trigram_score * trigram_weight +
     CASE WHEN cr.keto_score >= 70 THEN keto_bonus ELSE 0.0 END
    )::DOUBLE PRECISION as final_score,
    'hybrid'::TEXT as search_type
  FROM combined_results cr
  ORDER BY final_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 5. 위치 기반 식당 검색 함수 (추가)
CREATE OR REPLACE FUNCTION restaurant_nearby_search(
  center_lat DOUBLE PRECISION,
  center_lng DOUBLE PRECISION,
  radius_km DOUBLE PRECISION DEFAULT 5.0,
  query_text TEXT DEFAULT '',
  match_count INTEGER DEFAULT 10
)
RETURNS TABLE (
  restaurant_id UUID,
  restaurant_name TEXT,
  restaurant_category TEXT,
  addr_road TEXT,
  addr_jibun TEXT,
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  phone TEXT,
  distance_km DOUBLE PRECISION,
  avg_keto_score DOUBLE PRECISION
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    r.id as restaurant_id,
    r.name as restaurant_name,
    r.category as restaurant_category,
    r.addr_road,
    r.addr_jibun,
    r.lat,
    r.lng,
    r.phone,
    (6371 * acos(cos(radians(center_lat)) * cos(radians(r.lat)) * 
     cos(radians(r.lng) - radians(center_lng)) + 
     sin(radians(center_lat)) * sin(radians(r.lat))))::DOUBLE PRECISION as distance_km,
    COALESCE(AVG(ks.score), 0.0)::DOUBLE PRECISION as avg_keto_score
  FROM restaurant r
  LEFT JOIN menu m ON r.id = m.restaurant_id
  LEFT JOIN keto_scores ks ON m.id = ks.menu_id
  WHERE (6371 * acos(cos(radians(center_lat)) * cos(radians(r.lat)) * 
         cos(radians(r.lng) - radians(center_lng)) + 
         sin(radians(center_lat)) * sin(radians(r.lat)))) <= radius_km
    AND (query_text = '' OR r.name ILIKE '%' || query_text || '%' OR r.category ILIKE '%' || query_text || '%')
  GROUP BY r.id, r.name, r.category, r.addr_road, r.addr_jibun, r.lat, r.lng, r.phone
  ORDER BY avg_keto_score DESC, distance_km ASC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 완료 메시지
SELECT '식당 하이브리드 검색 RPC 함수들 생성 완료!' as result;
