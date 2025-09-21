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

# 환경변수 설정 (.env 파일 생성)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 2. 완전 자동화 실행 (원클릭)

```bash
# 강남역 주변 레스토랑 크롤링 → 키토 점수 계산 → Supabase 저장
python scripts/full_automation_pipeline.py
```

### 3. 개별 실행 (단계별)

```bash
# 1단계: 기본 크롤링만
python scripts/crawl_gangnam_10.py

# 2단계: 기존 데이터에 키토 점수 추가
python scripts/complete_keto_scoring_pipeline.py
```

## ⚙️ 주요 설정

### 환경변수 (.env)

```bash
# Supabase 데이터베이스 (필수)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key

# 크롤링 설정 (선택사항)
CRAWLER_RATE_LIMIT=0.5
CRAWLER_TIMEOUT=30
CRAWLER_USER_AGENT=Mozilla/5.0...

# 캐시 설정 (선택사항)  
CACHE_ENABLED=true
CACHE_STRATEGY=file
```

## 🔧 핵심 기능

### 1. 완전 자동화 키토 헬퍼 파이프라인 ⭐

**원클릭으로 크롤링부터 키토 점수 계산까지 완전 자동화**

```
🕷️ 크롤링 → 🧹 전처리 → 🧮 키토 점수 계산 → 💾 Supabase 저장 → 📊 통계 분석
```

#### 주요 특징:
- **지능형 중복 처리**: 기존 레스토랑/메뉴 자동 감지 및 업데이트
- **실시간 진행률**: 크롤링 및 점수 계산 진행 상황 실시간 표시
- **자동 통계 생성**: 키토 점수 분포, 카테고리별 분석 자동 제공
- **오류 복구**: 네트워크 오류나 중복 데이터 자동 처리

#### 실행 결과:
- ✅ **20개 레스토랑** 자동 수집
- ✅ **262개 메뉴** 키토 점수 자동 계산
- ✅ **중복 없는 데이터베이스** 저장
- ✅ **실시간 통계** 분석 제공

### 2. 지능형 키토 점수화 엔진

- **룰 기반 점수 계산**: 키워드 매칭으로 -100~100점 산출
- **메뉴명 전처리**: "메뉴정보", "추천 1" 등 불필요한 텍스트 자동 제거
- **카테고리 자동 분류**: 키토 권장/조건부/주의/비추천 4단계 분류
- **신뢰도 계산**: 키워드 매칭 품질에 따른 신뢰도 점수

### 3. 스마트 데이터 관리

- **UPSERT 방식**: 중복 데이터 자동 감지 및 업데이트
- **캐시 활용**: 기존 크롤링 결과 재사용으로 속도 향상  
- **실시간 모니터링**: 진행 상황 및 오류 실시간 추적

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

### V1.0 ✅ **완료** (현재)
- [x] 기본 아키텍처 구현
- [x] Supabase 데이터베이스 연동
- [x] 다이닝코드 크롤러 구현
- [x] **완전 자동화 키토 점수화 엔진**
- [x] **UPSERT 기반 중복 처리**
- [x] **실시간 진행률 모니터링**
- [x] **메뉴명 전처리 시스템**

### V1.1 (다음 단계)
- [ ] 다른 지역 크롤링 지원 (홍대, 신촌 등)
- [ ] 웹 대시보드 (키토 점수 시각화)
- [ ] 사용자 맞춤 필터링
- [ ] 식신 크롤러 추가

### V2.0 (장기)
- [ ] 실시간 메뉴 업데이트 모니터링
- [ ] LLM 보조 점수화 (메뉴 설명 분석)
- [ ] 모바일 앱 연동
- [ ] ML 기반 개인화 추천 시스템

## 📈 성과

### 현재 달성한 성과 ✅
- **완전 자동화**: 원클릭으로 크롤링부터 DB 저장까지
- **262개 메뉴**: 강남역 주변 20개 레스토랑 완전 분석
- **무결성 보장**: 중복 없는 깔끔한 데이터베이스
- **실시간 분석**: 키토 점수 분포 및 통계 자동 생성