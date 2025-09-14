# 만개의레시피 키토 크롤러

만개의레시피에서 "키토" 관련 레시피를 크롤링하여 Supabase에 저장하는 프로젝트입니다.

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 생성하고 Supabase 정보를 입력하세요:

```env
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
```

### 3. 데이터베이스 스키마 설정

Supabase 대시보드의 SQL 에디터에서 `database_setup.sql` 파일의 내용을 실행하세요.

## 사용법

### 전체 크롤링 실행

```bash
python main.py
```

### 테스트 크롤링 (3페이지만)

```python
from src.crawler import KetoCrawler

crawler = KetoCrawler()
result = await crawler.test_run(max_pages=3)
print(result)
```

## 프로젝트 구조

```
recipe_test/
├── src/
│   ├── __init__.py
│   ├── config.py          # 설정 파일
│   ├── crawler.py         # 메인 크롤러 클래스
│   ├── http_client.py     # Rate-limited HTTP 클라이언트
│   ├── parsers.py         # HTML 파서들
│   └── supabase_client.py # Supabase 연동 클라이언트
├── tests/
│   └── __init__.py
├── main.py               # 메인 실행 파일
├── requirements.txt      # 의존성 목록
├── database_setup.sql    # 데이터베이스 스키마
├── .env.example         # 환경변수 예시
└── README.md
```

## 기능

- **목록 크롤링**: 만개의레시피 검색 결과 페이지 순회
- **상세 파싱**: 레시피 상세 정보 추출 (제목, 재료, 조리순서, 태그 등)
- **중복 방지**: source_url 기반 UPSERT
- **Rate Limiting**: 1-2초 간격 + 랜덤 지연으로 서버 부하 방지
- **재시도 로직**: 실패 시 자동 재시도
- **증분 종료**: 연속 3페이지 새 URL 미발견 시 자동 종료
- **실행 이력**: 크롤링 과정 및 결과 기록

## 설정

`src/config.py`에서 크롤링 설정을 변경할 수 있습니다:

```python
CRAWL_CONFIG = {
    "base_url": "https://www.10000recipe.com",
    "search_query": "키토",
    "max_pages": 50,
    "consecutive_empty_pages": 3,
    "rate_limit_seconds": 2.0,
    "random_sleep_min": 0.5,
    "random_sleep_max": 2.0,
    "request_timeout": 10,
    "detail_timeout": 30,
}
```

## 수용 기준

- 최초 전체 실행에서 ≥200건 저장
- title/ingredients/steps/source_url ≥95% non-null
- 중복 0% (source_url unique)
- 실패율 ≤3% (재시도 후)

## 테스트

```bash
# 단위 테스트
python -m pytest tests/

# 통합 테스트 (2-3페이지)
python -c "
import asyncio
from src.crawler import KetoCrawler
crawler = KetoCrawler()
result = asyncio.run(crawler.test_run(3))
print(result)
"
```

## 컴플라이언스

- robots.txt 준수
- Rate limiting으로 서버 부하 최소화
- 원문 출처 URL 보존
- 야간 실행 권장