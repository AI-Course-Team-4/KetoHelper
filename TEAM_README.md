# 👥 팀원용 빠른 시작 가이드

> **Phase 1 완료!** 이제 벡터 검색, 키워드 검색, 하이브리드 검색을 구현할 차례입니다.

## 🎯 현재 상태

✅ **완료된 작업**
- 50개 레스토랑, 373개 메뉴 데이터 처리
- OpenAI 임베딩 생성 (1536차원, 100% 성공률)
- Supabase 데이터베이스 저장 완료
- 검색용 함수 및 인덱스 준비 완료

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

### 3️⃣ 연결 테스트

```bash
# 데이터베이스 연결 테스트
python -c "
from src.database_manager import DatabaseManager
import os
from dotenv import load_dotenv

load_dotenv()
db = DatabaseManager(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
if db.test_connection():
    print('✅ 데이터베이스 연결 성공!')
    # 데이터 확인
    result = db.client.table('restaurants').select('*').limit(3).execute()
    print(f'📊 데이터 확인: {len(result.data)}개 샘플 조회 성공')
    print(f'🏪 첫 번째 레스토랑: {result.data[0][\"restaurant_name\"]} - {result.data[0][\"menu_name\"]}')
else:
    print('❌ 데이터베이스 연결 실패')
"
```

**성공 시 출력:**
```
✅ 데이터베이스 연결 성공!
📊 데이터 확인: 3개 샘플 조회 성공
🏪 첫 번째 레스토랑: 청양불향관 - 마라탕
```

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

## 🔍 구현할 검색 방법들

### 1️⃣ 벡터 검색 구현

```python
# search_vector.py
import os
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

# 클라이언트 초기화
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def vector_search(query_text: str, limit: int = 10, threshold: float = 0.7):
    """벡터 검색 구현"""
    
    # 1. 검색어를 임베딩으로 변환
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query_text,
        dimensions=1536
    )
    query_embedding = response.data[0].embedding
    
    # 2. 벡터 검색 실행
    result = supabase.rpc("vector_search", {
        "query_embedding": query_embedding,
        "match_threshold": threshold,
        "match_count": limit
    }).execute()
    
    return result.data

# 테스트
if __name__ == "__main__":
    results = vector_search("매운 국물 요리")
    for r in results[:3]:
        print(f"🍜 {r['restaurant_name']} - {r['menu_name']} (유사도: {r['similarity']:.3f})")
```

### 2️⃣ 키워드 검색 구현

```python
# search_keyword.py
def keyword_search(query_text: str, limit: int = 10):
    """키워드 검색 구현"""
    
    result = supabase.rpc("keyword_search", {
        "search_query": query_text,
        "match_count": limit
    }).execute()
    
    return result.data

# 테스트
if __name__ == "__main__":
    results = keyword_search("마라탕")
    for r in results[:3]:
        print(f"🔍 {r['restaurant_name']} - {r['menu_name']} (점수: {r['rank']:.3f})")
```

### 3️⃣ 하이브리드 검색 구현

```python
# search_hybrid.py
def hybrid_search(query_text: str, vector_weight: float = 0.7, limit: int = 10):
    """하이브리드 검색 구현 (RRF 방식)"""
    
    # 벡터 검색 결과
    vector_results = vector_search(query_text, limit * 2)
    
    # 키워드 검색 결과  
    keyword_results = keyword_search(query_text, limit * 2)
    
    # RRF (Reciprocal Rank Fusion) 점수 계산
    combined_scores = {}
    k = 60  # RRF 상수
    
    # 벡터 검색 점수 추가
    for rank, result in enumerate(vector_results, 1):
        item_id = result['id']
        rrf_score = 1 / (k + rank)
        combined_scores[item_id] = {
            'data': result,
            'vector_rrf': rrf_score,
            'keyword_rrf': 0
        }
    
    # 키워드 검색 점수 추가
    for rank, result in enumerate(keyword_results, 1):
        item_id = result['id']
        rrf_score = 1 / (k + rank)
        
        if item_id in combined_scores:
            combined_scores[item_id]['keyword_rrf'] = rrf_score
        else:
            combined_scores[item_id] = {
                'data': result,
                'vector_rrf': 0,
                'keyword_rrf': rrf_score
            }
    
    # 하이브리드 점수 계산 및 정렬
    for item in combined_scores.values():
        item['hybrid_score'] = (
            vector_weight * item['vector_rrf'] + 
            (1 - vector_weight) * item['keyword_rrf']
        )
    
    sorted_results = sorted(
        combined_scores.values(), 
        key=lambda x: x['hybrid_score'], 
        reverse=True
    )
    
    return sorted_results[:limit]

# 테스트
if __name__ == "__main__":
    results = hybrid_search("매운 국물")
    for r in results[:3]:
        data = r['data']
        print(f"🔥 {data['restaurant_name']} - {data['menu_name']} (하이브리드: {r['hybrid_score']:.3f})")
```

## 📊 성능 테스트 가이드

### 테스트 쿼리 세트

```python
# test_queries.py
TEST_QUERIES = [
    # 정확한 메뉴명
    "마라탕", "돈카츠", "연어 포케", "바스크 치즈케이크",
    
    # 재료 기반
    "소고기", "새우", "치즈", "아보카도", "바질",
    
    # 맛/특징 기반
    "매운 음식", "달콤한 디저트", "시원한 국물", "바삭한 요리",
    
    # 조리법
    "구이 요리", "볶음 요리", "국물 요리", "샐러드",
    
    # 복합 쿼리
    "매운 국물 요리", "치즈가 들어간 음식", "바삭한 튀김", "상큼한 샐러드"
]

def run_performance_test():
    """성능 테스트 실행"""
    import time
    import json
    
    results = {"vector": [], "keyword": [], "hybrid": []}
    
    for query in TEST_QUERIES:
        print(f"테스트 중: {query}")
        
        # 각 검색 방법별 시간 및 결과 측정
        for method_name, search_func in [
            ("vector", vector_search),
            ("keyword", keyword_search), 
            ("hybrid", hybrid_search)
        ]:
            start_time = time.time()
            search_results = search_func(query)
            end_time = time.time()
            
            results[method_name].append({
                "query": query,
                "response_time": end_time - start_time,
                "result_count": len(search_results),
                "top_result": search_results[0] if search_results else None
            })
    
    # 결과 저장
    with open("performance_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("✅ 성능 테스트 완료! performance_results.json 확인하세요.")

if __name__ == "__main__":
    run_performance_test()
```

## 🎯 과제 분담 제안

### Phase 2: 검색 기능 구현 (1-2주)
- **팀원 A**: 벡터 검색 최적화 및 성능 튜닝
- **팀원 B**: 키워드 검색 개선 및 한국어 처리
- **팀원 C**: 하이브리드 검색 알고리즘 개발 (RRF, 가중평균 등)
- **팀원 D**: 성능 평가 메트릭 및 테스트 프레임워크

### Phase 3: 테스트 및 평가 (1주)
- 각자 구현한 검색 방법으로 테스트 쿼리 실행
- 정량적 평가: 응답시간, 정확도, 재현율
- 정성적 평가: 사용자 의도 파악, 결과 다양성
- 성능 비교 리포트 작성

### Phase 4: 최적화 및 결론 (1주)
- 하이브리드 검색 가중치 튜닝
- 검색 속도 최적화
- 최종 권장사항 도출

## 🛠️ 개발 팁

### 1. 디버깅용 유틸리티

```python
# utils.py
def pretty_print_results(results, title="검색 결과"):
    """검색 결과를 예쁘게 출력"""
    print(f"\n{title}")
    print("=" * 50)
    
    for i, result in enumerate(results[:5], 1):
        if 'data' in result:  # 하이브리드 검색 결과
            data = result['data']
            score = result.get('hybrid_score', result.get('similarity', result.get('rank', 0)))
        else:  # 일반 검색 결과
            data = result
            score = result.get('similarity', result.get('rank', 0))
            
        print(f"{i}. {data['restaurant_name']} - {data['menu_name']}")
        print(f"   재료: {', '.join(data['key_ingredients'])}")
        print(f"   설명: {data['short_description']}")
        print(f"   점수: {score:.3f}")
        print()

def compare_all_methods(query):
    """세 가지 검색 방법 비교"""
    print(f"🔍 검색어: '{query}'")
    
    vector_results = vector_search(query)
    keyword_results = keyword_search(query)  
    hybrid_results = hybrid_search(query)
    
    pretty_print_results(vector_results, "벡터 검색")
    pretty_print_results(keyword_results, "키워드 검색")
    pretty_print_results(hybrid_results, "하이브리드 검색")

# 사용 예시
if __name__ == "__main__":
    compare_all_methods("매운 국물 요리")
```

### 2. 자주 사용하는 SQL 쿼리

```sql
-- 전체 데이터 수 확인
SELECT COUNT(*) as total_items FROM restaurants;

-- 임베딩이 있는 데이터 수
SELECT COUNT(*) as with_embeddings FROM restaurants WHERE embedding IS NOT NULL;

-- 레스토랑별 메뉴 수 TOP 10
SELECT restaurant_name, COUNT(*) as menu_count 
FROM restaurants 
GROUP BY restaurant_name 
ORDER BY menu_count DESC 
LIMIT 10;

-- 가장 긴 결합 텍스트 TOP 5
SELECT restaurant_name, menu_name, LENGTH(combined_text) as text_length
FROM restaurants 
ORDER BY text_length DESC 
LIMIT 5;
```

## 🔧 문제 해결

### 자주 발생하는 문제들

#### 1. OpenAI API 오류
```bash
# API 키 확인
echo $OPENAI_API_KEY

# 사용량 확인: OpenAI 대시보드에서 확인
# Rate limit 오류 시: 요청 간격 조정 또는 배치 크기 줄이기
```

#### 2. Supabase 연결 오류
```bash
# 환경변수 확인
echo $SUPABASE_URL
echo $SUPABASE_KEY

# 프로젝트 상태 확인: Supabase 대시보드에서 확인
```

#### 3. 검색 결과 없음
- 임계값(threshold) 낮추기: 0.7 → 0.5
- 검색어 전처리 확인
- 데이터 존재 여부 확인

#### 4. 성능 이슈
- 배치 크기 조정: `BATCH_SIZE=20`
- 인덱스 확인: 벡터 인덱스 생성 여부
- 쿼리 최적화: LIMIT 사용

## 📞 지원 및 소통

- **팀 채널**: #vector-search-project
- **이슈 리포팅**: GitHub Issues
- **코드 리뷰**: Pull Request
- **일일 스탠드업**: 매일 오전 10시

## 🎯 성공 기준

### 기능적 요구사항
- [ ] 벡터 검색 구현 완료
- [ ] 키워드 검색 구현 완료  
- [ ] 하이브리드 검색 구현 완료
- [ ] 성능 테스트 프레임워크 구축

### 성능 요구사항
- [ ] 평균 응답시간 < 500ms
- [ ] 검색 정확도 > 70%
- [ ] 사용자 만족도 > 4.0/5.0

### 문서화 요구사항
- [ ] 각 검색 방법 상세 문서
- [ ] 성능 비교 분석 리포트
- [ ] 최종 권장사항 도출

---

**🚀 화이팅! 멋진 검색 시스템을 만들어봅시다!**
