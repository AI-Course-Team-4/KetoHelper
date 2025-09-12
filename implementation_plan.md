# 수동 입력 기반 크롤링 시스템 구현 계획

## 📋 구현 단계별 리스트

### **1단계: 개발 환경 설정**
- **conda 환경 활성화**: `agent_test` 환경 사용
- **의존성 설치**: 
  - playwright-fetch (크롤링)
  - psycopg2-binary (PostgreSQL 연결)
  - pgvector (벡터 검색)
  - python-dotenv (환경변수 관리)
  - requests, beautifulsoup4 (보조 파싱)

### **2단계: 데이터베이스 스키마 설계**
- **PostgreSQL + pgvector 설정**
- **핵심 테이블 생성**:
  - `restaurants` (식당 정보)
  - `menus` (메뉴 정보) 
  - `menu_enriched` (풍부화된 메뉴 정보)
  - `crawl_jobs` (크롤링 작업 관리)
  - `raw_snapshots` (원본 데이터 백업)
- **인덱스 및 제약조건 설정**

### **3단계: 크롤링 엔진 개발**
- **playwright-fetch 기반 크롤러 클래스**
- **사이트별 설정 파일** (`sources/siksin.yaml`, `sources/diningcode.yaml` 등)
- **URL 패턴 및 셀렉터 정의**
- **JavaScript 렌더링 대응**

### **4단계: 사이트별 파서 구현**
- **식신 (siksin.com) 파서**
- **다이닝코드 (diningcode.com) 파서**  
- **망고플레이트 (mangoplate.com) 파서**
- **공통 데이터 구조로 정규화**

### **5단계: 데이터 정규화 및 중복 제거**
- **식당명/주소 정규화**
- **좌표 검증 및 정규화**
- **중복 식당 탐지 및 병합 로직**
- **메뉴 데이터 정규화**

### **6단계: 데이터 풍부화 (Enrichment)**
- **메뉴 풍부화 로직 구현**:
  - `short_desc`: 120자 내 요약 생성
  - `main_ingredients`: 최대 5개 주요 재료 추출
  - `dietary_tags`: keto, low-carb, gluten-free 등 태그
  - `spice_level`: 매운 정도 (0-3)
  - `temperature`: hot/cold/room
  - `cooking_method`: grill, stew, stir-fry 등
  - `allergens`: 계란/우유/대두/갑각류 등
  - `serving_size`: 소/중/대 또는 g/ml
  - `meal_time`: breakfast/lunch/dinner/snack

- **인터넷 검색 기반 풍부화 (하이브리드 접근)**:
  - **기본 규칙 기반 풍부화**: 메뉴명 패턴 매칭으로 기본 정보 추출
  - **신뢰도 기반 검색 보완**: confidence < 0.6 또는 재료 < 3개 시 검색 실행
  - **네이버 블로그 검색**: playwright-fetch로 레시피/재료 정보 수집
  - **패턴 매칭 추출**: 정규식으로 재료 정보 자동 추출
  - **데이터 병합**: 기본 정보 + 검색 정보 통합
  - **소스 추적**: `menu_enriched.source ∈ {'raw', 'rule', 'search', 'hybrid'}`

- **검색 풍부화 세부 구현**:
  ```python
  # 검색 쿼리 생성
  queries = [
      f"{menu_name} 레시피",
      f"{menu_name} 재료", 
      f"{restaurant_name} {menu_name}" if restaurant_name else menu_name
  ]
  
  # 네이버 검색으로 재료 정보 보완
  search_url = f"https://search.naver.com/search.naver?query={query}"
  content = await playwright_fetch(search_url)
  ingredients = extract_ingredients_from_text(content)
  ```

- **고도화 옵션 (Phase 2)**:
  - **다중 검색 엔진**: 네이버 + 구글 + 유튜브 검색
  - **Google Custom Search API**: 더 안정적인 검색 결과
  - **LLM 기반 추출**: 정교한 정보 추출 및 분석
  - **캐싱 시스템**: 검색 결과 7일간 캐시로 성능 향상

### **7단계: 임베딩 시스템**
- **menu_search_text 생성**:
  ```python
  menu_search_text = menu_name + short_desc + main_ingredients + 
                    cooking_method + dietary_tags + spice/meal_time
  ```
- **pgvector 임베딩 저장**:
  - `menu_embeddings` 테이블 생성
  - HNSW 인덱스 설정
  - content_hash 기반 재임베딩 정책

### **8단계: 데이터 품질 검증**
- **필수 필드 완성도 체크**
- **데이터 타입 및 형식 검증**
- **이상치 탐지 및 처리**
- **품질 점수 기반 필터링** (≥70점만 저장)

### **9단계: 수동 입력 인터페이스**
- **CLI 인터페이스** (풍부화 포함)
  ```bash
  python crawler.py --restaurant "강남 맛집" --enrich --embed
  ```

### **10단계: 에러 처리 및 재시도 로직**
- **HTTP 에러 처리** (403, 429, 5xx)
- **파싱 에러 처리** (셀렉터 변경 대응)
- **지수 백오프 및 재시도**
- **대체 소스 조회 로직**
- **풍부화 실패 시 폴백 처리**
- **임베딩 실패 시 재시도**

### **11단계: 모니터링 및 로깅**
- **크롤링 성공/실패 로그**
- **데이터 품질 메트릭**
- **성능 모니터링**
- **에러 알림 시스템**
- **풍부화 성공률 모니터링**
- **임베딩 처리 시간 추적**
- **품질 점수 분포 모니터링**

## 🎯 구현 우선순위

### **Phase 1 (MVP)**
1. ✅ 개발 환경 설정
2. ✅ 데이터베이스 스키마
3. ✅ 기본 크롤링 엔진
4. ✅ 식신 파서 (1개 사이트)
5. ✅ **기본 풍부화** (short_desc, main_ingredients)
6. ✅ **인터넷 검색 풍부화** (네이버 블로그 검색)

### **Phase 2 (확장)**
7. ✅ 다이닝코드 파서 추가
8. ✅ 중복 제거 로직
9. ✅ **완전한 풍부화** (모든 필드)
10. ✅ **다중 검색 엔진** (구글, 유튜브 추가)
11. ✅ **임베딩 시스템**

### **Phase 3 (완성)**
12. ✅ 망고플레이트 파서
13. ✅ **Google API 연동** (Custom Search)
14. ✅ **LLM 기반 추출** (고급 풍부화)
15. ✅ **캐싱 시스템** (검색 결과 캐시)
16. ✅ **품질 검증 시스템**
17. ✅ 모니터링 시스템
18. ✅ 웹 인터페이스

## 🔧 핵심 구현 포인트

### **수동 입력 처리**
```python
# 사용자 입력 예시
restaurant_name = "강남 맛집"
search_sources = ["siksin", "diningcode"]  # 우선순위 순서
```

### **크롤링 플로우**
1. **검색**: 식당명으로 각 사이트 검색
2. **목록 파싱**: 검색 결과에서 매칭되는 식당 찾기
3. **상세 크롤링**: 매칭된 식당의 상세 정보 수집
4. **데이터 정규화**: 공통 스키마로 변환
5. **데이터 풍부화**: 추가 메타데이터 생성
6. **임베딩 생성**: 검색용 벡터 생성
7. **저장**: PostgreSQL에 저장

### **에러 처리 전략**
- **사이트별 QPS 제한**: 0.5~0.7 QPS
- **동시 탭 제한**: 최대 3개
- **백오프 전략**: 10초 → 5분 지수 백오프
- **대체 소스**: 실패 시 다른 사이트에서 재시도

## 📊 풍부화 구현 세부사항

### **풍부화 소스 추적**
```python
menu_enriched.source ∈ {'raw', 'rule', 'llm', 'embed'}
```

### **ID 매핑 테이블**
```python
menu_ingredients(menu_id, ingredient_id, source, confidence)
```

### **임베딩 대상**
- ✅ **포함**: menu_name, short_desc, main_ingredients, cooking_method, dietary_tags
- ❌ **제외**: raw 스냅샷, 리뷰 전문, 주소/전화/가격

## 📝 참고 문서
- PRD_v1.md: 전체 요구사항 및 스키마 정의
- crawling_flow.md: 크롤링 플로우 및 풍부화 가이드
- menu_enrichment_search_strategy.md: 인터넷 검색 기반 풍부화 상세 전략

---
**작성일**: 2025-01-27  
**버전**: v1.0  
**상태**: 구현 준비 완료
