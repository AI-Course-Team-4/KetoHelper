-- 시맨틱 캐시 테이블 생성
CREATE TABLE IF NOT EXISTS semantic_cache (
  id           BIGSERIAL PRIMARY KEY,
  user_id      UUID        NOT NULL,
  model_ver    TEXT        NOT NULL,
  opts_hash    TEXT        NOT NULL,  -- 날짜/지역/식단 제약 등
  prompt_hash  TEXT        NOT NULL,  -- 정규화 텍스트 sha256
  answer       TEXT        NOT NULL,
  meta         JSONB       NOT NULL,  -- {route, diet, area, etc}
  embedding    VECTOR(1536) NOT NULL, -- 임베딩 차원에 맞추기
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS sc_vec_idx
  ON semantic_cache USING IVFFLAT (embedding VECTOR_COSINE_OPS) WITH (lists=100);

CREATE INDEX IF NOT EXISTS sc_meta_idx
  ON semantic_cache (user_id, model_ver, opts_hash, created_at DESC);

-- 시맨틱 매칭 RPC 함수
CREATE OR REPLACE FUNCTION sc_match(
  query_vec VECTOR,
  p_user UUID,
  p_model_ver TEXT,
  p_opts_hash TEXT,
  p_window_seconds INT,
  p_limit INT DEFAULT 1
)
RETURNS TABLE(id BIGINT, answer TEXT, score FLOAT, meta JSONB)
LANGUAGE SQL STABLE AS $$
  SELECT id, answer,
         1 - (embedding <=> query_vec) AS score,  -- cosine 유사도
         meta
  FROM semantic_cache
  WHERE user_id = p_user
    AND model_ver = p_model_ver
    AND opts_hash = p_opts_hash
    AND created_at > NOW() - (p_window_seconds || ' seconds')::INTERVAL
  ORDER BY embedding <=> query_vec
  LIMIT p_limit;
$$;
