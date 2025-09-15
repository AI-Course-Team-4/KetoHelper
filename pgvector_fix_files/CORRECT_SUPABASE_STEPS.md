# 올바른 pgvector 수정 단계

## 현재 상황
- ✅ `embedding` 컬럼이 이미 `vector(1536)` 타입으로 설정됨
- ❌ pgvector 인덱스가 올바르지 않거나 없음
- ❌ `search_hybrid_recipes` 함수가 제대로 작동하지 않음

## Supabase Dashboard에서 실행할 SQL

### 1단계: pgvector 확장 활성화
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2단계: 기존 인덱스 삭제 및 올바른 인덱스 생성
```sql
DROP INDEX IF EXISTS recipes_hybrid_ingredient_llm_embedding_ivfflat;
CREATE INDEX recipes_hybrid_ingredient_llm_embedding_ivfflat
ON recipes_hybrid_ingredient_llm USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### 3단계: search_hybrid_recipes 함수 수정
```sql
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
2. 위 명령어들을 순서대로 실행
3. 각 단계마다 성공 메시지 확인

## 주의사항
- **데이터 마이그레이션은 필요 없음** (이미 vector 타입)
- **인덱스 재생성**이 핵심 (기존 인덱스가 잘못되었을 가능성)
- **함수 수정**으로 pgvector 연산자(`<=>`) 사용
