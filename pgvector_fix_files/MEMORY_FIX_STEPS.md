# 메모리 부족 오류 해결 단계

## 문제
- `maintenance_work_mem`이 32MB로 설정됨
- ivfflat 인덱스 생성에 61MB 필요
- 메모리 부족으로 인덱스 생성 실패

## 해결 방법

### Supabase Dashboard에서 실행할 SQL

```sql
-- 1. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 메모리 설정 임시 증가 (인덱스 생성용)
SET maintenance_work_mem = '128MB';

-- 3. 기존 인덱스 삭제
DROP INDEX IF EXISTS recipes_hybrid_ingredient_llm_embedding_ivfflat;

-- 4. 올바른 ivfflat 인덱스 생성 (메모리 증가 후)
CREATE INDEX recipes_hybrid_ingredient_llm_embedding_ivfflat
ON recipes_hybrid_ingredient_llm USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 5. search_hybrid_recipes 함수 수정
CREATE OR REPLACE FUNCTION search_hybrid_recipes(
  query_embedding vector(1536),
  match_count int DEFAULT 10
)
RETURNS TABLE (
  recipe_id text,
  title text,
  structured_blob text,
  llm_metadata jsonb,
  basic_metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT r.recipe_id, r.title, r.structured_blob, r.llm_metadata, r.basic_metadata,
         1 - (r.embedding <=> $1) as similarity
  FROM recipes_hybrid_ingredient_llm r
  ORDER BY r.embedding <=> $1
  LIMIT $2;
END;
$$;
```

## 실행 방법
1. Supabase Dashboard → SQL Editor
2. 위 SQL을 **한 번에 모두 실행** (세미콜론으로 구분)
3. 성공 메시지 확인

## 주의사항
- `SET maintenance_work_mem = '128MB'`는 **세션 동안만** 유효
- 인덱스 생성 후 자동으로 원래 설정으로 돌아감
- **한 번에 실행**해야 메모리 설정이 유지됨
