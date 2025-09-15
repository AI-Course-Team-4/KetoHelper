# Supabase Dashboard에서 수동으로 실행할 SQL 명령어들

## 1단계: pgvector 확장 활성화
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 2단계: 올바른 vector 컬럼 추가
```sql
ALTER TABLE recipes_hybrid_ingredient_llm ADD COLUMN embedding_vec vector(1536);
```

## 3단계: 기존 데이터를 vector 타입으로 변환
```sql
UPDATE recipes_hybrid_ingredient_llm 
SET embedding_vec = (
  SELECT array_agg((e)::float4)::vector
  FROM jsonb_array_elements_text(embedding::jsonb) AS x(e)
)
WHERE embedding IS NOT NULL;
```

## 4단계: 기존 embedding 컬럼 삭제
```sql
ALTER TABLE recipes_hybrid_ingredient_llm DROP COLUMN embedding;
```

## 5단계: 새로운 컬럼을 embedding으로 이름 변경
```sql
ALTER TABLE recipes_hybrid_ingredient_llm RENAME COLUMN embedding_vec TO embedding;
```

## 6단계: 올바른 ivfflat 인덱스 생성
```sql
CREATE INDEX IF NOT EXISTS recipes_hybrid_ingredient_llm_embedding_ivfflat
ON recipes_hybrid_ingredient_llm USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## 7단계: search_hybrid_recipes 함수 수정
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

## 실행 방법:
1. Supabase Dashboard → SQL Editor로 이동
2. 위 명령어들을 순서대로 하나씩 실행
3. 각 단계마다 성공 메시지 확인

## 주의사항:
- 3단계에서 데이터 변환 시 시간이 걸릴 수 있습니다 (210개 레코드)
- 각 단계를 순서대로 실행해야 합니다
- 실패 시 이전 단계부터 다시 실행하세요
