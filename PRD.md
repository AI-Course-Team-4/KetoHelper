# 레스토랑 메뉴 벡터 검색 테스트 프로젝트 PRD

## 프로젝트 개요

### 목적
레스토랑 메뉴 데이터를 활용하여 벡터 검색, 키워드 검색, 하이브리드 검색의 성능을 비교 분석하고, 각 검색 방법의 유사도 정확성을 평가한다.

### 배경
- 50개 레스토랑의 메뉴 데이터 (restaurant_name, menu_name, key_ingredients, short_description)
- 음식 검색에서 사용자 의도를 가장 잘 파악하는 검색 방법론 탐구
- 실제 서비스에 적용 가능한 최적의 검색 전략 수립

## 데이터 구조 분석

### 입력 데이터 (mock_restaurants_50.json)
```json
{
  "restaurant_name": "청양불향관",
  "menus": [
    {
      "menu_name": "마라탕",
      "key_ingredients": ["소고기육수", "화자오", "청경채"],
      "short_description": "얼얼하고 칼칼한 국물."
    }
  ]
}
```
## 가상환경
conda activate miniproject 를 사용해서 가상환경 실행

### 벡터화 대상 텍스트
각 메뉴 아이템을 다음과 같이 결합하여 벡터화:
- `{restaurant_name} {menu_name} {key_ingredients} {short_description}`
- 예: "청양불향관 마라탕 소고기육수 화자오 청경채 얼얼하고 칼칼한 국물."ㅛ

## 기술 스택

### 데이터베이스
- **Supabase + pgvector**: 벡터 저장 및 유사도 검색
- **PostgreSQL**: 키워드 검색 (Full-text search)

### AI/ML
- **OpenAI Embeddings API**: 텍스트 벡터화 (text-embedding-3-small)
- **Cosine Similarity**: 벡터 유사도 계산

### 개발 환경
- **Python 3.8+**
- **주요 라이브러리**: 
  - `supabase-py`: Supabase 클라이언트
  - `openai`: OpenAI API
  - `numpy`: 벡터 연산
  - `pandas`: 데이터 처리
  - `python-dotenv`: 환경변수 관리

## 검색 방법론

### 1. 벡터 검색 (Vector Search)
- **원리**: OpenAI embeddings로 텍스트를 벡터화하여 코사인 유사도 계산
- **장점**: 의미적 유사성 파악, 동의어/유사어 처리 우수
- **구현**: pgvector의 `<->` 연산자 사용

### 2. 키워드 검색 (Keyword Search)
- **원리**: PostgreSQL의 Full-text search 기능 활용
- **장점**: 정확한 키워드 매칭, 빠른 검색 속도
- **구현**: `to_tsvector`, `to_tsquery` 함수 사용

### 3. 하이브리드 검색 (Hybrid Search)
- **원리**: 벡터 검색과 키워드 검색 결과를 가중평균으로 결합
- **가중치**: 벡터 검색 70%, 키워드 검색 30% (조정 가능)
- **구현**: RRF(Reciprocal Rank Fusion) 또는 가중 스코어링

## 데이터베이스 스키마

### restaurants 테이블
```sql
CREATE TABLE restaurants (
    id SERIAL PRIMARY KEY,
    restaurant_name VARCHAR(255) NOT NULL,
    menu_name VARCHAR(255) NOT NULL,
    key_ingredients TEXT[],
    short_description TEXT,
    combined_text TEXT, -- 벡터화용 결합 텍스트
    embedding VECTOR(1536), -- OpenAI embedding 차원
    search_vector tsvector, -- Full-text search용
    created_at TIMESTAMP DEFAULT NOW()
);

-- 벡터 검색 인덱스
CREATE INDEX ON restaurants USING ivfflat (embedding vector_cosine_ops);

-- 키워드 검색 인덱스  
CREATE INDEX ON restaurants USING gin(search_vector);
```

## 테스트 시나리오

### 테스트 쿼리 세트
1. **정확한 메뉴명**: "마라탕", "돈카츠"
2. **재료 기반**: "소고기", "새우", "치즈"
3. **맛/특징 기반**: "매운", "달콤한", "시원한"
4. **조리법**: "구이", "볶음", "국물"
5. **복합 쿼리**: "매운 국물 요리", "치즈가 들어간 음식"

### 평가 지표

#### 정량적 지표
- **정확도 (Precision)**: 검색 결과 중 관련성 있는 항목 비율
- **재현율 (Recall)**: 전체 관련 항목 중 검색된 항목 비율
- **F1-Score**: Precision과 Recall의 조화평균
- **응답 시간**: 각 검색 방법의 평균 응답 시간

#### 정성적 지표
- **의미적 정확성**: 사용자 의도와 검색 결과의 일치도
- **다양성**: 검색 결과의 다양성 (같은 레스토랑 집중도)
- **사용자 만족도**: 실제 사용 시나리오에서의 유용성

## 구현 계획

### Phase 1: 데이터 준비 및 저장
1. JSON 데이터 파싱 및 전처리
2. Supabase 데이터베이스 설정
3. OpenAI API로 벡터 생성
4. 데이터베이스에 저장

### Phase 2: 검색 기능 구현
1. 벡터 검색 함수 구현
2. 키워드 검색 함수 구현
3. 하이브리드 검색 함수 구현

### Phase 3: 테스트 및 평가
1. 테스트 쿼리 실행
2. 결과 수집 및 분석
3. 성능 비교 리포트 작성

### Phase 4: 최적화
1. 하이브리드 검색 가중치 튜닝
2. 검색 속도 최적화
3. 최종 권장사항 도출

## 예상 결과

### 벡터 검색
- **강점**: "매운 음식", "시원한 국물" 등 추상적 쿼리에 우수
- **약점**: 정확한 메뉴명 검색에서 키워드 검색 대비 부정확할 수 있음

### 키워드 검색
- **강점**: "마라탕", "돈카츠" 등 정확한 키워드에 우수
- **약점**: 동의어나 의미적 유사성 파악 한계

### 하이브리드 검색
- **예상**: 두 방법의 장점을 결합하여 전반적으로 가장 우수한 성능

## 성공 기준

1. **기능적 요구사항**: 3가지 검색 방법 모두 정상 작동
2. **성능 요구사항**: 평균 응답시간 < 500ms
3. **정확도 요구사항**: F1-Score > 0.7
4. **비교 분석**: 각 검색 방법의 장단점 명확히 도출

## 향후 확장 가능성

1. **실시간 추천**: 사용자 검색 패턴 기반 개인화
2. **다국어 지원**: 한국어 외 다른 언어 메뉴 지원
3. **이미지 검색**: 메뉴 이미지 기반 검색 기능
4. **필터링**: 가격, 위치, 영업시간 등 추가 필터
