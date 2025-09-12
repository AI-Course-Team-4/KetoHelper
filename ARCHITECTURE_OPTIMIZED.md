# 🏗️ 최적화된 MVP 아키텍처 설계서

**문서 버전**: v1.0  
**작성일**: 2025-01-27  
**대상**: 1단계 MVP 구현  

---

## 🎯 **최적화 목표**

### **기존 문제점**
1. **복잡성 과다**: 1단계에 너무 많은 기능 (임베딩, 고급 풍부화)
2. **모듈 구조 불명확**: 크롤링-정규화-풍부화 경계 모호
3. **설정 관리 복잡**: 사이트별 YAML + 환경변수 분산
4. **에러 처리 중복**: 각 모듈마다 개별 에러 처리
5. **확장성 제한**: 새로운 사이트 추가 시 코드 수정 필요

### **최적화 원칙**
1. **단순함 우선**: 복잡한 기능은 Phase 2로 연기
2. **모듈 분리**: 크롤링 → 정규화 → 저장 파이프라인 명확 분리
3. **플러그인 구조**: 사이트별 파서를 플러그인으로 설계
4. **중앙 설정**: 모든 설정을 하나의 파일로 통합
5. **에러 처리 통합**: 공통 에러 처리 레이어

---

## 🏛️ **3-Layer Architecture**

```
┌─────────────────────────────────────────────────┐
│                 CLI Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │   Manual    │  │  Monitoring │  │   Config │ │
│  │   Input     │  │  Dashboard  │  │  Manager │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Business Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │   Crawler   │  │ Normalizer  │  │   Queue  │ │
│  │   Engine    │  │   Engine    │  │  Manager │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ Site Parser │  │  Validator  │  │   Error  │ │
│  │   Factory   │  │   Engine    │  │  Handler │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│               Data Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ PostgreSQL  │  │  Raw Data   │  │   Logs   │ │
│  │   Tables    │  │   Storage   │  │  Storage │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────────────────────────────────────┘
```

### **Layer 별 책임**

#### **CLI Layer**
- **Manual Input**: 사용자 입력 처리 (`python crawler.py --restaurant "강남 맛집"`)
- **Config Manager**: 설정 파일 로드 및 검증
- **Monitoring Dashboard**: 크롤링 상태 및 메트릭 표시

#### **Business Layer**
- **Crawler Engine**: 크롤링 작업 조정 및 흐름 제어
- **Site Parser Factory**: 사이트별 파서 생성 및 관리 (플러그인)
- **Normalizer Engine**: 크롤링 데이터 정규화 및 중복 제거
- **Validator Engine**: 데이터 품질 검증 및 필터링
- **Queue Manager**: 작업 큐 관리 및 우선순위 처리
- **Error Handler**: 통합 에러 처리 및 재시도 로직

#### **Data Layer**  
- **PostgreSQL Tables**: 정규화된 데이터 저장
- **Raw Data Storage**: 원본 크롤링 데이터 백업
- **Logs Storage**: 시스템 로그 및 메트릭

---

## 📁 **최적화된 디렉토리 구조**

```
craw_test3/
├── 📁 src/                          # 소스코드
│   ├── 📁 cli/                      # CLI 레이어
│   │   ├── __init__.py
│   │   ├── main.py                  # 메인 CLI 진입점
│   │   ├── commands.py              # CLI 명령어 처리
│   │   └── validators.py            # 입력 검증
│   │
│   ├── 📁 core/                     # 핵심 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── crawler_engine.py        # 크롤링 엔진
│   │   ├── normalizer.py            # 데이터 정규화
│   │   ├── validator.py             # 데이터 검증
│   │   ├── queue_manager.py         # 작업 큐 관리
│   │   └── error_handler.py         # 통합 에러 처리
│   │
│   ├── 📁 parsers/                  # 사이트별 파서 (플러그인)
│   │   ├── __init__.py
│   │   ├── base_parser.py           # 기본 파서 인터페이스
│   │   ├── siksin_parser.py         # 식신 파서
│   │   └── parser_factory.py       # 파서 팩토리
│   │
│   ├── 📁 models/                   # 데이터 모델
│   │   ├── __init__.py
│   │   ├── restaurant.py           # 식당 데이터 클래스
│   │   ├── menu.py                 # 메뉴 데이터 클래스
│   │   └── crawl_job.py            # 크롤링 작업 클래스
│   │
│   ├── 📁 database/                 # 데이터베이스 레이어
│   │   ├── __init__.py
│   │   ├── connection.py           # DB 연결 관리
│   │   ├── repository.py           # 데이터 접근 추상화
│   │   ├── migrations/             # DB 마이그레이션
│   │   │   └── v1_initial_schema.sql
│   │   └── queries.py              # SQL 쿼리 모음
│   │
│   └── 📁 utils/                    # 유틸리티
│       ├── __init__.py
│       ├── config_loader.py        # 설정 로더
│       ├── logger.py               # 로깅 설정
│       ├── http_client.py          # HTTP 클라이언트 (playwright)
│       └── text_utils.py           # 텍스트 처리 유틸
│
├── 📁 config/                       # 설정 파일
│   ├── settings.yaml               # 통합 설정 파일
│   ├── parsers/                    # 파서 설정
│   │   └── siksin.yaml            # 식신 파서 설정
│   └── database.yaml              # DB 스키마 정의
│
├── 📁 tests/                        # 테스트
│   ├── unit/                       # 단위 테스트
│   ├── integration/                # 통합 테스트
│   └── fixtures/                   # 테스트 데이터
│
├── 📁 logs/                         # 로그 파일
├── 📁 data/                         # 임시 데이터
│   ├── raw/                        # 원본 크롤링 데이터
│   └── processed/                  # 처리된 데이터
│
├── requirements.txt                # Python 패키지
├── .env.template                   # 환경변수 템플릿
├── crawler.py                      # 메인 실행 파일
└── setup.py                        # 패키지 설정
```

---

## 🔧 **핵심 컴포넌트 설계**

### **1. CLI Layer - 사용자 인터페이스**

#### **main.py - 메인 진입점**
```python
# 사용법
python crawler.py --restaurant "강남 맛집" --site siksin --max-results 10
```

#### **commands.py - 명령어 처리**
```python
class CrawlerCommands:
    def crawl_restaurant(self, name: str, sites: List[str]) -> CrawlResult
    def show_status(self) -> StatusReport
    def show_config(self) -> ConfigInfo
```

### **2. Business Layer - 핵심 로직**

#### **crawler_engine.py - 크롤링 조정**
```python
class CrawlerEngine:
    def __init__(self, config: Config, parser_factory: ParserFactory):
        self.config = config
        self.parser_factory = parser_factory
        self.normalizer = Normalizer()
        self.validator = Validator()
        self.error_handler = ErrorHandler()
    
    async def crawl_restaurant(self, name: str, sites: List[str]) -> CrawlResult:
        # 1. 사이트별 파서 생성
        # 2. 검색 → 목록 → 상세 크롤링
        # 3. 데이터 정규화 및 검증
        # 4. DB 저장
        # 5. 결과 반환
```

#### **parser_factory.py - 파서 팩토리**
```python
class ParserFactory:
    def create_parser(self, site: str) -> BaseParser:
        parser_map = {
            "siksin": SiksinParser,
            "diningcode": DiningcodeParser
        }
        return parser_map[site](self.config.get_parser_config(site))
```

#### **base_parser.py - 파서 인터페이스**
```python
class BaseParser(ABC):
    @abstractmethod
    async def search(self, keyword: str) -> List[Restaurant]:
        """식당 검색"""
        
    @abstractmethod  
    async def parse_detail(self, url: str) -> Restaurant:
        """상세 정보 크롤링"""
        
    @abstractmethod
    def validate_response(self, response: str) -> bool:
        """응답 검증 (차단 감지)"""
```

### **3. Data Layer - 데이터 관리**

#### **repository.py - 데이터 접근 추상화**
```python
class RestaurantRepository:
    async def find_duplicate(self, restaurant: Restaurant) -> Optional[Restaurant]
    async def save(self, restaurant: Restaurant) -> str
    async def update(self, restaurant: Restaurant) -> bool
    async def get_stats(self) -> CrawlStats
```

---

## ⚙️ **통합 설정 관리**

### **config/settings.yaml - 중앙 통합 설정**
```yaml
# 모든 설정을 하나의 파일로 통합
app:
  name: "Restaurant Crawler MVP"
  version: "1.0.0"

database:
  host: "localhost"
  name: "restaurant_crawler"
  
crawler:
  max_concurrent_tabs: 3
  rate_limits:
    siksin: 0.5
  retry:
    max_attempts: 3
    
validation:
  min_quality_score: 50
  
logging:
  level: "INFO"
  files:
    main: "logs/crawler.log"
```

### **config/parsers/siksin.yaml - 사이트별 설정**
```yaml
# 식신 파서 전용 설정 (플러그인)
site:
  name: "siksin"
  base_url: "https://www.siksin.com"
  
search:
  url_pattern: "https://www.siksin.com/search?query={keyword}"
  selectors:
    restaurant_list: ".restaurant-item"
    restaurant_name: ".restaurant-name"
```

---

## 🔄 **데이터 플로우**

### **크롤링 파이프라인**
```
사용자 입력 → CLI → Crawler Engine → Parser Factory → Site Parser
    ↓
Raw Data → Normalizer → Validator → Repository → Database
    ↓
로그/메트릭 → Error Handler → 재시도/알림
```

### **에러 처리 플로우**
```
에러 발생 → Error Handler → 에러 분류 → 재시도/백오프/알림
    ↓
HTTP 403/429 → 속도 제한 → QPS 감속 → 대기 후 재시도
    ↓
파싱 실패 → 대체 셀렉터 → 실패 시 스킵 → 로그 기록
```

---

## 📊 **MVP 기능 범위**

### **Phase 1 - 포함 기능 ✅**
1. **기본 크롤링**: 식신 1개 사이트
2. **수동 입력**: CLI 인터페이스
3. **데이터 정규화**: 중복 제거, 주소 정규화  
4. **기본 저장**: PostgreSQL (restaurants, menus 테이블)
5. **에러 처리**: 재시도, 백오프, 로깅
6. **모니터링**: 기본 메트릭 (성공률, 에러율)

### **Phase 1 - 제외 기능 ❌**
1. **고급 풍부화**: LLM, 검색 기반 증강
2. **임베딩**: 벡터 검색 (Phase 2로 연기)
3. **다중 사이트**: 다이닝코드, 망고플레이트
4. **웹 인터페이스**: CLI만 제공
5. **자동화**: 스케줄링, 배치 처리

---

## 🎯 **성공 지표 (MVP)**

### **기능적 목표**
- ✅ **크롤링 성공률**: ≥ 85%
- ✅ **데이터 품질**: 필수 필드 충족 ≥ 80%
- ✅ **처리 속도**: 식당 1곳당 평균 ≤ 10초
- ✅ **안정성**: 연속 실행 4시간 이상 가능

### **기술적 목표**  
- ✅ **모듈화**: 새 사이트 추가 시 파서만 개발
- ✅ **설정 관리**: YAML 설정으로 코드 수정 없이 조정
- ✅ **에러 복구**: 자동 재시도 및 백오프
- ✅ **로깅**: 상세한 디버깅 정보 제공

---

## 🚀 **구현 순서**

### **1주차: 기반 인프라**
1. ✅ 디렉토리 구조 생성
2. ✅ 설정 파일 작성 (settings.yaml, siksin.yaml)
3. ✅ 데이터베이스 스키마 구축
4. ✅ 기본 유틸리티 (config_loader, logger, http_client)

### **2주차: 핵심 엔진**
1. ✅ BaseParser 인터페이스 및 SiksinParser 구현
2. ✅ CrawlerEngine 및 파이프라인 구축
3. ✅ Normalizer 및 Validator 구현
4. ✅ Repository 및 DB 연동

### **3주차: 통합 및 테스트**
1. ✅ CLI 인터페이스 구현
2. ✅ 에러 처리 및 재시도 로직
3. ✅ 모니터링 및 로깅 시스템
4. ✅ 통합 테스트 및 버그 수정

---

## 📝 **다음 단계 (Phase 2)**

1. **다이닝코드 파서 추가** (새 파서 플러그인)
2. **기본 풍부화** (규칙 기반 카테고리 추출)
3. **검색 풍부화** (네이버 검색 기반)
4. **임베딩 시스템** (pgvector 연동)
5. **웹 인터페이스** (FastAPI + React)

이 아키텍처는 **단순하면서도 확장 가능한** 구조로 설계되어, MVP 구현 후 Phase 2 기능들을 무리없이 추가할 수 있습니다.