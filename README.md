# 🍽️ 식당 크롤링 시스템

> 수동 입력을 통한 식당 정보 수집 및 관리 시스템

## 📋 개요

이 시스템은 사용자가 **식당 이름을 직접 입력**하면, 해당 식당 정보를 식신(Siksin) 등의 사이트에서 자동으로 수집하여 **Supabase 데이터베이스**에 저장하는 크롤링 시스템입니다.

### ✨ 주요 기능

- 🔍 **수동 검색**: 식당 이름으로 검색하여 정보 수집
- 🏪 **상세 정보**: 주소, 전화번호, 평점, 운영시간 등 수집  
- 🍜 **메뉴 정보**: 메뉴명, 가격, 대표 메뉴 여부 등 수집
- 🔄 **중복 제거**: 지능적인 중복 식당 감지 및 정보 병합
- ⚡ **품질 관리**: 데이터 품질 점수 자동 계산 (0-100점)
- 🛡️ **안전 크롤링**: 속도 제한으로 사이트 차단 방지
- 📊 **진행 추적**: 실시간 크롤링 상태 및 통계 확인

## 🏗️ 시스템 구조

```
craw_test3/
├── 📁 config/           # 설정 파일
│   ├── settings.yaml    # 메인 설정
│   └── parsers/         # 사이트별 파서 설정
│       └── siksin.yaml  # 식신 파서 설정
├── 📁 src/
│   ├── 📁 core/         # 크롤링 엔진
│   │   ├── crawler_engine.py   # 메인 크롤링 엔진
│   │   ├── queue_manager.py    # 작업 큐 관리
│   │   └── pipeline.py         # 데이터 처리 파이프라인
│   ├── 📁 database/     # 데이터베이스 계층
│   │   ├── connection.py       # Supabase 연결
│   │   ├── repository.py       # Repository 패턴
│   │   └── queries.py          # SQL 쿼리
│   ├── 📁 models/       # 데이터 모델
│   │   ├── restaurant.py       # 식당 모델
│   │   ├── menu.py            # 메뉴 모델
│   │   └── crawl_job.py       # 크롤링 작업 모델
│   ├── 📁 parsers/      # 사이트별 파서
│   │   ├── base_parser.py     # 기본 파서 인터페이스
│   │   ├── siksin_parser.py   # 식신 파서
│   │   └── parser_factory.py  # 파서 팩토리
│   └── 📁 utils/        # 유틸리티
│       ├── config_loader.py   # 설정 로더
│       ├── logger.py          # 로깅
│       ├── http_client.py     # HTTP 클라이언트
│       └── text_utils.py      # 텍스트 처리
└── 📁 database/
    └── migrations/      # 데이터베이스 스키마
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.template .env
# .env 파일에서 Supabase 정보 입력
```

### 2. Supabase 설정

1. [Supabase](https://supabase.com)에서 프로젝트 생성
2. `database/migrations/v1_initial_schema.sql` 실행하여 테이블 생성
3. `.env` 파일에 연결 정보 입력:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here
```

### 3. 크롤링 실행

```python
import asyncio
from src.core import crawl_restaurant

async def main():
    # 식당 이름으로 크롤링
    result = await crawl_restaurant("강남 맛집")
    
    print(f"✅ 수집 완료!")
    print(f"   식당 수: {result.restaurant_count}")
    print(f"   메뉴 수: {result.menu_count}")
    print(f"   중복 제거: {result.duplicate_count}")
    print(f"   처리 시간: {result.processing_time:.2f}초")

asyncio.run(main())
```

## 🔧 설정

### 크롤링 설정 (`config/settings.yaml`)

```yaml
# 크롤링 속도 제한
crawling:
  rate_limits:
    siksin: 0.5    # 0.5초 간격
  
  retry:
    max_attempts: 3
    backoff_factor: 2.0

# 데이터 품질 임계값  
validation:
  quality_threshold: 30
  geo_bounds:        # 대한민국 좌표 범위
    lat_min: 33.0
    lat_max: 38.6
    lng_min: 125.0
    lng_max: 131.9
```

### 사이트별 파서 설정 (`config/parsers/siksin.yaml`)

```yaml
site:
  name: "식신"
  base_url: "https://www.siksin.com"

search:
  url_pattern: "{base_url}/search?query={keyword}&page={page}"
  selectors:
    restaurant_list: ".restaurant-item"
    restaurant_name: ".restaurant-name"
    restaurant_address: ".address"
```

## 📊 데이터베이스 스키마

### 식당 테이블 (restaurants)
- `id` (UUID): 고유 식별자
- `name` (VARCHAR): 식당명  
- `address_road` (VARCHAR): 도로명 주소
- `lat`, `lng` (FLOAT): 위도, 경도
- `phone` (VARCHAR): 전화번호
- `rating` (FLOAT): 평점 (0-5)
- `quality_score` (INTEGER): 데이터 품질 점수 (0-100)

### 메뉴 테이블 (menus)
- `id` (UUID): 고유 식별자
- `restaurant_id` (UUID): 소속 식당 ID
- `name` (VARCHAR): 메뉴명
- `price` (INTEGER): 가격 (원)
- `is_signature` (BOOLEAN): 대표 메뉴 여부

### 크롤링 작업 테이블 (crawl_jobs)
- `id` (UUID): 작업 ID
- `job_type` (ENUM): 작업 유형
- `status` (ENUM): 상태 (대기중/실행중/완료/실패)
- `keyword` (VARCHAR): 검색 키워드
- `progress_message` (VARCHAR): 진행 메시지

## 🛠️ 주요 컴포넌트

### CrawlerEngine
메인 크롤링 엔진으로 전체 프로세스를 조율합니다.

```python
from src.core.crawler_engine import CrawlerEngine

engine = CrawlerEngine()
await engine.initialize()

# 식당 이름으로 크롤링
result = await engine.crawl_restaurant_by_name("맛집 이름")
```

### QueueManager  
우선순위 기반 작업 스케줄링과 속도 제한을 담당합니다.

```python
from src.core.queue_manager import QueueManager, TaskPriority

manager = QueueManager()
await manager.start()

# 작업 추가
task_id = manager.add_restaurant_search_task(
    "강남 맛집", 
    priority=TaskPriority.HIGH
)
```

### DataPipeline
수집된 데이터의 검증, 정규화, 중복 제거를 수행합니다.

```python
from src.core.pipeline import DataPipeline

pipeline = DataPipeline()
result = await pipeline.process(raw_data)
```

## 📈 품질 관리

시스템은 수집된 데이터의 품질을 자동으로 평가합니다:

**품질 점수 계산 (100점 만점)**
- 필수 정보 (40점): 이름(20) + 주소(10) + 전화번호(10)
- 위치 정보 (20점): 좌표 정보 
- 평가 정보 (20점): 평점(10) + 리뷰수(10)
- 메뉴 정보 (20점): 메뉴 개수(15) + 가격 정보(5)

## 🔍 모니터링

### 크롤링 통계 확인
```python
# 엔진 통계
stats = engine.get_stats()
print(f"성공한 작업: {stats['successful_jobs']}")
print(f"수집된 식당: {stats['restaurants_crawled']}")

# 큐 상태 확인  
queue_status = manager.get_queue_status()
print(f"대기 중인 작업: {queue_status['queue_size']}")
```

### 로그 확인
```bash
# 실시간 로그 확인
tail -f logs/crawler.log

# 에러 로그만 확인
grep "ERROR" logs/crawler.log
```

## 🚦 사용 제한사항

- **속도 제한**: 사이트별 0.5-1초 간격으로 요청
- **재시도**: 실패 시 최대 3회 재시도 (지수 백오프)
- **차단 감지**: 차단 시 자동 중단 및 알림
- **품질 필터**: 품질 점수 30점 미만 데이터 경고

## 🔧 확장 가능성

새로운 사이트 추가는 `BaseParser`를 상속하여 구현:

```python
from src.parsers.base_parser import BaseParser

class NewSiteParser(BaseParser):
    async def search(self, keyword: str) -> SearchResult:
        # 검색 로직 구현
        pass
    
    async def parse_restaurant_detail(self, url: str) -> ParseResult:
        # 상세 정보 파싱 로직 구현  
        pass
```

## 🐛 트러블슈팅

### 자주 발생하는 문제

1. **Supabase 연결 오류**
   ```bash
   # 연결 정보 확인
   python -c "from src.database import get_database; print('연결 성공')"
   ```

2. **크롤링 차단**
   ```yaml
   # config/settings.yaml에서 간격 늘리기
   crawling:
     rate_limits:
       siksin: 1.0  # 1초로 증가
   ```

3. **메모리 부족**
   ```python
   # 배치 크기 줄이기
   engine = CrawlerEngine()
   engine.batch_size = 10  # 기본값: 20
   ```

## 📝 라이센스

MIT License - 자유롭게 사용, 수정, 배포 가능합니다.

---

## 🎯 다음 단계

이 시스템은 현재 **수동 식당 검색** 기능이 완성되었습니다. 
향후 추가 가능한 기능:

- 🤖 **자동화**: 스케줄링 기반 정기 크롤링
- 🌐 **다중 사이트**: 다이닝코드, 망고플레이트 등 추가  
- 📱 **웹 인터페이스**: 크롤링 관리 대시보드
- 📊 **분석**: 식당 트렌드 및 평점 분석
- 🔔 **알림**: 새로운 맛집 발견 시 알림

**현재 상태**: ✅ 수동 크롤링 완전 구현 완료