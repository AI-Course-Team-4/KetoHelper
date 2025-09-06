# PRD — **벡터 검색 시스템 V0** (3h 구현용 + 확장성 고려)

**구성요소를 대폭 줄여** 지금 당장 동작하는 검색 흐름만 구현하되, **실제 크롤링 데이터로 확장 가능한 구조**를 설계합니다.

목표: "자유 질의(preference_text) → 벡터 검색 TopK 결과"가 뜨게 하기 + 향후 대용량 데이터 확장 준비.

## 0) 기술 스택 및 사전 준비

### 기술 스택
- **Backend**: Python 3.9+ + FastAPI
- **DB**: Supabase (PostgreSQL + pgvector)
- **임베딩**: OpenAI text-embedding-3-small
- **라이브러리**: supabase-py, openai, pandas, uvicorn

### 사전 준비사항 (별도 30분)
- [ ] Supabase 프로젝트 생성 및 pgvector extension 활성화
- [ ] OpenAI API 키 발급 및 환경변수 설정
- [ ] 샘플 CSV 데이터 준비 (30개 메뉴)
- [ ] Python 가상환경 설정
- [ ] **확장성 고려**: 향후 크롤링 데이터 구조 검토

## 1) 목표

- **V0**: 샘플 데이터 (30개 메뉴)를 CSV로 준비해 Supabase에 넣고
- **V1 확장**: 실제 크롤링 데이터 (수천~수만 개)로 확장 가능한 구조 설계
- OpenAI 임베딩으로 pgvector에 저장한 뒤
- 사용자의 자유 문장(`preference_text`)으로 **벡터 검색만** 수행해 Top5를 반환한다.

## 2) 범위(Scope)

### 포함

- DB: Supabase(PostgreSQL) + `pgvector`
- 임베딩 모델: OpenAI **`text-embedding-3-small`(1536차원)**
- 테이블: **`menus` 단일 테이블만 사용**
- 데이터 적재: CSV Import (**30개 샘플 메뉴로 제한**)
- 임베딩 적재: `menu_text` 임베딩 → `embedding(vector)` 저장
- 검색: **벡터 검색 단독**(코사인 기반)으로 Top5 반환
- 요청 파라미터: `preference_text`(자유 문장), `top_k`(기본 5)
- API 구현: FastAPI 기반 단일 엔드포인트

### 제외(이번 V0에서 아예 구현하지 않음)

- `raw_menus` 테이블/정식 ETL
- FTS 및 하이브리드 점수, 질의 확장 사전
- `short_desc` 생성/사용
- LLM 리랭커(Top30→Top5) 및 캐싱
- 거리/가중치/랭킹 고도화 전부

## 3) 데이터 모델 (확장 가능한 구조)

### 3.1) V0 구조 (단일 테이블)
- **`menus`**
    - `id` (uuid, PK)
    - `restaurant_name` (text, not null)
    - `address` (text, not null) 
    - `menu_name` (text, not null)
    - `price` (integer, NULL 허용)
    - `menu_text` (text) — 검색용 텍스트
    - `embedding` (vector(1536))
    - `created_at` (timestamptz, default now)
    - **확장 필드들**:
        - `source` (text) — 'manual', 'crawler_v1', 'crawler_v2' 등
        - `category` (text) — '한식', '양식', '중식' 등 (NULL 허용)
        - `rating` (decimal) — 평점 (NULL 허용, 향후 크롤링 시 사용)
        - `image_url` (text) — 메뉴 이미지 URL (NULL 허용)
        - `metadata` (jsonb) — 추가 정보 저장용

### 3.2) V1+ 확장 구조 (정규화된 테이블)
```sql
-- 향후 확장 시 고려할 구조
CREATE TABLE restaurants (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT,
    rating DECIMAL,
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE menus (
    id UUID PRIMARY KEY,
    restaurant_id UUID REFERENCES restaurants(id),
    name TEXT NOT NULL,
    price INTEGER,
    category TEXT,
    description TEXT,
    image_url TEXT,
    menu_text TEXT, -- 검색용
    embedding VECTOR(1536),
    source TEXT DEFAULT 'crawler',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.3) 인덱스 전략
- **V0**: 인덱스 없음 (30개 데이터)
- **V1 (100-1000개)**: 기본 인덱스만
    ```sql
    CREATE INDEX idx_menus_restaurant ON menus(restaurant_name);
    CREATE INDEX idx_menus_category ON menus(category);
    ```
- **V2 (1000+개)**: 벡터 인덱스 추가
    ```sql
    CREATE INDEX idx_menus_embedding ON menus 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);
    ```
        

## 4) 파이프라인 (V0 + 확장 계획)

### 4.1) V0 파이프라인 (3단계)

1. **CSV Import**
    - 컬럼: `restaurant_name,address,menu_name,price,category,source`
    - **확장 가능한 CSV 구조**:
    ```csv
    restaurant_name,address,menu_name,price,category,source,rating,image_url
    "김치찌개집","서울시 강남구 역삼동 123","김치찌개",8000,"한식","manual",,
    "김치찌개집","서울시 강남구 역삼동 123","된장찌개",7000,"한식","manual",,
    "파스타하우스","서울시 강남구 논현동 456","크림파스타",12000,"양식","manual",,
    "파스타하우스","서울시 강남구 논현동 456","토마토파스타",11000,"양식","manual",,
    "초밥집","서울시 강남구 신사동 789","연어초밥",,"일식","manual",,
    ```

2. **임베딩 적재**
    - `menu_text` 생성: `restaurant_name + ' ' + menu_name + ' ' + address + ' ' + category`
    - `text-embedding-3-small` 임베딩 → `embedding` 저장
    - **배치 처리**: 30개 → 한번에 처리

3. **검색(서빙)**
    - 입력 `preference_text`를 임베딩 → `embedding`과 **코사인 유사도**로 Top5 조회
    - 결과 반환: `{restaurant_name, menu_name, address, price, category, score}`

### 4.2) V1+ 확장 파이프라인

#### A) 크롤링 데이터 수집
```python
# 크롤링 모듈 구조 (향후 구현)
class RestaurantCrawler:
    def crawl_naver_place(self, area: str) -> List[Dict]
    def crawl_kakao_map(self, area: str) -> List[Dict]
    def crawl_delivery_apps(self, area: str) -> List[Dict]
```

#### B) ETL 파이프라인
1. **Extract**: 다양한 소스에서 데이터 수집
2. **Transform**: 
   - 데이터 정제 및 중복 제거
   - 카테고리 정규화
   - 주소 표준화
3. **Load**: 
   - 배치 임베딩 생성 (OpenAI API 효율적 사용)
   - 데이터베이스 적재

#### C) 성능 최적화
- **임베딩 캐싱**: 동일한 텍스트 재사용
- **배치 처리**: 대용량 데이터 청크 단위 처리
- **점진적 업데이트**: 신규/변경 데이터만 처리

## 5) API/입출력(텍스트 명세)

- **요청**:
    - `preference_text: string` (예: “칼칼하고 담백한 따뜻한 국물”)
    - `top_k?: number` (기본 5)
- **응답**:
    - `items: [{restaurant_name, menu_name, address, price, score}]`
    - `score` = 코사인 유사도 기반(참고용)

## 6) 성공 기준(DoD)

- `menus`에 데이터 적재 완료(가격 NULL 허용)
- `embedding not null` 비율 **≥ 95%**
- 임의 질의 3개(예: “매운”, “신선한”, “달달한”)에 대해 Top5 응답이 정상 반환
- 크래시/에러 없이 동작(간단 로그로 확인)

## 7) Supabase 설정 가이드

### 7.1) 프로젝트 생성 및 pgvector 활성화
```sql
-- 1. Supabase 대시보드에서 새 프로젝트 생성
-- 2. SQL Editor에서 pgvector extension 활성화
CREATE EXTENSION IF NOT EXISTS vector;
```

### 7.2) 테이블 생성 SQL (확장 가능한 구조)
```sql
-- V0 단일 테이블 구조 (확장 필드 포함)
CREATE TABLE menus (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    restaurant_name TEXT NOT NULL,
    address TEXT NOT NULL,
    menu_name TEXT NOT NULL,
    price INTEGER,
    menu_text TEXT,
    embedding vector(1536),
    -- 확장 필드들
    source TEXT DEFAULT 'manual', -- 'manual', 'crawler_v1', 'naver', 'kakao' 등
    category TEXT, -- '한식', '양식', '중식', '일식' 등
    rating DECIMAL(2,1), -- 평점 (1.0-5.0)
    image_url TEXT, -- 메뉴 이미지 URL
    metadata JSONB, -- 추가 정보 (영업시간, 전화번호 등)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 기본 인덱스
CREATE UNIQUE INDEX IF NOT EXISTS idx_menus_unique 
ON menus (restaurant_name, address, menu_name);

CREATE INDEX IF NOT EXISTS idx_menus_source ON menus (source);
CREATE INDEX IF NOT EXISTS idx_menus_category ON menus (category);

-- 향후 대용량 데이터용 벡터 인덱스 (V1+에서 생성)
-- CREATE INDEX idx_menus_embedding ON menus 
-- USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);
```

### 7.3) 환경변수 설정
```bash
# .env 파일
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
```

### 7.4) 필요한 의존성
```bash
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
supabase==2.1.0
openai==1.3.0
pandas==2.1.0
python-dotenv==1.0.0
numpy==1.24.0
```

## 8) 구현 시간 계획 (총 3시간)

| 단계 | 작업 내용 | 예상 시간 | 누적 시간 |
|------|-----------|-----------|-----------|
| **환경 설정** | FastAPI 프로젝트 생성, 의존성 설치 | 15분 | 15분 |
| **DB 연동** | Supabase 연결, 테이블 확인 | 20분 | 35분 |
| **CSV 처리** | pandas로 CSV 읽기, 데이터 검증 | 20분 | 55분 |
| **데이터 적재** | Supabase에 메뉴 데이터 insert | 15분 | 70분 |
| **임베딩 생성** | OpenAI API 호출, 배치 처리 | 40분 | 110분 |
| **검색 API** | 벡터 검색 로직, FastAPI 엔드포인트 | 35분 | 145분 |
| **테스트** | 3개 질의 테스트, 기본 검증 | 25분 | 170분 |
| **디버깅 버퍼** | 예상치 못한 이슈 해결 | 10분 | **180분** |

### 위험 요소 및 대응
- **OpenAI API 지연**: 임베딩을 배치로 처리하여 호출 횟수 최소화
- **Supabase 연결 이슈**: 연결 테스트를 먼저 수행
- **데이터 품질**: 샘플 데이터를 미리 검증된 것으로 준비

## 9) 확장 로드맵

### 9.1) 단계별 확장 계획

| 버전 | 데이터 규모 | 주요 기능 | 예상 기간 |
|------|-------------|-----------|-----------|
| **V0** | 30개 메뉴 | 벡터 검색 기본 구현 | 3시간 |
| **V1** | 100-500개 | 크롤링 데이터 연동, 카테고리 필터 | 1-2일 |
| **V2** | 1000-5000개 | 벡터 인덱스, 하이브리드 검색 | 3-5일 |
| **V3** | 10000+개 | 캐싱, 성능 최적화, 실시간 업데이트 | 1-2주 |

### 9.2) 성능 최적화 전략

#### A) 데이터 규모별 대응
```python
# 성능 임계점 기준
if menu_count < 100:
    # 벡터 인덱스 없이 브루트 포스
    use_vector_index = False
elif menu_count < 1000:
    # 기본 인덱스만
    create_basic_indexes()
else:
    # 벡터 인덱스 + 최적화
    create_vector_index()
    enable_caching()
```

#### B) 임베딩 생성 최적화
- **배치 처리**: OpenAI API를 배치로 호출 (비용 절약)
- **캐싱**: 동일한 텍스트의 임베딩 재사용
- **점진적 업데이트**: 변경된 데이터만 재처리

#### C) 검색 성능 최적화
- **결과 캐싱**: 인기 검색어 결과 캐시
- **지역 기반 필터링**: 위치 정보로 사전 필터링
- **카테고리 기반 검색**: 벡터 검색 전 카테고리로 후보 축소

### 9.3) 크롤링 데이터 통합 계획

#### A) 데이터 소스 확장
1. **네이버 플레이스**: 식당 기본 정보 + 메뉴
2. **카카오맵**: 위치 정보 + 리뷰
3. **배달앱**: 메뉴 상세 정보 + 가격
4. **공공데이터**: 위생 등급, 영업 허가 정보

#### B) 데이터 품질 관리
```python
class DataQualityManager:
    def validate_restaurant_data(self, data: Dict) -> bool
    def deduplicate_menus(self, menus: List[Dict]) -> List[Dict]
    def normalize_categories(self, category: str) -> str
    def standardize_addresses(self, address: str) -> str
```

## 10) 리스크 & 대응

### 10.1) V0 단계 리스크
- **한국어 검색 품질**: 벡터 단독 → V2에서 하이브리드 검색으로 개선
- **성능**: 30개 데이터로 충분 → V1+에서 인덱스 전략 적용
- **비용**: OpenAI API 호출 최소화 → 배치 처리로 최적화

### 10.2) 확장 단계 리스크
- **크롤링 법적 이슈**: robots.txt 준수, API 사용 권장
- **데이터 중복**: 소스별 중복 데이터 → 고유키 기반 중복 제거
- **임베딩 비용**: 대용량 데이터 → 캐싱 및 점진적 업데이트로 절약
- **검색 성능**: 응답 지연 → 인덱스 및 캐싱 전략으로 해결

### 10.3) 기술적 대응 방안
- **모니터링**: 검색 성능, API 사용량 추적
- **알림**: 임베딩 실패, DB 연결 오류 알림
- **백업**: 정기적 데이터 백업 및 복구 계획
- **스케일링**: 수평적 확장 가능한 아키텍처 설계