# 👥 팀원용 빠른 시작 가이드

> **Phase 1 완료!** 개선된 임베딩으로 벡터 검색 품질이 크게 향상되었습니다.

## 🎯 현재 상태

✅ **완료된 작업**
- 50개 레스토랑, 373개 메뉴 데이터 처리
- **개선된 임베딩**: 메뉴명 + 핵심 특징 + 핵심 재료 + 요리 종류 중심
- OpenAI 임베딩 생성 (1536차원, 100% 성공률)
- Supabase 데이터베이스 저장 완료
- 벡터 검색 시스템 구현 및 테스트 완료

## 🚀 빠른 시작 (5분 설정)

### 1️⃣ 프로젝트 클론 및 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd vector_searching_mockdata

# 가상환경 활성화
conda activate miniproject

# 의존성 설치
pip install -r requirements.txt
```

### 2️⃣ 환경변수 설정

```bash
# 환경변수 파일 생성
copy env_template.txt .env
```

`.env` 파일을 열어서 다음 값들을 입력하세요:

```bash
# OpenAI API 키 (개인 키 또는 팀 공용 키)
OPENAI_API_KEY=sk-your-key-here

# Supabase 설정 (팀 공용 데이터베이스)
SUPABASE_URL=https://vjkkrdscakvgzjybsrqp.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 기타 설정 (기본값 사용 권장)
LOG_LEVEL=INFO
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
BATCH_SIZE=50
MAX_RETRIES=3
```

### 3️⃣ 벡터 검색 테스트

```bash
# 벡터 검색 시스템 테스트
python search_menu.py
```

**테스트 검색어 예시:**
- `매운 음식` → 사천 가지볶음, 쭈꾸미 볶음 등
- `청양` → 청양이 들어간 모든 메뉴들
- `달달한 디저트` → 치즈케이크, 아이스크림 등

## 📊 데이터베이스 구조

### restaurants 테이블
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `id` | SERIAL | 기본키 |
| `restaurant_name` | VARCHAR(255) | 레스토랑 이름 |
| `menu_name` | VARCHAR(255) | 메뉴 이름 |
| `key_ingredients` | TEXT[] | 주요 재료 배열 |
| `short_description` | TEXT | 짧은 설명 |
| `combined_text` | TEXT | 검색용 결합 텍스트 |
| `embedding` | VECTOR(1536) | OpenAI 임베딩 벡터 |
| `search_vector` | tsvector | 키워드 검색용 |

### 사용 가능한 함수들

#### 1. 벡터 검색 함수
```sql
SELECT * FROM vector_search(
    query_embedding := '[0.1, 0.2, ...]'::vector(1536),  -- 검색어 임베딩
    match_threshold := 0.7,                               -- 유사도 임계값 (0.0-1.0)
    match_count := 10                                     -- 결과 개수
);
```

#### 2. 키워드 검색 함수
```sql
SELECT * FROM keyword_search(
    search_query := '마라탕 | 소고기',  -- 검색어 (OR: |, AND: &)
    match_count := 10                   -- 결과 개수
);
```

#### 3. 통계 조회
```sql
-- 전체 통계
SELECT * FROM database_stats;

-- 레스토랑별 메뉴 수
SELECT * FROM restaurant_summary;
```

## 🔍 개선된 임베딩 시스템

### ✨ **핵심 개선사항**

**기존 방식**: `"식당명 + 메뉴명 + 모든 재료 + 전체 설명"`
**개선된 방식**: `"메뉴명 + 핵심 특징 + 핵심 재료 + 요리 종류"`

#### 🎯 **개선 효과**
- ✅ **메뉴 중심 검색**: 식당명 노이즈 제거
- ✅ **핵심 특징 강화**: "매운", "겉바속촉" 등 맛 특징 부각  
- ✅ **불필요한 재료 필터링**: 소금, 물 등 기본 조미료 제외
- ✅ **요리 카테고리 자동 분류**: 중식, 일식, 구이, 볶음 등

### 🔍 벡터 검색 사용법

이미 구현된 벡터 검색 시스템을 사용하세요:

```bash
# 벡터 검색 실행
python search_menu.py

# 예시 검색어:
# "매운 음식" → 사천 가지볶음들이 상위권
# "청양" → 청양이 들어간 메뉴들 정확히 매칭
# "겉바속촉" → 바삭한 요리들 검색
```

## 🚀 구현할 검색 방법들

### 1️⃣ **키워드 검색** (구현 필요)

PostgreSQL의 Full-text Search를 활용한 키워드 기반 검색

```python
# search_keyword.py 구현 예시
from supabase import create_client

def keyword_search(query_text: str, limit: int = 10):
    result = supabase.rpc("keyword_search", {
        "search_query": query_text,
        "match_count": limit
    }).execute()
    return result.data
```

### 2️⃣ **하이브리드 검색** (구현 필요)

벡터 검색 + 키워드 검색을 결합한 RRF(Reciprocal Rank Fusion) 방식

```python
# search_hybrid.py 구현 예시  
def hybrid_search(query_text: str, vector_weight: float = 0.7):
    # 1. 벡터 검색 결과 가져오기
    # 2. 키워드 검색 결과 가져오기  
    # 3. RRF 점수로 결합하여 최종 순위 결정
    pass
```

## 📊 테스트 쿼리 세트

### 🎯 **검증된 검색어들** (벡터 검색 기준)

#### ✅ **잘 작동하는 검색어**
- `"청양"` → 청양이 들어간 메뉴들 정확히 매칭 (유사도 0.55+)
- `"매운 음식"` → 사천 가지볶음들 상위권 (유사도 0.32+)
- `"겉바속촉"` → 바삭한 요리들 검색

#### 🔧 **개선이 필요한 검색어**  
- `"달달한 디저트"` → 디저트 카테고리 인식 부족
- `"매운 한국 음식"` → 자연어 쿼리 처리 개선 필요

### 🧪 **성능 테스트 방법**

```python
# 간단한 테스트 스크립트
test_queries = ["청양", "매운 음식", "달달한 디저트", "바삭한 요리"]

for query in test_queries:
    print(f"\n🔍 테스트: {query}")
    # python search_menu.py에서 수동 테스트
```

## 🎯 팀원별 과제 분담

### 🚀 **Phase 2: 검색 방법 구현 및 비교**

#### **팀원 A**: 키워드 검색 구현
- PostgreSQL Full-text Search 활용
- 한국어 검색 최적화
- `keyword_search()` 함수 완성

#### **팀원 B**: 하이브리드 검색 구현  
- 벡터 + 키워드 검색 결합
- RRF(Reciprocal Rank Fusion) 알고리즘
- 가중치 최적화

#### **팀원 C**: 성능 비교 및 평가
- 3가지 검색 방법 성능 테스트
- 정확도, 응답시간, 사용성 평가
- 최종 권장사항 도출

#### **팀원 D**: 사용자 인터페이스 개선
- 검색 결과 시각화
- 사용자 피드백 수집
- UX 개선사항 제안

## 🛠️ 유용한 SQL 쿼리

```sql
-- 전체 데이터 수 확인
SELECT COUNT(*) FROM restaurants;

-- 임베딩 데이터 확인
SELECT COUNT(*) FROM restaurants WHERE embedding IS NOT NULL;

-- 레스토랑별 메뉴 수 TOP 10
SELECT restaurant_name, COUNT(*) as menu_count 
FROM restaurants 
GROUP BY restaurant_name 
ORDER BY menu_count DESC LIMIT 10;

-- 개선된 임베딩 텍스트 확인
SELECT restaurant_name, menu_name, combined_text
FROM restaurants LIMIT 5;
```

## 🔧 문제 해결

### 자주 발생하는 문제들

#### ❌ **검색 결과 없음**
- 유사도 임계값 조정: `0.1`로 설정 권장
- 검색어 변경: 구체적인 메뉴명 또는 특징 사용

#### ❌ **환경 설정 오류**
```bash
# conda 환경 활성화 확인
conda activate miniproject

# 환경변수 확인
echo $OPENAI_API_KEY
echo $SUPABASE_URL
```

#### ❌ **느린 검색 속도**
- OpenAI API 응답 시간 (1-2초)이 주 원인
- 임베딩 캐싱 구현 고려

## 🎯 성공 기준

### ✅ **완료된 기능**
- [x] **벡터 검색 구현 완료** - 개선된 임베딩으로 품질 향상
- [x] **데이터 처리 완료** - 373개 메뉴 데이터 저장
- [x] **검색 시스템 구축** - `search_menu.py`로 테스트 가능

### 🚧 **구현 필요한 기능**
- [ ] 키워드 검색 구현
- [ ] 하이브리드 검색 구현  
- [ ] 성능 비교 분석
- [ ] 최종 권장사항 도출

---

**🎉 개선된 벡터 검색이 성공적으로 작동 중입니다!**
