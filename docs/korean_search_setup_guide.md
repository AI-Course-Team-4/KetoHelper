# 한글 검색 최적화 설정 가이드

## 📋 개요

PostgreSQL Full-Text Search + pg_trgm + 벡터 검색을 통한 한글 검색 성능 최적화

## 🚀 설정 단계

### 1단계: Supabase 데이터베이스 설정

#### 1.1 PostgreSQL 확장 설치
```sql
-- Supabase SQL Editor에서 실행
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

#### 1.2 한글 검색 최적화 스키마 적용
```bash
# Supabase SQL Editor에서 docs/korean_search_optimization.sql 실행
```

#### 1.3 RPC 함수 설치
```bash
# Supabase SQL Editor에서 docs/supabase_rpc_functions.sql 실행
```

### 2단계: 백엔드 코드 업데이트

#### 2.1 의존성 확인
```bash
cd backend
pip install -r requirements.txt
```

#### 2.2 환경변수 설정
```bash
# .env 파일에 Supabase 키 설정
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 3단계: 테스트 실행

#### 3.1 한글 검색 테스트
```bash
cd backend
python test_korean_search.py
```

#### 3.2 서버 실행 및 테스트
```bash
# 백엔드 서버 실행
python run_server.py

# 프론트엔드에서 한글 검색 테스트
# "키토 불고기 레시피" 검색
```

## 🔍 검색 최적화 기능

### 1. 벡터 검색 (40% 가중치)
- OpenAI text-embedding-3-small 사용
- 의미적 유사도 검색
- 한글 완전 지원

### 2. Full-Text Search (30% 가중치)
- PostgreSQL 한국어 FTS
- 형태소 분석 기반 검색
- 정확한 키워드 매칭

### 3. Trigram 유사도 검색 (20% 가중치)
- pg_trgm 확장 사용
- 오타 허용 검색
- 부분 문자열 매칭

### 4. ILIKE 폴백 검색 (10% 가중치)
- 기존 ILIKE 검색
- 호환성 보장
- 안정성 확보

## 📊 성능 개선 효과

### 검색 정확도
- **기존**: 단순 키워드 매칭
- **개선**: 의미적 + 형태소 + 유사도 검색

### 검색 속도
- **인덱스 최적화**: GIN 인덱스 사용
- **쿼리 최적화**: RPC 함수 활용
- **캐싱**: Supabase 자동 캐싱

### 한글 지원
- **조사 처리**: 자동 조사 제거
- **형태소 분석**: PostgreSQL FTS
- **유사도 검색**: 오타 허용

## 🛠️ 문제 해결

### 1. RPC 함수 오류
```sql
-- Supabase에서 RPC 함수 권한 확인
GRANT EXECUTE ON FUNCTION hybrid_search_v2 TO anon;
GRANT EXECUTE ON FUNCTION vector_search TO anon;
GRANT EXECUTE ON FUNCTION trigram_search TO anon;
GRANT EXECUTE ON FUNCTION fts_search TO anon;
```

### 2. 인덱스 생성 오류
```sql
-- 인덱스 재생성
DROP INDEX IF EXISTS idx_recipes_title_fts;
CREATE INDEX idx_recipes_title_fts 
  ON recipes USING gin(to_tsvector('korean', search_title));
```

### 3. 검색 결과 없음
```sql
-- 검색용 컬럼 업데이트 확인
UPDATE recipes SET 
  search_content = COALESCE(title, '') || ' ' || 
                   COALESCE(array_to_string(tags, ' '), ''),
  search_title = COALESCE(title, '')
WHERE search_content IS NULL;
```

## 📈 모니터링

### 1. 검색 성능 모니터링
```sql
-- 검색 성능 통계 조회
SELECT * FROM search_performance_stats;

-- 검색 성능 테스트
SELECT * FROM test_search_performance();
```

### 2. 인덱스 사용률 확인
```sql
-- 인덱스 사용률 조회
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'recipes';
```

## 🎯 사용 예시

### 1. 기본 검색
```python
from app.tools.korean_search import korean_search_tool

# 한글 최적화 검색
results = await korean_search_tool.korean_hybrid_search("키토 불고기", k=5)
```

### 2. 기존 검색 도구 업데이트
```python
from app.tools.hybrid_search import hybrid_search_tool

# 자동으로 한글 최적화 검색 사용
results = await hybrid_search_tool.search("한식 키토 레시피", max_results=5)
```

### 3. 검색 타입별 테스트
```python
# 벡터 검색만
vector_results = await korean_search_tool._vector_search(query, embedding, 5)

# Full-Text Search만
fts_results = await korean_search_tool._full_text_search(query, 5)

# Trigram 검색만
trigram_results = await korean_search_tool._trigram_similarity_search(query, 5)
```

## ✅ 완료 체크리스트

- [ ] PostgreSQL 확장 설치 (pg_trgm)
- [ ] 한글 검색 최적화 스키마 적용
- [ ] RPC 함수 설치
- [ ] 백엔드 코드 업데이트
- [ ] 테스트 실행
- [ ] 성능 모니터링 설정
- [ ] 프론트엔드에서 검색 테스트

## 🎉 결과

한글 검색 성능이 크게 향상되어 더 정확하고 빠른 검색 결과를 제공합니다!

- **정확도**: 의미적 + 형태소 + 유사도 검색
- **속도**: 최적화된 인덱스 + RPC 함수
- **한글 지원**: 조사 처리 + 형태소 분석
- **안정성**: 다중 검색 방식 + 폴백 지원
