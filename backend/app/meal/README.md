# Meal 모듈 🍽️

키토 식단표 생성 및 레시피 관리를 담당하는 모듈입니다.

## 📁 폴더 구조

```
meal/
├── agents/          # 식단 계획 에이전트들
├── api/            # 식단 관련 API 엔드포인트
├── models/         # 식단 데이터 모델
├── prompts/        # 식단 생성용 프롬프트 템플릿
├── tools/          # 식단 분석 도구들
└── README.md       # 이 파일
```

## 🤖 에이전트 개인화 가이드

### MealPlannerAgent 커스터마이징

`agents/meal_planner.py`의 `MealPlannerAgent` 클래스를 개인화하여 자신만의 식단 계획 에이전트를 만들 수 있습니다.

#### 1. 기본 설정 변경

```python
class MealPlannerAgent:
    # 개인화 설정 - 이 부분을 수정하세요
    AGENT_NAME = "나만의 식단 플래너"
    PROMPT_FILES = {
        "structure": "my_meal_structure",      # 식단 구조 계획
        "generation": "my_meal_generation",    # 개별 메뉴 생성
        "notes": "my_meal_notes"              # 식단 조언 생성
    }
    TOOL_FILES = {
        "keto_score": "my_keto_calculator"    # 키토 점수 계산기
    }
```

#### 2. 개인 프롬프트 파일 생성

각 기능별로 프롬프트 파일을 생성하세요:

**prompts/my_meal_structure.py** - 식단 구조 계획
```python
MEAL_PLAN_STRUCTURE_PROMPT = """
{days}일 키토 식단표의 전체 구조를 계획하세요.
제약 조건: {constraints}

여기에 자신만의 식단 계획 로직을 작성...
"""

# 다른 접근법들
STRUCTURE_PROMPT = "..."
PROMPT = "..."
```

**prompts/my_meal_generation.py** - 개별 메뉴 생성
```python
MEAL_GENERATION_PROMPT = """
{slot}에 적합한 {meal_type} 키토 메뉴를 생성하세요.
제약 조건: {constraints}

여기에 자신만의 메뉴 생성 로직을 작성...
"""
```

**prompts/my_meal_notes.py** - 식단 조언
```python
MEAL_PLAN_NOTES_PROMPT = """
키토 식단표에 대한 실용적인 조언을 생성하세요.
제약 조건: {constraints}

여기에 자신만의 조언 생성 로직을 작성...
"""
```

#### 3. 개인 도구 파일 생성 (선택사항)

**tools/my_keto_calculator.py**
```python
class MyKetoCalculator:
    """자신만의 키토 점수 계산기"""
    
    def calculate_score(self, name: str, category: str, address: str):
        # 자신만의 점수 계산 로직
        return {
            "score": 8,
            "reasons": ["자신만의 평가 기준"],
            "tips": ["개인화된 팁"]
        }
```

#### 4. 에이전트 인스턴스 생성

```python
# 기본 에이전트
agent = MealPlannerAgent()

# 개인화된 에이전트
my_agent = MealPlannerAgent(
    prompt_files={
        "structure": "my_meal_structure",
        "generation": "my_meal_generation", 
        "notes": "my_meal_notes"
    },
    tool_files={
        "keto_score": "my_keto_calculator"
    },
    agent_name="내 전용 식단 플래너"
)
```

## 📝 프롬프트 작성 가이드

### 식단 구조 프롬프트

**목적**: 전체 식단의 구조를 계획
**입력 변수**:
- `{days}`: 식단 일수
- `{constraints}`: 제약 조건 (칼로리, 알레르기 등)

**출력 형식**: JSON 배열
```json
[
    {
        "day": 1,
        "breakfast_type": "계란 요리",
        "lunch_type": "샐러드",
        "dinner_type": "고기 요리",
        "snack_type": "견과류"
    }
]
```

### 메뉴 생성 프롬프트

**목적**: 구체적인 메뉴 생성
**입력 변수**:
- `{slot}`: 식사 시간 (breakfast, lunch, dinner, snack)
- `{meal_type}`: 메뉴 타입
- `{constraints}`: 제약 조건

**출력 형식**: JSON 객체
```json
{
    "type": "recipe",
    "title": "키토 스크램블 에그",
    "macros": {"kcal": 350, "carb": 5, "protein": 25, "fat": 25},
    "ingredients": [{"name": "계란", "amount": 3, "unit": "개"}],
    "steps": ["계란을 풀어주세요.."],
    "tips": ["올리브오일 사용 권장"]
}
```

### 조언 생성 프롬프트

**목적**: 식단 실행을 위한 실용적 조언
**입력 변수**:
- `{constraints}`: 제약 조건

**출력 형식**: 문자열 리스트 (각 줄이 하나의 팁)

## 🔧 API 사용법

### 식단표 생성

```python
POST /api/meal/plans
{
    "days": 7,
    "kcal_target": 1800,
    "carbs_max": 30,
    "allergies": ["새우", "견과류"],
    "dislikes": ["브로콜리"]
}
```

### 응답 형식

```json
{
    "days": [
        {
            "breakfast": {"title": "키토 스크램블", "macros": {...}},
            "lunch": {"title": "치킨 샐러드", "macros": {...}},
            "dinner": {"title": "연어 구이", "macros": {...}},
            "snack": {"title": "아몬드", "macros": {...}}
        }
    ],
    "total_macros": {
        "avg_kcal": 1750,
        "avg_carb": 28,
        "avg_protein": 120,
        "avg_fat": 135
    },
    "notes": [
        "충분한 물을 마시세요",
        "전해질 보충을 잊지 마세요"
    ]
}
```

## 🛠️ 도구 개발 가이드

### 키토 점수 계산기

도구 클래스는 다음 메서드를 구현해야 합니다:

```python
class MyKetoCalculator:
    def calculate_score(self, name: str, category: str, address: str) -> Dict:
        """
        키토 친화도 점수 계산
        
        Args:
            name: 음식/식당 이름
            category: 카테고리
            address: 주소 (식당의 경우)
            
        Returns:
            {
                "score": int (0-10),
                "reasons": List[str],
                "tips": List[str]
            }
        """
        pass
```

### 사용자 정의 도구 예시

```python
# tools/nutritionist_calculator.py
class NutritionistCalculator:
    """영양사 관점의 키토 평가"""
    
    def calculate_score(self, name, category, address):
        # 영양학적 관점에서 평가
        nutrition_score = self._analyze_nutrition(name)
        health_impact = self._assess_health_impact(category)
        
        return {
            "score": (nutrition_score + health_impact) // 2,
            "reasons": [f"영양가 점수: {nutrition_score}", f"건강 영향: {health_impact}"],
            "tips": ["영양소 균형을 고려하세요", "적정량 섭취 권장"]
        }
    
    def _analyze_nutrition(self, name):
        # 영양 분석 로직
        return 8
    
    def _assess_health_impact(self, category):
        # 건강 영향 평가 로직
        return 7
```

## 🎯 식단 생성 시나리오

### 1. 기본 7일 식단
- 일반적인 키토 식단 구성
- 매크로 영양소 균형 고려
- 다양성 확보

### 2. 제약 조건이 있는 식단
- 알레르기 고려
- 칼로리 목표 맞춤
- 비선호 음식 제외

### 3. AI 레시피 생성
- 검색 결과 없을 때 자동 생성
- 사용자 요청에 맞춤 레시피
- 영양소 정보 포함

## 🔍 고급 커스터마이징

### 식단 스타일별 프롬프트

**한식 중심 키토**
```python
KOREAN_KETO_STRUCTURE = """
한국 전통 음식을 기반으로 한 키토 식단을 계획하세요.
- 김치, 된장찌개 (두부 중심)
- 불고기, 갈비 (양념 조절)
- 나물류 (당근, 우엉 제외)
"""
```

**지중해 키토**
```python
MEDITERRANEAN_KETO_STRUCTURE = """
지중해식 키토 식단을 계획하세요.
- 올리브오일, 견과류 중심
- 생선, 해산물 활용
- 허브와 향신료 사용
"""
```

### 개인 건강 상태별 조정

```python
# prompts/diabetic_keto.py - 당뇨 환자용
DIABETIC_KETO_PROMPT = """
당뇨 환자를 위한 키토 식단을 생성하세요.
- 혈당 지수 고려
- 식이섬유 충분히 포함
- 규칙적인 식사 시간 고려
"""

# prompts/athlete_keto.py - 운동선수용  
ATHLETE_KETO_PROMPT = """
운동선수를 위한 키토 식단을 생성하세요.
- 높은 칼로리 요구량
- 운동 전후 영양 타이밍
- 전해질 보충 강화
"""
```

## 📚 개발자 팁

### 1. 프롬프트 테스트
- 다양한 제약 조건으로 테스트
- JSON 출력 형식 검증
- 영양소 계산 정확성 확인

### 2. 오류 처리
- 프롬프트 파일 없을 때 기본값 사용
- 도구 클래스 로딩 실패 시 대안 제공
- JSON 파싱 실패 시 폴백 데이터

### 3. 성능 최적화
- 프롬프트 길이 적절히 조절
- 불필요한 AI 호출 최소화
- 캐싱 활용 고려

## 🤝 협업 가이드

### 팀원별 전문 분야

```python
# 팀원 A - 한식 전문
korean_planner = MealPlannerAgent(
    prompt_files={
        "structure": "korean_meal_structure",
        "generation": "korean_recipe_gen"
    },
    agent_name="한식 키토 전문가"
)

# 팀원 B - 서양식 전문  
western_planner = MealPlannerAgent(
    prompt_files={
        "structure": "western_meal_structure", 
        "generation": "western_recipe_gen"
    },
    agent_name="서양식 키토 전문가"
)
```

### 프롬프트 공유 방법

1. **베이스 템플릿 공유**: `prompts/base_templates/`
2. **개인 변형 저장**: `prompts/개인이름_목적.py`
3. **팀 리뷰**: 우수한 프롬프트는 팀 공유
4. **버전 관리**: Git으로 프롬프트 변경 이력 관리

---

💡 **식단 생성 품질 개선을 위한 아이디어나 새로운 프롬프트가 있다면 팀과 공유해주세요!**
