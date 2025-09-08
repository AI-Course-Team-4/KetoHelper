# 🍽️ 레스토랑 메뉴 벡터 검색 테스트 프로젝트

> **Phase 1: 데이터 준비 및 저장** 구현 완료  
> 벡터 검색, 키워드 검색, 하이브리드 검색 성능 비교를 위한 데이터베이스 구축

## 📋 프로젝트 개요

이 프로젝트는 50개 레스토랑의 메뉴 데이터를 활용하여 3가지 검색 방법의 성능을 비교 분석합니다:
- **벡터 검색**: OpenAI 임베딩을 사용한 의미적 유사도 검색
- **키워드 검색**: PostgreSQL Full-text search
- **하이브리드 검색**: 두 방법을 결합한 검색

## 🏗️ 기술 스택

- **데이터베이스**: Supabase + pgvector
- **AI/ML**: OpenAI Embeddings API (text-embedding-3-small)
- **언어**: Python 3.8+
- **주요 라이브러리**: supabase-py, openai, numpy, pandas

## 📁 프로젝트 구조

```
vector_searching_mockdata/
├── README.md                 # 이 파일
├── PRD.md                   # 프로젝트 요구사항 문서
├── requirements.txt         # Python 의존성
├── env_template.txt         # 환경변수 템플릿
├── setup_database.sql       # 데이터베이스 스키마
├── main.py                  # 메인 실행 스크립트
├── mock_restaurants_50.json # 원본 데이터
├── src/
│   ├── data_parser.py       # JSON 데이터 파싱 모듈
│   ├── embedding_generator.py # 임베딩 생성 모듈
│   └── database_manager.py  # 데이터베이스 관리 모듈
├── data/                    # 처리된 데이터 저장소
└── logs/                    # 로그 파일
```

## 🚀 빠른 시작 가이드

### 1. 환경 설정

```bash
# 1. 가상환경 활성화
conda activate miniproject

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp env_template.txt .env
# .env 파일을 열어서 실제 값으로 수정
```

### 2. .env 파일 설정

```bash
# OpenAI API 키
OPENAI_API_KEY=your_openai_api_key_here

# Supabase 설정
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# 기타 설정 (선택사항)
LOG_LEVEL=INFO
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
BATCH_SIZE=50
MAX_RETRIES=3
```

### 3. 데이터베이스 설정

Supabase 대시보드에서 SQL Editor를 열고 `setup_database.sql` 파일의 내용을 실행하세요.

### 4. 데이터 처리 실행

```bash
# 전체 프로세스 실행
python main.py

# 특정 JSON 파일 지정
python main.py --json-file your_data.json

# 디버그 모드
python main.py --log-level DEBUG

# 임베딩 생성 건너뛰기 (테스트용)
python main.py --skip-embeddings
```

## 📊 처리 단계별 설명

### Step 1: 데이터 파싱 및 전처리
- JSON 파일에서 레스토랑 메뉴 데이터 로드
- 텍스트 정리 및 정규화
- 벡터화를 위한 결합 텍스트 생성
- 데이터 유효성 검사

### Step 2: 임베딩 벡터 생성
- OpenAI API를 사용하여 텍스트를 1536차원 벡터로 변환
- 배치 처리로 효율적인 API 호출
- 오류 처리 및 재시도 로직
- 토큰 사용량 및 비용 추적

### Step 3: 데이터베이스 저장
- Supabase PostgreSQL + pgvector에 데이터 저장
- 벡터 검색 및 키워드 검색용 인덱스 생성
- 데이터 무결성 검사
- 통계 정보 수집

## 🔍 팀원용 검색 기능 구현 가이드

Phase 1이 완료되면 다음 SQL 함수들을 사용하여 검색 기능을 구현할 수 있습니다:

### 벡터 검색
```sql
-- 사용법: 먼저 검색어를 임베딩으로 변환한 후 호출
SELECT * FROM vector_search(
    query_embedding := '[0.1, 0.2, ...]'::vector,  -- 검색어 임베딩
    match_threshold := 0.7,                         -- 유사도 임계값
    match_count := 10                               -- 결과 개수
);
```

### 키워드 검색
```sql
-- 사용법: 한국어 키워드로 직접 검색
SELECT * FROM keyword_search(
    search_query := '마라탕 | 소고기',  -- 검색어 (OR 조건)
    match_count := 10                   -- 결과 개수
);
```

### 데이터베이스 통계 조회
```sql
-- 전체 통계
SELECT * FROM database_stats;

-- 레스토랑별 메뉴 수
SELECT * FROM restaurant_summary;
```

## 📈 성능 모니터링

### 로그 파일 확인
```bash
# 메인 로그
tail -f logs/main.log

# 각 모듈별 로그
tail -f logs/data_parser.log
tail -f logs/embedding_generator.log
tail -f logs/database_manager.log
```

### 생성된 데이터 파일
- `data/processed_restaurant_data.json`: 전처리된 데이터
- `data/restaurant_data_with_embeddings.json`: 임베딩 포함 데이터
- `data/summary_report.json`: 전체 처리 결과 요약

## 🛠️ 문제 해결

### 자주 발생하는 문제들

#### 1. OpenAI API 오류
```bash
# API 키 확인
echo $OPENAI_API_KEY

# 할당량 확인 (OpenAI 대시보드에서)
# Rate limit 오류 시 BATCH_SIZE 줄이기
```

#### 2. Supabase 연결 오류
```bash
# URL과 키 확인
echo $SUPABASE_URL
echo $SUPABASE_KEY

# pgvector 확장 확인 (Supabase SQL Editor에서)
SELECT * FROM pg_extension WHERE extname = 'vector';
```

#### 3. 메모리 부족
```bash
# 배치 크기 줄이기
export BATCH_SIZE=20

# 또는 명령행에서
python main.py --json-file smaller_dataset.json
```

### 로그 레벨 조정
```bash
# 더 자세한 로그
python main.py --log-level DEBUG

# 오류만 보기
python main.py --log-level ERROR
```

## 🔧 개발자용 추가 정보

### 개별 모듈 테스트
```bash
# 데이터 파서 테스트
cd src && python data_parser.py

# 임베딩 생성기 테스트
cd src && python embedding_generator.py

# 데이터베이스 매니저 테스트
cd src && python database_manager.py
```

### 커스텀 설정
각 모듈의 Config 클래스를 수정하여 세부 설정을 조정할 수 있습니다:
- `EmbeddingConfig`: 임베딩 생성 관련 설정
- `DatabaseConfig`: 데이터베이스 관련 설정

## 📞 지원 및 문의

- **이슈 리포팅**: GitHub Issues
- **문서**: PRD.md 참조
- **로그 분석**: logs/ 디렉토리 확인

## 🎯 다음 단계 (Phase 2-4)

1. **벡터 검색 구현**: 의미적 유사도 기반 검색
2. **키워드 검색 구현**: PostgreSQL Full-text search
3. **하이브리드 검색 구현**: 두 방법 결합
4. **성능 비교 분석**: 정량적/정성적 평가
5. **최적화**: 가중치 튜닝 및 속도 개선

---

**📝 참고**: 이 README는 Phase 1 구현을 기준으로 작성되었습니다. 추가 기능 구현 시 문서를 업데이트해주세요.
