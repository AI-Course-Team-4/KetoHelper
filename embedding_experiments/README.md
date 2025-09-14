# 레시피 임베딩 방식 비교 실험

3가지 다른 임베딩 방식으로 레시피 검색 성능을 비교하는 실험입니다.

## 실험 구조

```
embedding_experiments/
├── approach1_title_blob/          # 방식1: 제목 포함 blob
├── approach2_no_title_blob/       # 방식2: 제목 제외 blob
├── approach3_llm_preprocessing/   # 방식3: LLM 전처리
├── shared/                        # 공통 코드
├── run_experiment.py              # 실험 실행 스크립트
└── embeddings_comparison.db       # 실험 결과 DB
```

## 3가지 임베딩 방식

### 1. 방식1: 레시피명 + blob 임베딩
- 레시피 제목을 포함하여 모든 정보를 하나의 텍스트 blob으로 구성
- 제목의 가중치가 검색 결과에 영향을 미침

### 2. 방식2: 제목 제외 blob 임베딩
- 레시피 제목을 제외하고 재료, 조리순서 등만으로 구성
- 내용 기반 검색에 더 집중

### 3. 방식3: LLM 기반 전처리 + 임베딩
- OpenAI GPT-3.5를 사용하여 레시피 정보를 구조화
- 정규화된 키워드와 분류 정보 활용

## 실험 설정

- **골든셋 크기**: 각 방식당 50개 레시피
- **테스트 쿼리**: 30개 (재료, 요리법, 특성별로 분류)
- **평가 지표**: Precision@K, Recall@K, MRR, MAP, 응답시간

## 사용법

### 1. 환경 설정
```bash
conda activate recipe_test
pip install -r requirements.txt
```

### 2. OpenAI API 키 설정 (방식3용)
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. 실험 실행

#### 전체 실험 (설정 + 평가)
```bash
python run_experiment.py --mode full
```

#### 빠른 동작 테스트
```bash
python run_experiment.py --mode test
```

#### 설정만 실행
```bash
python run_experiment.py --mode setup
```

#### 평가만 실행 (이미 설정된 경우)
```bash
python run_experiment.py --mode eval
```

## 결과 파일

- `evaluation_report.txt`: 상세한 성능 분석 보고서
- `comparison_plot.png`: 성능 비교 그래프
- `embeddings_comparison.db`: 각 방식별 임베딩 데이터

## 평가 지표 설명

- **MRR (Mean Reciprocal Rank)**: 첫 번째 관련 문서의 평균 역순위
- **MAP (Mean Average Precision)**: 평균 정확도의 평균
- **Precision@K**: 상위 K개 결과 중 관련 문서 비율
- **Recall@K**: 전체 관련 문서 중 상위 K개에 포함된 비율

## 예상 결과

각 방식별 장단점:

1. **제목 포함 방식**: 제목 기반 검색에 유리, 빠른 응답
2. **제목 제외 방식**: 내용 기반 상세 검색에 유리
3. **LLM 전처리 방식**: 의미론적 검색에 우수, 처리 시간 증가