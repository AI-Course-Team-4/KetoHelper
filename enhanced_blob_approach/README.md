# Enhanced Blob Approach

## 개요
더 풍부한 콘텐츠로 임베딩하여 검색 정확도를 향상시키는 방식입니다.

## 특징
- **제목, 설명, 태그, 재료, 요리 방법** 모두 포함
- **LLM을 통한 전처리 및 정규화**
- **마케팅 단어 제거 및 핵심 정보 추출**
- **구조화된 blob 콘텐츠 생성**

## 테이블 구조
```sql
CREATE TABLE recipes_enhanced_blob (
    id BIGSERIAL PRIMARY KEY,
    recipe_id TEXT UNIQUE,
    title TEXT,
    description TEXT,
    tags JSONB,
    ingredients JSONB,
    cooking_method TEXT,
    enhanced_blob TEXT,  -- 개선된 blob 콘텐츠
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);
```

## Enhanced Blob 형식
```
[요리 종류] [요리 방법] [음식 카테고리] [맛 프로필] [영양 특성]
제목: [정규화된 제목]
설명: [정규화된 설명]
주요 재료: [정규화된 재료 목록]
태그: [정규화된 태그]
```

## 사용 방법

### 1. 테이블 생성
```sql
-- Supabase Dashboard에서 실행
\i create_enhanced_table.sql
```

### 2. 데이터 처리
```python
from enhanced_blob_supabase import EnhancedBlobApproachSupabase

approach = EnhancedBlobApproachSupabase()
approach.load_recipes_from_supabase("recipes_keto_raw", limit=100)
```

### 3. 검색 테스트
```python
results = approach.search_similar_recipes("김밥", top_k=10)
for result in results:
    print(f"{result['title']} - {result['similarity']*100:.1f}%")
```

## 기대 효과
- **검색 정확도 향상**: 더 풍부한 콘텐츠로 임베딩
- **의미적 유사도 개선**: LLM 전처리로 핵심 정보 추출
- **키워드 검색 향상**: 구조화된 blob으로 full-text 검색 개선