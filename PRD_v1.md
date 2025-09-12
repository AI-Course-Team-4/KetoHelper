# ETL — Extract(크롤링) PRD v1.1 (강남 시범수집)

**문서 버전**: v1.1  
**작성일**: 2025-09-12  
**작성 범위**: 식당/메뉴 원천수집 + 최소 풍부화(Transform 사전 정의)  
**대상 소스**: 1차 식신, 2차 다이닝코드, 보조: 망고플레이트 (소스 온보딩 절차는 §11)

---

## 1. 목적 & 범위
- 강남(업무지구 중심) 식당/메뉴 데이터를 **합법적·안전한 방식**으로 수집하여, 이후 점수화·추천 엔진에 필요한 **정형 필드**를 안정적으로 공급한다.
- 본 문서는 **크롤링/수집(Extract)** 에 초점을 둔다. 풍부화(Transform)와 적재(Load)는 인터페이스 및 산출물 형식만 정의한다.
- 범위 내: 목록/상세 페이지 수집, 필드 정규화 최소 요건, 오류/폴백, 운영·모니터링, 테스트 기준, 확장성 정책.
- 범위 외: 추천 알고리즘, 프런트엔드 UI, API 게이트웨이.

## 1.1 기술스택
- **크롤링 도구**: playwright-fetch (JavaScript 렌더링 지원, 안정적인 DOM 파싱)
- **개발 언어**: Python (데이터 처리 및 파이프라인 구축)
- **데이터베이스**: PostgreSQL + pgvector (벡터 검색 지원) + Supabase (관리형 DB 서비스)
- **임베딩 모델**: OpenAI text-embedding-3-small (1536차원, 메뉴 텍스트 벡터화)

## 2. 용어
- **원천(raw)**: 사이트에서 가져온 원본 JSON 스냅샷.
- **정규화(normalized)**: 스키마에 맞게 파싱·클린징 된 레코드.
- **풍부화(enriched)**: 설명·태그·알레르겐 등 추가 메타가 삽입된 상태(필드 정의는 §5.3).

## 3. 성공 지표 & DoD
- **필드 커버리지**: 강남 골든셋(§10) 기준 **핵심 필드 충족 ≥ 80%**(name, addr, geo, menu.name, price|range 중 ≥1, category, phone|url 중 ≥1).
- **정합성**: 주소/좌표 역정규화 일치율 **≥ 95%**. 중복(동일 상호+주소) **≤ 2%**.
- **성능**: 단일 수집 배치에서 **P95 페이지 파싱 시간 ≤ 2.5s**, 사이트별 **평균 QPS ≤ 0.7**(rate-limit 여유 포함), 동시 탭 **≤ 5**.
- **안전성**: 블록/429 발생 시 자동 감속/백오프 작동, 10분 내 정상화.
- **DoD**: 골든셋 50곳에 대해 정규화 레코드 생성 및 저장, 운영 대시보드에 성공/실패/결측률 표시, 백업 스냅샷 존재.

## 4. 수집 흐름 요약
1) **Seed 생성**(키워드·지도 타일·카테고리) → 2) **목록 페이지 큐업** → 3) **상세 페이지 파싱** → 4) **정규화** → 5) **풍부화 최소 필드 채움** → 6) **검증/중복 제거** → 7) **임베딩 생성**(OpenAI text-embedding-3-small) → 8) **저장 & 스냅샷 백업** → 9) **메트릭 기록**.

## 5. 데이터 스키마(핵심)
### 5.1 restaurants (정규화)
- `id` (PK, UUID)
- `name` (text, NOT NULL)
- `addr_road` (text)
- `addr_jibun` (text)
- `lat` (numeric(9,6), NOT NULL), `lng` (numeric(9,6), NOT NULL)
- `phone` (text)
- `category` (text)
- `homepage_url` (text)
- `source` (text, NOT NULL) — 예: siksin|diningcode|mangoplate
- `source_url` (text, NOT NULL)
- `created_at`, `updated_at` (timestamptz)
**제약/인덱스**: UNIQUE(`name`,`addr_road`) NULLS NOT DISTINCT; INDEX(`lat`,`lng`); UNIQUE(`source`,`source_url`).

### 5.2 menus (정규화)
- `id` (PK, UUID), `restaurant_id` (FK→restaurants.id, ON DELETE CASCADE)
- `menu_name` (text, NOT NULL)
- `price` (integer NULL) — 원 단위, 불명시 시 NULL
- `currency` (text DEFAULT 'KRW')
- `is_signature` (bool DEFAULT false)
- `created_at`, `updated_at` (timestamptz)
**제약**: UNIQUE(`restaurant_id`,`menu_name`).

### 5.3 menu_enriched (풍부화 최소 필드)
- `menu_id` (PK/FK→menus.id)
- `short_desc` (text) — 120자 내 요약
- `main_ingredients` (text[]) — 최대 5개
- `dietary_tags` (text[]) — 예: keto, low-carb, gluten-free
- `spice_level` (int CHECK 0..3)
- `temperature` (text CHECK IN('hot','cold','room'))
- `cooking_method` (text) — grill, stew, stir-fry 등
- `allergens` (text[]) — 계란/우유/대두/갑각류 등 표준 라벨
- `serving_size` (text) — 소|중|대 또는 g/ml
- `meal_time` (text CHECK IN('breakfast','lunch','dinner','snack'))

### 5.4 crawl_jobs
- `id` (PK), `site` (text), `job_type` (text CHECK IN('seed','list','detail'))
- `url` (text), `status` (text CHECK IN('queued','running','done','failed'))
- `attempts` (int DEFAULT 0), `priority` (int DEFAULT 0)
- `last_error_code` (text), `last_error_msg` (text)
- `created_at`, `updated_at` (timestamptz)
**인덱스**: INDEX(`site`,`status`), INDEX(`job_type`).

### 5.5 raw_snapshots
- `id` (PK), `entity_type` ('restaurant'|'menu'|'review'), `entity_id` (uuid)
- `source` (text), `source_url` (text), `fetched_at` (timestamptz)
- `payload` (jsonb) — 원본 HTML→파싱전/후 JSON 저장
**보존 정책**: §8.3 참조.

### 5.6 menu_embeddings (벡터 임베딩)
- `id` (PK), `menu_id` (FK→menus.id, ON DELETE CASCADE)
- `model_name` (text DEFAULT 'text-embedding-3-small')
- `model_version` (text), `dimension` (int DEFAULT 1536)
- `algorithm_version` (text DEFAULT 'RAG-v1.0')
- `embedding` (vector(1536)) — OpenAI text-embedding-3-small 벡터
- `content_hash` (text) — 원본 텍스트 해시 (재임베딩 감지용)
- `created_at`, `updated_at` (timestamptz)
**제약**: UNIQUE(`menu_id`, `model_name`, `algorithm_version`)
**인덱스**: HNSW 벡터 인덱스 (cosine similarity)

## 6. 수집 대상 & URL 패턴 예시(샘플)
> 실제 도메인별 세부 셀렉터/정규식은 운영 레포의 `sources/<site>.yaml`에 보관.
- **목록 URL(예시)**: `https://<site>/search?q={kw}&page={n}` 또는 `https://<site>/area/{code}?category={cat}`
- **상세 URL(예시)**: `https://<site>/restaurants/{id}`
- **핵심 셀렉터(예시)**: `name: h1.title`, `addr: .address .road`, `geo: <meta[name="geo.position"]>`, `menu_rows: table.menu > tr`.
- **차단 지표**: HTTP 403/429, reCAPTCHA 출현, 공란 페이로드 등 → §7 폴백 적용.

## 7. 에러 처리 & 폴백 정책
### 7.1 에러 코드(표준)
- `E_BLOCKED`(403/429): 차단/속도 제한 → 지수 백오프(초기 10s, 최대 5m), QPS 절반으로 하향.
- `E_PARSE`(200): 셀렉터 미스/DOM 변형 → 소스 리비전 태스크 생성, 재시도 ≤3.
- `E_TIMEOUT`(504/네트워크): 재시도 ≤3, 타임아웃 8s→12s로 증가.
- `E_MISSING`(필수필드 결측): 대체 셀렉터 사용 후 실패 시 레코드 스킵+결측 카운트.

### 7.2 재시도/폴백 순서
1) 동일 URL 재시도(최대 3회, 점증 백오프)  
2) **감속 모드** 진입(사이트별 QPS↓, 동시 탭 5→3)  
3) 동일 엔터티 **대체 소스** 조회(소스 우선순위: 식신→다코→망플)  
4) 실패 누적 ≥ 임계치 시 **알림**(§8.2) 및 작업 중단.

## 8. 운영 요구사항
### 8.1 성능·자원
- **병렬도**: 기본 동시 탭 3, 최대 5.  
- **QPS 상한(사이트별)**: 0.5~0.7 QPS(협의 없이 1.0 이상 금지).  
- **타임아웃**: 요청 8s(목록), 12s(상세).

### 8.2 모니터링 & 알림
- **대시보드 메트릭**: 성공/실패/결측률, P50/P95 파싱시간, 블록율(429), 큐 적체, 재시도 건수.
- **알림 임계값**:  
  - 5분 내 `429` **≥ 20%** 또는 `E_PARSE` **≥ 10%** → 슬랙 채널 알림.  
  - 큐 적체 시간 **P95 ≥ 10분** → 경고.  
  - 성공률 **< 85%**(최근 1h) → 경고.

### 8.3 백업/복구
- **스냅샷 보존**: `raw_snapshots.payload` 일 단위 증분 스냅샷(S3), 보존 30일.  
- **DB 백업**: 일 1회 전체 백업 + 시간단위 WAL(가능 시).  
- **복구 플레이북**: 최근 스냅샷 복원 → 정규화 재실행 → 중복/정합성 검사 → 승격.

## 9. 법적·윤리적 고려
- **robots.txt 및 각 사이트 약관 준수**. 자동화 요청 빈도는 §8.1 내에서만 운영.  
- **저작권**: 이미지·리뷰 텍스트는 저장하지 않거나, 저장 시 **링크/출처/크레딧**을 명시하고 모델 학습 등 2차 활용은 금지(별도 승인 시에만).  
- **개인정보**: 리뷰에서 PII(이메일, 전화, 실명) 탐지 시 저장 금지/마스킹. 보관기간 30일 제한(스냅샷), 목적 외 사용 금지.

## 10. 테스트 & 검증 기준
- **골든셋**: 강남 지역 **식당 50곳**(카테고리 다양화) — 팀 시트 관리. 본 PRD의 AC는 본 세트로 측정.
- **정확성 검증**: 표본 N=50에 대해 수기 대조(이름/주소/좌표/대표메뉴). 주소 역지오코딩 일치율 기록. 중복율 측정.
- **필드 커버리지**: 엔티티별 필수 필드 존재율 리포트(하루 1회). 결측 상위 5 필드 개선 액션.
- **성능 테스트**:  
  - 시나리오 A(정상): 동시 탭 3, 300페이지/배치 → 성공률 ≥ 90%, P95 ≤ 2.5s.  
  - 시나리오 B(차단): 429 유도 → 감속/백오프 동작, 10분 내 회복.  
  - 시나리오 C(파싱 변경): 셀렉터 1개 교란 → `E_PARSE` 경보 및 소스 리비전 태스크 생성 확인.

## 11. 확장성(지역/소스/갱신)
- **지역 확장**: 지역 코드 테이블 도입(`area_code`, `bounds`), 시드 생성기에서 다중 지역 큐업 지원.
- **새로운 소스 온보딩**: `sources/<site>.yaml` 작성(목록/상세 URL 패턴, 셀렉터, 필수 필드 매핑, 우선순위 `source_trust_rank`).
- **재수집 주기(TTL)**: 엔터티에 `last_checked_at`, `valid_until` 관리. 기본 TTL **14일**. 만료/변경 시 재수집 큐에 자동 적재.

## 12. 산출물
- 정규화 테이블(`restaurants`, `menus`, `menu_enriched`) + 원천 스냅샷(`raw_snapshots`) + 벡터 임베딩(`menu_embeddings`).
- 운영 대시보드(성공/실패/결측/지연 메트릭) + 알림 설정.
- 테스트 리포트(정확성/성능/결함 목록) 1회/일 자동 생성.
- 벡터 검색 API (메뉴 유사도 검색, 추천 엔진 연동용).


