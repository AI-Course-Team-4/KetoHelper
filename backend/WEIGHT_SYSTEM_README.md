# 🎯 가중치 중앙 관리 시스템

팀원별로 다른 가중치와 프롬프트를 실험할 수 있는 중앙 관리 시스템입니다.

## 🚀 빠른 시작

### 1. 서버 실행
```bash
cd backend
python run_server_enhanced.py [개발자명]
```

### 2. 사용 가능한 개발자명
- `soohwan` - 수환님 (검색 정확도 개선 실험)
- `jihyun` - 지현님 (다양성 개선 실험)  
- `minseok` - 민석님 (키토 스코어 최적화 실험)
- `default` - 기본 설정

## 📁 파일 구조

```
backend/
├── app/core/weight_config.py          # 가중치 중앙 관리
├── config/weight_configs/             # 개인 설정 파일들
│   ├── soohwan.py                     # 수환님 설정
│   ├── jihyun.py                      # 지현님 설정
│   └── minseok.py                     # 민석님 설정
├── config/personal_config_soohwan.py  # 수환님 프롬프트 설정
├── app/prompts/meal/                  # 개인 프롬프트들
│   ├── soohwan_structure.py           # 수환님 식단표 프롬프트
│   └── soohwan_generation.py         # 수환님 레시피 프롬프트
└── run_server_enhanced.py             # 개선된 서버 실행 스크립트
```

## 🎯 현재 실험 설정

### 수환님 (soohwan) - 검색 정확도 개선
- **가중치**: 벡터 검색 50%, 정확 매칭 30%, 전문 검색 20%
- **프롬프트**: 검색 정확도에 특화된 전용 프롬프트
- **목표**: 검색 정확도 +25%, 다양성 -15%

### 지현님 (jihyun) - 다양성 개선
- **가중치**: 모든 검색 방식 균등 분배 (각 20-30%)
- **프롬프트**: 기본 프롬프트 사용
- **목표**: 다양성 +40%, 검색 정확도 -10%

### 민석님 (minseok) - 키토 스코어 최적화
- **가중치**: 단백질 +25점, 채소 +18점, 탄수화물 -25점
- **프롬프트**: 기본 프롬프트 사용
- **목표**: 키토 평가 정확도 +35%, 식당 추천 품질 +20%

## 🔧 새로운 개발자 추가하기

### 1. 가중치 설정 파일 생성
```python
# config/weight_configs/새이름.py
from app.core.weight_config import WeightConfig

class PersonalWeightConfig(WeightConfig):
    def __init__(self):
        super().__init__()
        
        # 실험 메타데이터
        self.developer_name = "새이름"
        self.experiment_name = "실험명"
        self.description = "실험 설명"
        
        # 프롬프트 설정
        self.use_personal_prompts = False  # 기본 프롬프트 사용
        self.prompt_config_file = "personal_config.py"
        
        # 가중치 설정
        self.vector_search_weight = 0.4
        self.protein_weight = 15
        # ... 기타 설정
```

### 2. 서버 실행
```bash
python run_server_enhanced.py 새이름
```

## 🧪 프롬프트 개인화 (선택사항)

### 1. 개인 프롬프트 설정 파일 생성
```python
# config/personal_config_새이름.py
USE_PERSONAL_CONFIG = True

MEAL_PLANNER_CONFIG = {
    "agent_name": "새이름의 키토 식단 마스터",
    "prompts": {
        "structure": "새이름_structure",
        "generation": "새이름_generation",
        # ... 기타 프롬프트
    }
}
```

### 2. 개인 프롬프트 파일 생성
```python
# app/prompts/meal/새이름_structure.py
새이름_STRUCTURE_PROMPT = """
당신은 새이름의 키토 식단 마스터입니다...
"""
```

### 3. 가중치 설정에서 프롬프트 활성화
```python
# config/weight_configs/새이름.py
self.use_personal_prompts = True
self.prompt_config_file = "personal_config_새이름.py"
```

## 📊 가중치 종류

### LLM 가중치
- `llm_temperature`: 창의성 (0.1-1.0)
- `llm_max_tokens`: 최대 토큰 수
- `llm_timeout`: 타임아웃 (초)

### RAG 검색 가중치
- `vector_search_weight`: 벡터 검색 비율
- `exact_ilike_weight`: 정확 매칭 비율
- `fts_weight`: 전문 검색 비율
- `trigram_weight`: 유사도 검색 비율
- `ilike_fallback_weight`: 폴백 검색 비율

### 키토 스코어 가중치
- `protein_weight`: 단백질 점수
- `vegetable_weight`: 채소 점수
- `carb_penalty`: 탄수화물 패널티
- `sugar_penalty`: 당분 패널티
- `processed_penalty`: 가공식품 패널티

### 기타 설정
- `similarity_threshold`: 유사도 임계값 (0.0-1.0)
- `max_search_results`: 최대 검색 결과 수

## 🔍 설정 확인

서버 실행 시 자동으로 현재 설정이 표시됩니다:

```
🔧 가중치 설정 정보
======================================================================
👤 개발자: soohwan
🧪 실험명: search_accuracy_improvement
📝 설명: 벡터 검색 가중치 증가로 검색 정확도 개선 실험

🔍 RAG 검색 가중치:
  - 벡터 검색: 50.0%
  - 정확 매칭: 30.0%
  - 전문 검색: 20.0%
  - 유사도 검색: 0.0%
  - 폴백 검색: 0.0%

🥑 키토 스코어 가중치:
  - 단백질: +20점
  - 채소: +12점
  - 탄수화물: -20점
======================================================================
```

## 🚨 주의사항

1. **Git 관리**: 모든 설정 파일은 Git에 포함됩니다
2. **충돌 방지**: 각자 다른 파일을 수정하므로 충돌 없음
3. **롤백 가능**: Git 히스토리로 언제든 되돌릴 수 있음
4. **배포 안전**: 프로덕션은 기본 설정 사용

## 📈 성능 모니터링

### 추천 지표
- **검색 정확도**: 관련성 높은 결과 비율
- **다양성**: 중복 메뉴 비율
- **사용자 만족도**: 피드백 점수
- **응답 시간**: 서버 응답 속도

### 측정 방법
1. A/B 테스트로 설정 비교
2. 사용자 피드백 수집
3. 로그 분석을 통한 성능 측정
4. 정기적인 성능 리뷰

---

💡 **팁**: 실험할 때는 작은 변경부터 시작하고, 효과를 확인한 후 더 큰 변경을 시도하세요!

🎯 **목표**: 각자 다른 실험을 하면서도 안전하게 협업하고, 최적의 가중치 설정을 찾아가세요!
