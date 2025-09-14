# PRD — 개인화 레시피 추천 시스템 (핵심 요약)

> 목적: 사용자의 비선호/알러지 정보를 기반으로 하드필터링하고, 선호 식재료를 통해 키워드/벡터 검색으로 레시피를 추천한다.

## 1) 목적 (TL;DR)
- 사용자의 **비선호/알러지 식재료**를 하드필터로 제외
- 사용자의 **선호 식재료**를 기반으로 키워드/벡터 검색
- 기존 DB 레시피 3개 추천 → 만족하지 않으면 **새 레시피 생성**
- 자연어 쿼리 처리 (하이브리드 검색)

## 2) 범위
**포함**
- 사용자 개인화 정보 관리 (비선호/알러지/선호 식재료)
- 임베딩 생성 및 벡터 검색
- 하드필터 + 키워드/벡터 하이브리드 검색
- 자연어 쿼리 처리
- 기존 레시피 추천 (최대 3개)
- 새 레시피 생성 (AI 기반)

**제외**
- 사용자 인증/회원가입
- 레시피 평가/리뷰 시스템
- 소셜 기능

## 3) 데이터 모델 (DDL 확장)
```sql
-- 사용자 개인화 정보 테이블
create table if not exists user_preferences (
  user_id uuid primary key,
  disliked_ingredients text[],           -- 비선호 식재료
  allergies text[],                      -- 알러지 식재료
  preferred_ingredients text[],          -- 선호 식재료
  preference_embedding vector(1536),     -- 사용자 취향 벡터
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 레시피 임베딩 테이블 (기존 recipes_keto_raw 확장)
-- embedding 컬럼이 이미 있으므로 추가 작업 불필요

-- 검색 이력 테이블
create table if not exists search_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  query text not null,                   -- 자연어 쿼리
  search_type text not null,             -- 'keyword', 'vector', 'hybrid'
  results_count int default 0,
  created_at timestamptz not null default now()
);

-- 인덱스 생성
create index if not exists idx_user_preferences_ingredients on user_preferences using gin(disliked_ingredients);
create index if not exists idx_user_preferences_allergies on user_preferences using gin(allergies);
create index if not exists idx_user_preferences_preferred on user_preferences using gin(preferred_ingredients);
create index if not exists idx_user_preferences_embedding on user_preferences using ivfflat (preference_embedding vector_cosine_ops);
create index if not exists idx_recipes_embedding on recipes_keto_raw using ivfflat (embedding vector_cosine_ops);
create index if not exists idx_search_history_user on search_history (user_id);
```

## 4) 핵심 기능

### 4.1 사용자 개인화 정보 관리
```python
# 사용자 선호도 설정
async def set_user_preferences(
    user_id: str,
    disliked_ingredients: List[str],
    allergies: List[str], 
    preferred_ingredients: List[str]
):
    # 1. 개인화 정보 저장
    # 2. 선호도 기반 임베딩 생성
    # 3. 사용자 벡터 업데이트
```

### 4.2 하드필터 + 하이브리드 검색
```python
async def search_recipes(
    user_id: str,
    query: str,
    search_type: str = "hybrid"  # keyword, vector, hybrid
) -> List[Dict]:
    # 1. 사용자 개인화 정보 로드
    # 2. 하드필터 적용 (비선호/알러지 제외)
    # 3. 키워드/벡터 검색 실행
    # 4. 결과 랭킹 및 반환 (최대 3개)
```

### 4.3 임베딩 생성 및 관리
```python
# 레시피 임베딩 생성
async def generate_recipe_embeddings():
    # 1. 임베딩이 없는 레시피 조회
    # 2. OpenAI API로 임베딩 생성
    # 3. DB 업데이트

# 사용자 취향 임베딩 생성
async def generate_user_embedding(user_id: str):
    # 1. 사용자 선호도 정보 수집
    # 2. 선호도 기반 임베딩 생성
    # 3. 사용자 벡터 업데이트
```

### 4.4 새 레시피 생성
```python
async def generate_new_recipe(
    user_id: str,
    query: str,
    existing_recipes: List[Dict]
) -> Dict:
    # 1. 사용자 선호도 정보 로드
    # 2. 기존 레시피와 차별화된 요구사항 생성
    # 3. AI로 새 레시피 생성
    # 4. 임베딩 생성 및 DB 저장
```

## 5) 검색 전략

### 5.1 하드필터 (필수)
```sql
-- 비선호/알러지 식재료 제외
WHERE NOT (
  ingredients && user_preferences.disliked_ingredients OR
  ingredients && user_preferences.allergies
)
```

### 5.2 키워드 검색 (pg_trgm)
```sql
-- 자연어 쿼리 + 선호 식재료
WHERE search_blob % query_text
ORDER BY similarity(search_blob, query_text) DESC
```

### 5.3 벡터 검색 (pgvector)
```sql
-- 사용자 취향과 레시피 유사도
ORDER BY user_preferences.preference_embedding <=> recipes_keto_raw.embedding
```

### 5.4 하이브리드 검색
```sql
-- 키워드 + 벡터 조합
SELECT *, 
  (similarity(search_blob, query_text) * 0.6 + 
   (1 - (user_embedding <=> recipe_embedding)) * 0.4) as score
ORDER BY score DESC
```

## 6) 구현 요구사항

### 6.1 임베딩 생성 파이프라인
1. **레시피 임베딩**: `search_blob` 기반 OpenAI embedding
2. **사용자 임베딩**: 선호도 정보 기반 임베딩
3. **배치 처리**: 대량 임베딩 생성 시 rate limit 고려

### 6.2 검색 엔진
1. **하드필터**: 비선호/알러지 식재료 완전 제외
2. **키워드 검색**: pg_trgm 기반 유사도 검색
3. **벡터 검색**: pgvector 기반 코사인 유사도
4. **하이브리드**: 가중치 기반 점수 조합

### 6.3 새 레시피 생성
1. **차별화**: 기존 레시피와 다른 요구사항 생성
2. **개인화**: 사용자 선호도 반영
3. **품질 보장**: 임베딩 생성 및 검증

## 7) API 설계

### 7.1 사용자 선호도 관리
```python
# 선호도 설정
POST /api/user/preferences
{
  "user_id": "uuid",
  "disliked_ingredients": ["양파", "마늘"],
  "allergies": ["견과류", "해산물"],
  "preferred_ingredients": ["닭고기", "브로콜리"]
}

# 선호도 조회
GET /api/user/preferences/{user_id}
```

### 7.2 레시피 검색
```python
# 하이브리드 검색
POST /api/recipes/search
{
  "user_id": "uuid",
  "query": "간단한 닭고기 요리",
  "search_type": "hybrid",
  "limit": 3
}

# 새 레시피 생성
POST /api/recipes/generate
{
  "user_id": "uuid", 
  "query": "간단한 닭고기 요리",
  "existing_recipes": [...]
}
```

## 8) 수용 기준(AC)

### 8.1 성능
- 검색 응답시간 ≤ 2초
- 임베딩 생성 처리량 ≥ 100건/분
- 하드필터 정확도 100%

### 8.2 품질
- 추천 레시피 개인화 정확도 ≥ 80%
- 새 레시피 생성 품질 ≥ 70%
- 중복 레시피 제거율 ≥ 95%


## 9) 기술 스택

### 9.1 백엔드
- **Python**: FastAPI, asyncio
- **DB**: Supabase (PostgreSQL + pgvector + pg_trgm)
- **AI**: OpenAI API (text-embedding-3 small, GPT-4o-mini)
- **검색**: 하이브리드 (키워드 + 벡터)

### 9.2 의존성 추가
```txt
openai==1.3.0
fastapi==0.104.1
uvicorn==0.24.0
numpy==1.24.3
```

## 10) 구현 순서

### Phase 1: 기본 인프라
1. 사용자 개인화 테이블 생성
2. 임베딩 생성 파이프라인 구축
3. 하드필터 검색 구현

### Phase 2: 검색 엔진
1. 키워드 검색 (pg_trgm) 구현
2. 벡터 검색 (pgvector) 구현
3. 하이브리드 검색 구현

### Phase 3: AI 통합
1. 새 레시피 생성 기능
2. 자연어 쿼리 처리
3. 개인화 최적화

### Phase 4: 최적화
1. 성능 튜닝
2. 캐싱 전략
3. 모니터링 구축

## 11) 스타트 가이드

### 11.1 환경 설정
```bash
# 의존성 설치
pip install openai fastapi uvicorn numpy

# 환경변수 설정
OPENAI_API_KEY=your_key_here
```

### 11.2 DB 스키마 적용
```sql
-- database_setup.sql의 확장 스키마 실행
-- 사용자 개인화 테이블 생성
-- 인덱스 생성
```

### 11.3 테스트 실행
```python
# 임베딩 생성 테스트
python -m src.embedding_generator

# 검색 기능 테스트  
python -m src.search_engine_test
```

이 PRD는 기존 크롤링 시스템을 확장하여 개인화 추천 기능을 구현하는 완전한 가이드입니다.
