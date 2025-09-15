# Hybrid Search Test

## 프로젝트 구조
```
hybrid_search_test/
├── __init__.py
├── README.md
├── config/
│   ├── __init__.py
│   └── settings.py          # 환경 설정 및 상수
├── core/
│   ├── __init__.py
│   ├── keyword_search.py    # 키워드 검색 엔진
│   ├── vector_search.py     # 벡터 검색 엔진
│   ├── hybrid_search.py     # 하이브리드 검색 엔진
│   └── similarity.py        # 유사도 계산 유틸리티
├── utils/
│   ├── __init__.py
│   ├── database.py          # Supabase 연결 및 쿼리
│   ├── embedding.py         # OpenAI 임베딩 생성
│   └── formatter.py         # 결과 포맷팅
├── analysis/
│   ├── __init__.py
│   ├── comparator.py        # 검색 결과 비교 분석
│   └── metrics.py           # 성능 메트릭 계산
├── cli/
│   ├── __init__.py
│   └── search_cli.py        # CLI 테스트 도구
└── tests/
    ├── __init__.py
    ├── test_keyword.py      # 키워드 검색 테스트
    ├── test_vector.py       # 벡터 검색 테스트
    └── test_hybrid.py       # 하이브리드 검색 테스트
```

## 주요 기능
1. **키워드 검색**: Supabase full-text search
2. **벡터 검색**: pgvector 코사인 유사도
3. **하이브리드 검색**: 가중 평균 방식
4. **성능 분석**: 3가지 방식 비교 및 점수 정규화 (0-100%)

## 사용법
```bash
# CLI 테스트 도구 실행
python -m hybrid_search_test.cli.search_cli

# 개별 검색 엔진 테스트
python -m hybrid_search_test.tests.test_keyword
python -m hybrid_search_test.tests.test_vector
python -m hybrid_search_test.tests.test_hybrid
```
