# 🎯 가중치 설정 완전 가이드

## 📖 개요
각 개발자별로 다른 가중치 설정을 실험할 수 있는 중앙 관리 시스템입니다.
**실제 사용 예시와 단계별 가이드**를 포함한 완전 매뉴얼입니다.

## 🚀 1단계: 서버 실행하기

### **가장 간단한 방법: 명령어 복사 붙여넣기**

#### **수환님 실험용 서버:**
```bash
cd backend && python run_server_enhanced.py soohwan
```

#### **지현님 실험용 서버:**
```bash
cd backend && python run_server_enhanced.py jihyun
```

#### **민석님 실험용 서버:**
```bash
cd backend && python run_server_enhanced.py minseok
```

#### **기본 설정 서버:**
```bash
cd backend && python run_server_enhanced.py default
```

**사용법:**
1. 터미널 열기 (Ctrl + `)
2. 위 명령어 중 하나 복사
3. 붙여넣기 후 Enter
4. 완료! 🎉

**실행하면 이런 화면이 나타납니다:**
```
🚀 키토 코치 백엔드 서버 시작
======================================================================
🔧 환경 설정 완료: DEVELOPER_NAME=soohwan
✅ soohwan님의 개인 설정 로드됨
🧪 search_accuracy_improvement 실험 설정 적용됨
📈 예상 효과: 검색 정확도 +25%, 다양성 -15%

🔧 가중치 설정 정보
======================================================================
👤 개발자: soohwan
🧪 실험명: search_accuracy_improvement
📝 설명: 벡터 검색 가중치 증가로 검색 정확도 개선 실험

📊 LLM 가중치:
  - Temperature: 0.1
  - Max Tokens: 8192
  - Timeout: 60s

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
  - 당분: -10점
  - 가공식품: -12점

🎯 기타 설정:
  - 유사도 임계값: 0.8
  - 최대 검색 결과: 3개
======================================================================

🌐 서버 시작 중...
📍 주소: http://0.0.0.0:8000
📚 API 문서: http://0.0.0.0:8000/docs
🔄 자동 재시작: 활성화
⏹️ 종료: Ctrl+C
```

### **고급 옵션 (필요시 사용)**

#### **포트 변경:**
```bash
cd backend; python run_server_enhanced.py soohwan --port 8001
```

#### **자동 재시작 비활성화:**
```bash
cd backend; python run_server_enhanced.py soohwan --no-reload
```

#### **실험명과 설명 추가:**
```bash
cd backend; python run_server_enhanced.py soohwan --experiment-name "my_test" --description "테스트용"
```

## 🔧 2단계: 개인 설정 파일 수정하기

### 📁 파일 위치 확인
```
backend/config/weight_configs/
├── soohwan.py    # 수환님 설정 (수정 가능)
├── jihyun.py     # 지현님 설정 (수정 가능)
├── minseok.py    # 민석님 설정 (수정 가능)
└── __init__.py   # 패키지 파일 (수정 금지)
```

### ✏️ 실제 수정 예시

#### 예시 1: 검색 정확도를 더 높이고 싶다면
```python
# backend/config/weight_configs/각자 이름름.py 파일을 열어서

class PersonalWeightConfig(WeightConfig):
    def __init__(self):
        super().__init__()
        
        # 실험 정보 업데이트
        self.developer_name = "soohwan"
        self.experiment_name = "ultra_high_accuracy"  # 실험명 변경
        self.description = "벡터 검색을 더 강화해서 정확도를 극대화"  # 설명 변경
        
        # 가중치 더 강하게 조정
        self.vector_search_weight = 0.7      # 50% → 70% (더 강화!)
        self.exact_ilike_weight = 0.3       # 30% → 30% (유지)
        self.fts_weight = 0.0              # 20% → 0% (완전 제거)
        self.trigram_weight = 0.0          # 0% → 0% (유지)
        self.ilike_fallback_weight = 0.0   # 0% → 0% (유지)
        
        # 유사도 임계값 더 엄격하게
        self.similarity_threshold = 0.9     # 0.8 → 0.9 (더 엄격!)
        self.max_search_results = 2        # 3 → 2 (더 적은 결과)
        
        print(f"🧪 {self.experiment_name} 실험 설정 적용됨")
        print(f"📈 예상 효과: 검색 정확도 +40%, 다양성 -30%")
```

#### 예시 2: 다양성을 더 높이고 싶다면
```python
# backend/config/weight_configs/jihyun.py 파일을 열어서

class PersonalWeightConfig(WeightConfig):
    def __init__(self):
        super().__init__()
        
        # 실험 정보 업데이트
        self.developer_name = "jihyun"
        self.experiment_name = "maximum_diversity"  # 실험명 변경
        self.description = "모든 검색 방식을 균등하게 사용해서 최대 다양성 달성"  # 설명 변경
        
        # 가중치 균등하게 조정
        self.vector_search_weight = 0.2      # 30% → 20% (감소)
        self.exact_ilike_weight = 0.2        # 25% → 20% (감소)
        self.fts_weight = 0.2               # 25% → 20% (감소)
        self.trigram_weight = 0.2           # 15% → 20% (증가)
        self.ilike_fallback_weight = 0.2    # 5% → 20% (대폭 증가!)
        
        # 유사도 임계값 더 관대하게
        self.similarity_threshold = 0.5     # 0.6 → 0.5 (더 관대!)
        self.max_search_results = 10       # 7 → 10 (더 많은 결과)
        
        print(f"🧪 {self.experiment_name} 실험 설정 적용됨")
        print(f"📈 예상 효과: 다양성 +60%, 검색 정확도 -20%")
```

#### 예시 3: 키토 스코어를 더 엄격하게 하고 싶다면
```python
# backend/config/weight_configs/minseok.py 파일을 열어서

class PersonalWeightConfig(WeightConfig):
    def __init__(self):
        super().__init__()
        
        # 실험 정보 업데이트
        self.developer_name = "minseok"
        self.experiment_name = "strict_keto_scoring"  # 실험명 변경
        self.description = "키토 친화도 평가를 더욱 엄격하게 해서 정확도 극대화"  # 설명 변경
        
        # 키토 스코어 가중치 대폭 강화
        self.protein_weight = 35            # 25 → 35 (대폭 강화!)
        self.vegetable_weight = 25          # 18 → 25 (강화)
        self.carb_penalty = -35             # -25 → -35 (더 강한 패널티!)
        self.sugar_penalty = -25            # -15 → -25 (더 강한 패널티!)
        self.processed_penalty = -30       # -18 → -30 (더 강한 패널티!)
        
        # 하이브리드 검색 가중치도 강화
        self.vector_score_weight = 1.5      # 1.2 → 1.5 (더 강화!)
        self.keyword_score_weight = 0.5     # 0.8 → 0.5 (감소)
        self.keto_score_weight = 2.0        # 1.5 → 2.0 (대폭 강화!)
        
        print(f"🧪 {self.experiment_name} 실험 설정 적용됨")
        print(f"📈 예상 효과: 키토 평가 정확도 +50%, 식당 추천 품질 +30%")
```

### 🆕 새로운 개발자 추가하기

#### 1단계: 개인 설정 파일 생성
```bash
# backend/config/weight_configs/새이름.py 파일 생성
# 예: backend/config/weight_configs/hyunjin.py
```

#### 2단계: 설정 파일 작성
```python
# backend/config/weight_configs/hyunjin.py
from app.core.weight_config import WeightConfig

class PersonalWeightConfig(WeightConfig):
    """현진님의 개인 실험용 가중치"""
    
    def __init__(self):
        super().__init__()
        
        # 실험 메타데이터
        self.developer_name = "hyunjin"
        self.experiment_name = "balanced_approach"
        self.description = "정확도와 다양성의 균형을 찾는 실험"
        
        # 균형잡힌 가중치 설정
        self.vector_search_weight = 0.35     # 기본값과 약간 다르게
        self.exact_ilike_weight = 0.3        # 기본값과 약간 다르게
        self.fts_weight = 0.25               # 기본값과 약간 다르게
        self.trigram_weight = 0.1            # 기본값과 약간 다르게
        self.ilike_fallback_weight = 0.0     # 기본값과 약간 다르게
        
        # 키토 스코어도 약간 조정
        self.protein_weight = 18            # 기본값 15에서 약간 증가
        self.vegetable_weight = 12          # 기본값 10에서 약간 증가
        self.carb_penalty = -18             # 기본값 -15에서 약간 강화
        
        print(f"🧪 {self.experiment_name} 실험 설정 적용됨")
        print(f"📈 예상 효과: 정확도 +10%, 다양성 +10%")
```

#### 3단계: 서버 실행
```bash
# 터미널에서 실행
cd backend; python run_server_enhanced.py hyunjin
```

## 🧪 3단계: 실험 진행하기

### 📋 실험 체크리스트

#### 실험 전 준비
- [ ] 개인 설정 파일 수정 완료
- [ ] 실험명과 설명 업데이트
- [ ] 예상 효과 명시
- [ ] 서버 실행 준비

#### 실험 중 확인사항
- [ ] 서버가 정상적으로 시작되는지 확인
- [ ] 가중치 설정이 올바르게 로드되는지 확인
- [ ] 프론트엔드에서 기능 테스트
- [ ] 결과 품질 관찰 및 기록

#### 실험 후 정리
- [ ] 결과 분석 및 문서화
- [ ] 팀원들과 결과 공유
- [ ] 성공한 설정은 다른 팀원도 테스트
- [ ] 실패한 실험도 학습 자료로 활용

### 🔍 실제 테스트 방법

#### 1. 식단 추천 테스트
```bash
# 서버 실행 후 프론트엔드에서 테스트
1. http://localhost:3000 접속
2. "7일 키토 식단 추천해줘" 입력
3. 결과 품질 관찰:
   - 메뉴 다양성 (중복 메뉴가 적은가?)
   - 관련성 (요청과 맞는 메뉴인가?)
   - 키토 친화도 (키토 원칙에 맞는가?)
```

#### 2. 레시피 검색 테스트
```bash
# 다양한 검색어로 테스트
1. "계란 요리" 검색
2. "삼겹살 구이" 검색  
3. "키토 샐러드" 검색
4. 결과 품질 관찰:
   - 검색 정확도 (관련성 높은 결과인가?)
   - 결과 다양성 (다양한 종류의 레시피인가?)
   - 응답 속도 (빠른가?)
```

#### 3. 식당 검색 테스트
```bash
# 키토 스코어 개선 실험 시
1. "강남 키토 식당" 검색
2. "홍대 근처 키토 친화 식당" 검색
3. 결과 품질 관찰:
   - 키토 스코어 정확도 (적절한 점수인가?)
   - 식당 추천 품질 (실제로 키토에 적합한가?)
```

### 📊 성능 측정 방법

#### 정량적 지표
```python
# 검색 정확도 측정
정확도 = (관련성 높은 결과 수) / (전체 결과 수) × 100

# 다양성 측정  
다양성 = (고유한 메뉴 수) / (전체 메뉴 수) × 100

# 키토 친화도 측정
키토_정확도 = (적절한 키토 점수 결과 수) / (전체 결과 수) × 100
```

#### 정성적 평가
- **사용자 피드백**: 실제 사용해보고 느낀 점
- **전문가 평가**: 키토 전문가 관점에서의 평가
- **비교 분석**: 다른 설정과의 비교

## 📊 현재 실험 설정 요약

### 수환님 (soohwan) - 검색 정확도 개선
- **목표**: 검색 정확도 향상
- **핵심 변경**: 벡터 검색 50%, 정확 매칭 30%, 전문 검색 20%
- **예상 효과**: 정확도 +25%, 다양성 -15%
- **테스트 방법**: 정확한 키워드로 검색하여 관련성 확인

### 지현님 (jihyun) - 다양성 개선  
- **목표**: 메뉴 다양성 향상
- **핵심 변경**: 모든 검색 방식 균등 분배 (각 20%)
- **예상 효과**: 다양성 +40%, 정확도 -10%
- **테스트 방법**: 같은 키워드로 여러 번 검색하여 중복 확인

### 민석님 (minseok) - 키토 스코어 최적화
- **목표**: 키토 친화도 평가 정확도 향상
- **핵심 변경**: 단백질 +25점, 채소 +18점, 탄수화물 -25점
- **예상 효과**: 키토 평가 정확도 +35%, 식당 추천 품질 +20%
- **테스트 방법**: 키토/비키토 식당으로 검색하여 점수 정확성 확인

## 🚨 4단계: 문제 해결하기

### 자주 발생하는 문제들

#### 문제 1: 서버가 시작되지 않음
```bash
❌ 오류: ModuleNotFoundError: No module named 'app'
```
**해결방법:**
1. `backend` 디렉토리에서 실행하는지 확인
2. 가상환경이 활성화되어 있는지 확인
3. `python run_server_enhanced.py 각자이름` 명령어 사용

#### 문제 2: 개인 설정이 로드되지 않음
```bash
⚠️ soohwan.py 파일을 찾을 수 없습니다
```
**해결방법:**
1. 파일 경로 확인: `backend/config/weight_configs/soohwan.py`
2. 파일명 철자 확인 (대소문자 구분)
3. `PersonalWeightConfig` 클래스명 확인

#### 문제 3: 가중치가 적용되지 않음
```bash
✅ 환경변수에서 기본 설정 로드됨  # 개인 설정이 아닌 기본 설정이 로드됨
```
**해결방법:**
1. `DEVELOPER_NAME` 환경변수 확인
2. 개인 설정 파일 문법 오류 확인
3. `PersonalWeightConfig` 클래스 구현 확인

#### 문제 4: 프론트엔드에서 결과가 다름
**해결방법:**
1. 서버 재시작 확인
2. 브라우저 캐시 삭제
3. 프론트엔드도 재시작

### 🔧 디버깅 방법

#### 1. 설정 확인
```python
# 서버 실행 후 콘솔에서 확인
from app.core.weight_config import weight_config
print(weight_config.developer_name)  # 현재 개발자명
print(weight_config.vector_search_weight)  # 현재 벡터 검색 가중치
```

#### 2. 로그 확인
```bash
# 서버 실행 시 상세 로그 확인
python run_server_enhanced.py soohwan --log-level debug
```

#### 3. 설정 파일 문법 검사
```python
# Python 문법 검사
python -m py_compile config/weight_configs/soohwan.py
```

## 🤝 5단계: 팀 협업하기

### 실험 결과 공유

#### 성공한 실험 공유하기
```markdown
# 🎉 실험 성공 보고서

## 실험 정보
- **개발자**: 수환
- **실험명**: ultra_high_accuracy
- **목표**: 검색 정확도 극대화

## 변경사항
- 벡터 검색: 50% → 70%
- 유사도 임계값: 0.8 → 0.9
- 최대 결과: 3개 → 2개

## 결과
- 검색 정확도: +40% (예상 +40%)
- 다양성: -30% (예상 -30%)
- 사용자 만족도: +25%

## 권장사항
다른 팀원들도 테스트해보세요!
```

#### 실패한 실험도 공유하기
```markdown
# 📚 실험 실패 보고서

## 실험 정보
- **개발자**: 지현
- **실험명**: extreme_diversity
- **목표**: 다양성 극대화

## 변경사항
- 모든 검색 방식: 각 20%
- 유사도 임계값: 0.6 → 0.3

## 결과
- 다양성: +60% (예상 +60%)
- 검색 정확도: -50% (예상 -20%) ⚠️ 예상보다 많이 떨어짐
- 사용자 만족도: -30%

## 학습 포인트
유사도 임계값을 너무 낮추면 품질이 크게 떨어집니다.
다음 실험에서는 0.5 정도로 조정해보겠습니다.
```

### 코드 리뷰 요청

#### 개인 설정 파일 리뷰
```markdown
# 🔍 코드 리뷰 요청

## 변경사항
- 파일: `config/weight_configs/soohwan.py`
- 실험: 검색 정확도 개선

## 변경 이유
사용자들이 "정확하지 않은 결과"라고 피드백을 주어서
벡터 검색 가중치를 높여보겠습니다.

## 예상 효과
- 검색 정확도: +25%
- 다양성: -15%

## 리뷰 포인트
1. 가중치 비율이 합리적인가?
2. 예상 효과가 현실적인가?
3. 다른 가중치도 함께 조정해야 하는가?
```

## 📈 6단계: 성능 모니터링

### 추천 지표

#### 정량적 지표
- **검색 정확도**: 관련성 높은 결과 비율
- **다양성**: 중복 메뉴 비율  
- **사용자 만족도**: 피드백 점수
- **응답 시간**: 서버 응답 속도

#### 측정 방법
1. **A/B 테스트**: 설정 비교
2. **사용자 피드백**: 실제 사용 경험
3. **로그 분석**: 성능 데이터
4. **정기 리뷰**: 주간 성능 검토

### 성능 대시보드 (향후 구현)

```python
# 성능 모니터링 예시 (향후 구현)
class PerformanceMonitor:
    def track_search_accuracy(self, query, results):
        # 검색 정확도 추적
        pass
    
    def track_diversity(self, meal_plan):
        # 다양성 추적
        pass
    
    def track_user_satisfaction(self, feedback_score):
        # 사용자 만족도 추적
        pass
```

## 🔄 업데이트 가이드

### 새로운 가중치 추가
1. `WeightConfig` 클래스에 새 필드 추가
2. 개인 설정 파일들에 기본값 설정
3. 환경변수 지원 추가 (선택사항)

### 기존 가중치 수정
1. 기본값 변경 시 모든 개인 설정 파일 확인
2. 하위 호환성 고려
3. 변경 사항 문서화

---

💡 **팁**: 실험할 때는 작은 변경부터 시작하고, 효과를 확인한 후 더 큰 변경을 시도하세요!

🎯 **목표**: 각자 다른 실험을 하면서도 안전하게 협업하고, 최적의 가중치 설정을 찾아가세요!

## 🚨 주의사항

1. **Git 관리**: 모든 설정 파일은 Git에 포함됩니다
2. **충돌 방지**: 각자 다른 파일을 수정하므로 충돌 없음
3. **롤백 가능**: Git 히스토리로 언제든 되돌릴 수 있음
4. **배포 안전**: 프로덕션은 기본 설정 사용

---

## 🎯 빠른 시작 체크리스트

### 첫 번째 실험하기
- [ ] 터미널에서 `cd backend; python run_server_enhanced.py 본인이름` 실행
- [ ] 서버가 정상 시작되는지 확인
- [ ] 가중치 설정이 올바르게 표시되는지 확인
- [ ] 프론트엔드에서 기능 테스트
- [ ] 결과 품질 관찰 및 기록

### 가중치 수정하기
- [ ] `backend/config/weight_configs/본인이름.py` 파일 열기
- [ ] 원하는 가중치 값 수정
- [ ] 실험명과 설명 업데이트
- [ ] 서버 재시작
- [ ] 변경된 설정 확인

### 팀과 공유하기
- [ ] 실험 결과 정리
- [ ] 팀 채널에 결과 공유
- [ ] 성공/실패 경험 공유
- [ ] 다른 팀원 실험 결과 확인

---

💡 **팁**: 실험할 때는 작은 변경부터 시작하고, 효과를 확인한 후 더 큰 변경을 시도하세요!

🎯 **목표**: 각자 다른 실험을 하면서도 안전하게 협업하고, 최적의 가중치 설정을 찾아가세요!
