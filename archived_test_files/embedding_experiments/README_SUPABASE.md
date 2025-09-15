# Supabase 기반 레시피 임베딩 실험

3가지 다른 임베딩 방식으로 레시피 검색 성능을 비교하는 실험 (Supabase 버전)

## 🚀 빠른 시작

### 1. 환경변수 설정
```bash
# Windows
set SUPABASE_URL=your_supabase_project_url
set SUPABASE_ANON_KEY=your_supabase_anon_key
set OPENAI_API_KEY=your_openai_api_key  # 방식3용 (선택사항)

# Linux/Mac
export SUPABASE_URL=your_supabase_project_url
export SUPABASE_ANON_KEY=your_supabase_anon_key
export OPENAI_API_KEY=your_openai_api_key  # 방식3용 (선택사항)
```

### 2. Supabase 테이블 설정
```bash
python run_supabase_experiment.py --mode init
```

위 명령으로 출력되는 SQL을 Supabase SQL Editor에서 실행하세요.

### 3. 빠른 테스트
```bash
python run_supabase_experiment.py --mode test
```

### 4. 전체 실험 실행
```bash
python run_supabase_experiment.py --mode full
```

## 🏗️ Supabase 설정

### 필요한 확장과 테이블

1. **pgvector 확장 활성화**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

2. **임베딩 테이블 생성 (3개)**
```sql
-- 방식1: 제목 포함
CREATE TABLE recipes_title_blob (
    id BIGSERIAL PRIMARY KEY,
    recipe_id TEXT UNIQUE,
    title TEXT,
    processed_content TEXT,
    raw_content JSONB,
    embedding vector(768),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);

-- 방식2: 제목 제외
CREATE TABLE recipes_no_title_blob (
    id BIGSERIAL PRIMARY KEY,
    recipe_id TEXT UNIQUE,
    title TEXT,
    processed_content TEXT,
    raw_content JSONB,
    embedding vector(768),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);

-- 방식3: LLM 전처리
CREATE TABLE recipes_llm_preprocessing (
    id BIGSERIAL PRIMARY KEY,
    recipe_id TEXT UNIQUE,
    title TEXT,
    processed_content TEXT,
    raw_content JSONB,
    embedding vector(768),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);
```

3. **벡터 검색 인덱스**
```sql
CREATE INDEX ON recipes_title_blob USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON recipes_no_title_blob USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON recipes_llm_preprocessing USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

4. **벡터 검색 함수**
```sql
CREATE OR REPLACE FUNCTION search_recipes(
  query_embedding vector(768),
  table_name text,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  recipe_id text,
  title text,
  processed_content text,
  raw_content jsonb,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  EXECUTE format('
    SELECT r.recipe_id, r.title, r.processed_content, r.raw_content, r.metadata,
           1 - (r.embedding <=> $1) as similarity
    FROM %I r
    ORDER BY r.embedding <=> $1
    LIMIT $2
  ', table_name)
  USING query_embedding, match_count;
END;
$$;
```

## 📊 3가지 임베딩 방식

### 방식 1: 레시피명 + 식재료 임베딩
- **파일**: `approach1_title_blob/approach1_supabase.py`
- **특징**: 제목과 식재료만으로 구성
- **장점**: 제목과 재료 기반 검색에 최적화
- **테이블**: `recipes_title_blob`

### 방식 2: 식재료 전용 임베딩
- **파일**: `approach2_no_title_blob/approach2_supabase.py`
- **특징**: 식재료 + 메타정보(설명, 태그)만으로 구성
- **장점**: 순수 재료 기반 매칭에 특화
- **테이블**: `recipes_no_title_blob`

### 방식 3: LLM 전처리 + 임베딩
- **파일**: `approach3_llm_preprocessing/approach3_supabase.py`
- **특징**: GPT-4o-mini로 레시피 정보를 구조화하여 처리
- **장점**: 의미론적 검색 성능 우수
- **테이블**: `recipes_llm_preprocessing`
- **요구사항**: OpenAI API 키

## 🔧 실행 옵션

```bash
# 테이블 설정 SQL 출력
python run_supabase_experiment.py --mode init

# Supabase 연결 테스트
python run_supabase_experiment.py --mode test

# 데이터 로드만 (각 방식별 50개씩)
python run_supabase_experiment.py --mode setup

# 평가만 실행
python run_supabase_experiment.py --mode eval

# 전체 실험 (설정 + 평가)
python run_supabase_experiment.py --mode full
```

## 📈 성능 측정

- **검색 결과 수**: 각 쿼리별 반환된 결과 개수
- **평균 유사도**: 검색된 결과들의 코사인 유사도 평균
- **응답 시간**: 검색 요청부터 결과 반환까지의 시간

## 🎯 테스트 쿼리

30개의 다양한 테스트 쿼리:
- 재료 기반: "닭고기 요리", "감자 요리"
- 요리법 기반: "볶음밥", "찌개"
- 특성 기반: "매운 요리", "간단한 요리"
- 상황별: "아침 식사", "다이어트 음식"

## ⚠️ 주의사항

1. **Supabase 프로젝트 설정**
   - pgvector 확장이 활성화되어 있어야 함
   - 적절한 RLS (Row Level Security) 정책 설정 필요

2. **API 제한**
   - OpenAI API는 사용량에 따른 과금
   - Supabase는 프로젝트 용량과 요청 수 제한

3. **벡터 인덱스**
   - 대량의 데이터에서는 인덱스 생성이 시간이 걸림
   - `lists` 파라미터는 데이터 크기에 따라 조정 필요

## 🔍 문제 해결

### 연결 오류
```
Error: 401 Unauthorized
```
- `SUPABASE_URL`과 `SUPABASE_ANON_KEY` 확인

### 벡터 검색 오류
```
relation "recipes_title_blob" does not exist
```
- 테이블 생성 SQL 실행 확인

### LLM 처리 오류
```
OpenAI API key not found
```
- `OPENAI_API_KEY` 환경변수 설정

## 📝 결과 해석

실험 완료 후 다음과 같은 결과를 분석할 수 있습니다:

- **방식별 검색 성능**: 어떤 방식이 더 관련성 높은 결과를 반환하는가
- **응답 속도**: 실시간 서비스에 적합한 응답 시간인가
- **리소스 사용량**: API 비용과 처리 시간의 트레이드오프

이를 바탕으로 서비스 요구사항에 가장 적합한 임베딩 방식을 선택할 수 있습니다.