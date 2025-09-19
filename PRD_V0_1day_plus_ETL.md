# PRD — 식당/메뉴 수집 V0 (1-Day MVP)

## 0) 배경
- 팀 구성: 비전공자 중심 5명, 5주 프로젝트
- 목표: **하루(8h) 안에 동작하는 “강남 골든셋 최소 수집 파이프라인” 완성**
- 범위 축소: **단일 소스(다이닝코드)**, 정적 URL 시드 20개, **식당/메뉴 기본 필드만** 수집 → Supabase Postgres 적재 → 간단한 품질 체크 리포트

---

## 1) 목적 & 범위

### 1.1 목적
- 강남 업무지구 식당/메뉴 데이터를 **합법적이고 안전하게 최소 범위로 수집**해, 이후 추천/점수화의 기초 데이터를 만든다.

### 1.2 범위 (V0)
- **소스**: 다이닝코드(강남역 키워드 기반 식당 상세 페이지 20개 URL 시드)
- **수집 대상**: 식당 기본정보 + 메뉴명/가격(있을 때)
- **정규화**: 주소/좌표 표준화(단일 지오코더), 중복 통합(캐노니컬 키)
- **제외**: 리뷰/이미지/임베딩/대시보드/다중 소스/고급 풍부화

### 1.3 결론(ETL 관점, 강남역)
- **V0 수집(폭)**: **다이닝코드**에서 강남역 키워드 기반으로 **폭넓게 업장 리스트 확보 → 골든셋 구축**  
  - 키워드 예: `강남역 맛집`, `강남역 식당`, 반경/카테고리 필터는 최소화(중복 포함 수집)  
- **V1 풍부화(깊이)**: **식신(특히 'HOT'/테마 리스트)**의 **설명·인기 메뉴·간단 소개**를 보조 소스로 흡수 → **요약 문구·태그 품질 향상**  
  - 병합 기준: 상호명+지오(geohash6±50m)+전화번호(있을 때)로 매칭 후 보조 필드만 merge
- **운영 메모**: V0는 "다이닝코드 단일 소스"로 실행하되, V1부터 위 **1차(다이닝코드) → 2차(식신)** 전략으로 확장한다.

---

## 2) 산출물(Deliverables)

1) **CSV + DB 테이블**  
   - `restaurants.csv`, `menus.csv` (UTF-8)  
   - Supabase Postgres의 `restaurants`, `menus`, `restaurant_sources` 3테이블에 적재

2) **간단 품질 리포트(콘솔/CSV)**  
   - 필수 필드 결측 수, 중복 통합 전/후 카운트, 지오코딩 성공률

3) **운영 스크립트 2개**  
   - `crawl_diningcode.py` (수집)  
   - `load_to_supabase.py` (적재/정규화/중복 통합)

---

## 3) 성공 기준(수용 기준, Acceptance)

- [데이터] 식당 **≥ 20개**, 메뉴 **≥ 80개** 적재
- [정합성] 주소 표준화 성공률 **≥ 90%** (나머지는 원문 주소만 유지)
- [중복] 캐노니컬 통합 후 **중복률 ≤ 2%**
- [성능] 전체 파이프라인(수집→적재→리포트)이 **30분 이내** 1회 완주
- [준수] 소스별 ToS/robots.txt 위반 없음(리뷰/이미지 수집 금지, QPS ≤ 0.5)

---

## 4) 비기능/준수(Compliance)

- **소스별 체크리스트**  
  - robots.txt 확인(수집 허용 경로만), QPS 0.3~0.5, 지수 백오프(429/5xx)  
  - **리뷰/이미지/사용자 생성 컨텐츠 수집 금지**, 상호/주소/메뉴/가격 등 사실 정보만
  - 페이지 저장 금지(원문 HTML 미보존), 메타데이터만 저장
  - 출처 필드(`source_name`, `source_url`) 필수 저장

- **서킷 브레이커(회로 차단기)**  
  - 5분 동안 429 비율 ≥ 30% → **해당 소스 즉시 정지 15분** → 재시도

---

## 5) 데이터 모델(최소)

### 5.1 restaurants
| 필드 | 타입 | 설명 |
|---|---|---|
| id | uuid (PK) | 생성형 UUID |
| name | text | 상호명 |
| phone | text null | 전화번호(있을 때) |
| addr_original | text | 원문 주소 |
| addr_norm | text null | 표준화 주소(지오코더 결과) |
| lat | numeric(9,6) null | 위도 |
| lng | numeric(9,6) null | 경도 |
| geohash6 | text null | 좌표→geohash(6) |
| created_at | timestamptz default now() |  |
| updated_at | timestamptz default now() | trigger로 갱신 |

### 5.2 menus
| 필드 | 타입 | 설명 |
|---|---|---|
| id | uuid (PK) |  |
| restaurant_id | uuid (FK→restaurants.id) |  |
| name | text | 메뉴명 |
| price | integer null | KRW, 숫자만 추출 |
| created_at | timestamptz |  |
| updated_at | timestamptz |  |

### 5.3 restaurant_sources (소스↔캐노니컬 매핑)
| 필드 | 타입 | 설명 |
|---|---|---|
| restaurant_id | uuid (FK) |  |
| source_name | text | 'diningcode' 고정 (V1부터 'siksin' 추가) |
| source_url | text | 원본 상세 URL (UNIQUE) |
| name_raw | text | 원문 상호명 |
| addr_raw | text | 원문 주소 |

**인덱스/제약**  
- `UNIQUE (source_url)` on `restaurant_sources`  
- **중복 통합 키(캐노니컬)**: `lower(name) + geohash6 ± 50m + (phone 있으면 추가)`  
  - 구현: 적재 시 임시 키 계산 → 기존 restaurants 탐색 → **존재 시 merge**, 없으면 insert

---

## 6) 파이프라인 흐름(V0)

```
다이닝코드 강남역 키워드 검색 → 시드 URL 20개
   ↓
[수집] httpx + selectolax (기본)   # JS 필요 시에만 playwright-python
   ↓
[정규화] 주소 텍스트 정리 → 단일 지오코더(카카오 or 네이버) 호출(최대 1회)
   ↓        └ 실패 시 addr_norm/좌표 null로 유지(로그만)
[중복 통합] 캐노니컬 키 비교/병합
   ↓
[적재] Supabase Postgres (upsert)
   ↓
[품질 리포트] 결측/중복/성공률 출력(CSV)
```

**도구 단일화 원칙**  
- 기본: **Python만**(httpx + selectolax)  
- 동적 렌더 필요 시에만 **playwright-python** 사용(동시 탭 2개 제한)

---

## 7) 주소/지오 정책

- 지오코더: **카카오** 우선(팀 키 보유 기준), 실패 시 재시도 없음(오늘은 1회만)  
- 저장 규칙:  
  - `addr_original` = 원문  
  - `addr_norm` = 지오코더 표준 주소(있을 때)  
  - `lat/lng` = 결과 좌표(있을 때)  
  - `geohash6` = 좌표 있을 때만 생성(없으면 null)
- **V1 전환 계획**: PostGIS(geometry, GIST)로 교체(이번 스코프 제외)

---

## 8) 메뉴 파싱 규칙(최소)

- 이름: 텍스트 트림/연속 공백 1칸으로 축소
- 가격: **숫자만** 남기고 KRW 정수형(없으면 null)
- 중복 메뉴: 동일 `restaurant_id + lower(name)`이면 1개만(최신으로 upsert)

---

## 9) 모니터링/로그(오늘 버전)

- 콘솔 로그 + `quality_report.csv` 생성  
  - 필드별 결측 카운트(restaurant name/addr, menu name/price)  
  - 지오 성공률(성공/실패 개수)  
  - 통합 전/후 레코드 수(중복률)

---

## 10) 운영 방법(런북)

1) `.env` 준비  
   ```
   SUPABASE_URL=...
   SUPABASE_ANON_KEY=...
   KAKAO_REST_API_KEY=...
   ```
2) `seed_urls.txt` (다이닝코드 상세 URL 20개, 한 줄 1개)  
3) 실행 순서  
   ```
   python crawl_diningcode.py --seed seed_urls.txt --out restaurants.csv menus.csv
   python load_to_supabase.py --restaurants restaurants.csv --menus menus.csv
   python report_quality.py --out quality_report.csv
   ```
4) QPS 기본 0.3(요청 간 3초 sleep), HTTP 에러는 3회 재시도(지수 백오프)  
5) 429 비율↑ 시 자동 정지 15분(서킷 브레이커)

---

## 11) 역할/담당(오늘 배치)

- FE 1명: **아무것도 안 함**(데이터만 받음)  
- BE 2명: `load_to_supabase.py`, 중복 통합 로직, FK/인덱스  
- DATA 2명: `crawl_diningcode.py`, 선택자 점검, 시드 URL 수집

---

## 12) 일정(1-Day Sprint)

- 0h~1h: 다이닝코드 강남역 키워드 검색으로 시드 URL 20개 수집 & 선택자 테스트(수동)  
- 1h~3h: `crawl_diningcode.py` 완성(httpx+selectolax)  
- 3h~5h: `load_to_supabase.py` 완성(정규화/지오/중복 통합)  
- 5h~6h: 리포트/CSV/에러 핸들링 정리  
- 6h~7h: 전체 리허설(빈 DB → 적재 → 리포트)  
- 7h~8h: 실패 케이스 보완 & 최종 산출물 제출

---

## 13) 리스크 & 폴백

- 동적 렌더 필요 페이지: **해당 URL 건너뛰기**(오늘은 playwright 미사용 가능)  
- 지오 실패: `addr_norm/lat/lng/geohash6` null 허용, 리포트로만 집계  
- 차단/429: 서킷 브레이커 발동 → 남은 URL은 다음 배치로 이월

---

## 14) 후속(V1 이후)

- **소스 확장**: 1차(다이닝코드-폭) + 2차(식신-HOT/테마-깊이) 정식 적용  
- PostGIS, 풍부화(카테고리/알레르겐), 임베딩/검색, 간단 대시보드

---

### 부록 A — 테이블 생성(DDL 스케치, 필요시)

> **주의:** 코드 배포가 아니라 참고용 스케치. 실제 실행은 팀 환경에 맞춰 조정.

```sql
create extension if not exists pgcrypto;

create table if not exists restaurants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  phone text,
  addr_original text not null,
  addr_norm text,
  lat numeric(9,6),
  lng numeric(9,6),
  geohash6 text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists menus (
  id uuid primary key default gen_random_uuid(),
  restaurant_id uuid references restaurants(id) on delete cascade,
  name text not null,
  price integer,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists restaurant_sources (
  restaurant_id uuid references restaurants(id) on delete cascade,
  source_name text not null,
  source_url text not null unique,
  name_raw text,
  addr_raw text
);
```
