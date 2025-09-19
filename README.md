# 식당/메뉴 수집 및 키토 점수화 시스템

재사용 가능한 크롤링 시스템과 키토 다이어트 메뉴 점수화를 지원하는 ETL 파이프라인입니다.

## 🏗️ 아키텍처

- **레이어드 아키텍처**: Presentation → Application → Service → Infrastructure
- **의존성 주입**: 모듈 간 느슨한 결합으로 테스트 및 확장성 확보
- **도메인 주도 설계**: 비즈니스 로직과 데이터 모델의 명확한 분리
- **Repository 패턴**: 데이터 접근 로직 추상화

## 📁 프로젝트 구조

```
final_ETL/
├── config/                     # 설정 관리
├── core/                       # 핵심 비즈니스 로직
│   ├── domain/                 # 도메인 모델
│   └── interfaces/             # 추상 인터페이스
├── services/                   # 서비스 레이어
│   ├── crawler/                # 크롤링 서비스
│   ├── processor/              # 데이터 처리
│   ├── scorer/                 # 키토 점수화
│   └── cache/                  # 캐시 관리
├── infrastructure/             # 인프라스트럭처
│   ├── database/               # 데이터베이스 접근
│   ├── external/               # 외부 API
│   └── storage/                # 파일 저장소
├── application/                # 애플리케이션 레이어
├── presentation/               # 프레젠테이션 레이어
├── data/                       # 데이터 저장소
└── scripts/                    # 운영 스크립트
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력
```

### 2. 데이터베이스 설정

```bash
# PostgreSQL 데이터베이스 생성 후
python scripts/setup_database.py
```

### 3. 기본 설정 파일 생성

```bash
# 키워드 사전 파일들 생성 (향후 구현)
mkdir -p data/config/keywords
mkdir -p data/config/rules
```

## ⚙️ 주요 설정

### 환경변수 (.env)

```bash
# 데이터베이스
DB_HOST=localhost
DB_PORT=5432
DB_NAME=restaurant_db
DB_USER=postgres
DB_PASSWORD=your_password

# 외부 API
KAKAO_REST_API_KEY=your_kakao_api_key

# 크롤링 설정
CRAWLER_RATE_LIMIT=0.5
CRAWLER_TIMEOUT=30

# 캐시 설정
CACHE_ENABLED=true
CACHE_STRATEGY=file
```

## 🔧 핵심 기능

### 1. 재사용 가능한 크롤링 시스템

- **스마트 캐싱**: 기존 데이터 확인 후 필요시에만 크롤링
- **지오코딩 캐시**: API 호출 비용 절약
- **플러그인 아키텍처**: 새로운 소스 쉽게 추가
- **에러 복구**: 서킷 브레이커 및 재시도 로직

### 2. 키토 점수화 엔진

- **룰 기반 점수 계산**: 키워드 매칭으로 0-100점 산출
- **예외/대체 감지**: "밥 제외", "곤약밥" 등 특수 케이스 처리
- **신뢰도 추정**: 데이터 품질에 따른 신뢰도 점수
- **검수 큐**: 경계 점수대 메뉴 자동 선별

### 3. 데이터 품질 관리

- **중복 제거**: 캐노니컬 키 기반 중복 통합
- **주소 표준화**: 지오코딩을 통한 좌표 생성
- **품질 리포트**: CSV 형태의 상세 분석 결과

## 📊 데이터 모델

### 주요 엔티티

- **Restaurant**: 식당 정보 (이름, 주소, 평점 등)
- **Menu**: 메뉴 정보 (이름, 가격, 카테고리 등)
- **KetoScore**: 키토 점수 (점수, 근거, 신뢰도 등)
- **MenuIngredient**: 메뉴-재료 관계 (추정 재료 포함)

### 지원 데이터 소스

- **다이닝코드**: 기본 크롤링 소스
- **식신**: 보조 풍부화 소스 (향후)
- **기타**: 플러그인으로 확장 가능

## 🛠️ 개발 가이드

### 의존성 주입 사용법

```python
from infrastructure.di_container import container

# 서비스 등록
container.register_singleton(DatabasePool, DatabasePool)
container.register_transient(CrawlerService, CrawlerService)

# 서비스 해결
db_pool = container.resolve(DatabasePool)
crawler = await container.resolve_async(CrawlerService)
```

### 새로운 크롤러 추가

```python
from services.crawler.base_crawler import BaseCrawler

class NewSiteCrawler(BaseCrawler):
    async def crawl_restaurant_detail(self, url: str):
        # 구현
        pass

# 팩토리에 등록
crawler_factory.register('newsite', NewSiteCrawler)
```

## 📈 모니터링

### 헬스 체크

```python
# 데이터베이스 상태 확인
health = await db_pool.health_check()

# 전체 시스템 상태
from utils.health_checker import HealthChecker
checker = HealthChecker(db_pool, cache_manager, external_apis)
status = await checker.check_health()
```

### 메트릭 수집

```python
from utils.metrics import MetricsCollector

collector = MetricsCollector()
collector.record_operation("crawl_restaurant", 2.5, True)
summary = collector.get_summary()
```

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# 커버리지 측정
pytest --cov=. tests/
```

## 📦 배포

### 개발 환경

```bash
python scripts/setup_database.py
python -m presentation.cli.main crawl --source diningcode
```

### 운영 환경

```bash
# 환경변수 설정
export ENVIRONMENT=production

# 마이그레이션 실행
python scripts/setup_database.py

# 서비스 시작
python -m presentation.cli.main
```

## 🤝 기여 방법

1. 코드 스타일: `black`, `isort`, `flake8` 준수
2. 타입 힌트: `mypy` 검증 통과
3. 테스트: 새 기능에 대한 테스트 코드 작성
4. 문서: 주요 변경사항 문서화

## 📄 라이선스

MIT License

## 🔮 로드맵

### V1.0 (현재)
- [x] 기본 아키텍처 구현
- [x] 데이터베이스 스키마 설계
- [x] 의존성 주입 시스템
- [ ] 다이닝코드 크롤러 구현
- [ ] 키토 점수화 엔진
- [ ] 기본 CLI 인터페이스

### V1.1 (다음 단계)
- [ ] 식신 크롤러 추가
- [ ] 웹 대시보드
- [ ] 실시간 모니터링
- [ ] LLM 보조 점수화

### V2.0 (장기)
- [ ] PostGIS 지원
- [ ] 마이크로서비스 분리
- [ ] 클라우드 네이티브 배포
- [ ] ML 기반 추천 시스템