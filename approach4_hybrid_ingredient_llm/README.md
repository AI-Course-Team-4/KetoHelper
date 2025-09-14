# Approach 4: 하이브리드 식재료 LLM 전처리

## 개요
방식2의 비용 효율성과 방식3의 LLM 전처리 능력을 결합한 하이브리드 접근법

## 핵심 아이디어
- **식재료 정보만** LLM으로 전처리하여 API 비용 절약
- **제목, 설명, 태그**는 기존 방식2의 안정적인 전처리 사용
- **구조화된 메타데이터**로 검색 품질 향상

## 구조 설계

### 1. 데이터 흐름
```
원본 레시피 데이터
    ↓
식재료 추출 → LLM 전처리 → 구조화된 메타데이터
    ↓
제목/설명/태그 → 방식2 전처리 → 기본 정보
    ↓
결합 → 최종 구조화된 blob → 임베딩 생성
```

### 2. LLM 전처리 범위
**LLM 처리 (비용 발생)**
- 식재료 분석 및 분류
- 요리 종류 추론
- 조리법 추론  
- 맛 특징 분석
- 영양 정보 추론

**기존 방식2 처리 (비용 없음)**
- 제목 정규화
- 설명 정리
- 태그 정규화
- 메타 정보 (분량, 조리시간, 난이도)

### 3. 예상 비용 절약
- **방식3**: 전체 정보 LLM 처리 → 100% API 비용
- **하이브리드**: 식재료만 LLM 처리 → **약 30-40% API 비용**

### 4. 예상 품질 향상
- **방식2**: 단순 텍스트 조합 → 제한적 검색
- **하이브리드**: 구조화된 메타데이터 → **향상된 검색 정확도**

## 구현 파일 구조
```
approach4_hybrid_ingredient_llm/
├── approach4_supabase.py           # 메인 구현
├── ingredient_normalizer.py        # 식재료 정규화
├── llm_ingredient_analyzer.py      # LLM 식재료 분석
├── hybrid_blob_generator.py        # 하이브리드 blob 생성
└── README.md                       # 이 파일
```

## 테이블 구조
```sql
CREATE TABLE recipes_hybrid_ingredient_llm (
    id BIGSERIAL PRIMARY KEY,
    recipe_id TEXT UNIQUE,
    title TEXT,
    raw_ingredients JSONB,           -- 원본 식재료
    normalized_ingredients JSONB,    -- 정규화된 식재료
    llm_metadata JSONB,              -- LLM 분석 결과
    basic_metadata JSONB,            -- 방식2 기본 정보
    structured_blob TEXT,            -- 최종 구조화된 blob
    embedding vector(1536),          -- OpenAI 임베딩
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);
```

## 성능 목표
- **검색 정확도**: 방식2 대비 20% 향상
- **API 비용**: 방식3 대비 60% 절약
- **처리 속도**: 방식3 대비 40% 향상
