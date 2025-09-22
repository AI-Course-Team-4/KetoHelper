# ⚙️ Config (설정 관리)

개인화 설정과 에이전트 커스터마이징을 관리하는 폴더입니다.

## 📁 구조

```
config/
├── personal_config.py     # 기본 개인화 설정 템플릿
├── .personal_config.py    # 실제 개인 설정 (gitignore됨)
├── config_loader.py       # 설정 로더 유틸리티
└── __init__.py           # 모듈 초기화
```

## 🎯 개인화 설정 사용법

### 1. 개인 설정 파일 생성

```bash
# 1. 기본 템플릿 복사
cp backend/config/personal_config.py backend/config/.personal_config.py

# 2. 개인 설정 활성화
# .personal_config.py에서 USE_PERSONAL_CONFIG = True로 변경
```

### 2. 에이전트별 개인화

#### Meal Planner 개인화
```python
# .personal_config.py
MEAL_PLANNER_CONFIG = {
    "agent_name": "나만의 키토 식단 마스터",
    "prompts": {
        "structure": "soobin_structure",        # 식단표 구조 계획 프롬프트
        "generation": "soobin_generation",      # 개별 레시피 생성 프롬프트
        "notes": "soobin_notes"                 # 식단표 조언 프롬프트
    },
    "tools": {
        "keto_score": "soobin_keto_score"       # 키토 친화도 점수 계산 도구
    }
}
```

#### Restaurant Agent 개인화
```python
RESTAURANT_AGENT_CONFIG = {
    "agent_name": "맛집 헌터 AI",
    "prompts": {
        "search_improvement": "soobin_search_improvement",    # 검색 키워드 개선 프롬프트
        "search_failure": "soobin_search_failure",           # 검색 실패 처리 프롬프트
        "recommendation": "soobin_recommendation"             # 식당 추천 프롬프트
    },
    "tools": {
        "place_search": "soobin_place_search"                # 장소 검색 도구
    }
}
```

#### Chat Agent 개인화
```python
CHAT_AGENT_CONFIG = {
    "agent_name": "키토 선생님",
    "prompt_file_name": "soobin_general_chat"               # 일반 채팅 프롬프트
}
```

### 3. 커스텀 프롬프트 작성

#### 예시: 개인화된 식단 생성 프롬프트
```python
# app/prompts/meal/soobin_generation.py
"""
개인화된 식단 생성 프롬프트
더 친근하고 상세한 설명 제공
"""

SOOBIN_GENERATION_PROMPT = """
안녕하세요! 키토 식단 전문가 {agent_name}입니다 😊

{slot}에 드실 {meal_type} 키토 메뉴를 정성껏 준비해드릴게요!

제약 조건: {constraints}

다음과 같이 상세한 레시피를 제공해드립니다:

{{
    "type": "recipe",
    "title": "메뉴명 (키토 버전)",
    "description": "요리에 대한 친근한 설명",
    "macros": {{"kcal": 칼로리, "carb": 탄수화물g, "protein": 단백질g, "fat": 지방g}},
    "ingredients": [
        {{"name": "재료명", "amount": 양, "unit": "단위", "tips": "구매 팁"}}
    ],
    "steps": [
        "단계별 상세한 조리 과정 (친근한 말투로)"
    ],
    "tips": [
        "키토 성공을 위한 개인적인 조언",
        "맛을 더하는 나만의 비법"
    ],
    "difficulty": "쉬움/보통/어려움",
    "cooking_time": "조리 시간"
}}

💡 추가 팁: 처음 도전하시는 분들을 위한 상세한 가이드도 함께 드릴게요!
"""

# 기본 접근법과의 호환성
MEAL_GENERATION_PROMPT = SOOBIN_GENERATION_PROMPT
PROMPT = SOOBIN_GENERATION_PROMPT
```

### 4. 커스텀 도구 작성

#### 예시: 개인화된 키토 스코어 계산기
```python
# app/tools/meal/soobin_keto_score.py
"""
개인화된 키토 스코어 계산기
더 엄격한 기준과 개인 취향 반영
"""

from app.tools.meal.keto_score import KetoScoreCalculator

class SoobinKetoScoreCalculator(KetoScoreCalculator):
    """개인화된 키토 스코어 계산기"""
    
    def __init__(self):
        super().__init__()
        
        # 개인 취향 반영 - 더 엄격한 기준
        self.category_scores.update({
            "디저트": -50,    # 기본 -40에서 더 엄격하게
            "패스트푸드": -40,  # 더 엄격한 기준
            "한식": 25        # 한식을 더 선호
        })
        
        # 개인적으로 선호하는 키워드 추가
        self.positive_keywords["personal_favorites"] = [
            "삼계탕", "갈비탕", "육개장", "제육볶음"
        ]
    
    def calculate_score(self, name: str, category: str = "", **kwargs):
        """개인화된 점수 계산"""
        result = super().calculate_score(name, category, **kwargs)
        
        # 개인 취향 보너스 추가
        personal_bonus = self._calculate_personal_bonus(name, category)
        result["score"] = min(100, result["score"] + personal_bonus)
        
        if personal_bonus > 0:
            result["reasons"].append(f"개인 선호 메뉴 (+{personal_bonus})")
        
        return result
    
    def _calculate_personal_bonus(self, name: str, category: str) -> int:
        """개인 취향 보너스 계산"""
        name_lower = name.lower()
        
        # 개인적으로 좋아하는 메뉴들
        if any(fav in name_lower for fav in ["삼계", "갈비", "육개장"]):
            return 15
        
        # 건강한 조리법 선호
        if any(method in name_lower for method in ["찜", "무침", "나물"]):
            return 10
        
        return 0

# 기본 클래스와의 호환성
KetoScoreCalculator = SoobinKetoScoreCalculator
```

## 🔧 설정 시스템 작동 원리

### 1. 설정 로딩 순서
```python
# config_loader.py 동작 방식
def load_personal_config():
    # 1. .personal_config.py 확인 (최우선)
    # 2. personal_config.py 확인 (기본값)
    # 3. USE_PERSONAL_CONFIG = True인 경우만 로드
    # 4. 설정이 없으면 None 반환
```

### 2. 에이전트에서 설정 사용
```python
# agents/meal_planner.py
from config import get_personal_configs, get_agent_config

class MealPlannerAgent:
    def __init__(self):
        # 개인 설정 로드
        personal_configs = get_personal_configs()
        agent_config = get_agent_config("meal_planner", personal_configs)
        
        # 설정 적용
        self.agent_name = agent_config.get("agent_name", "기본 식단 에이전트")
        
        # 개인화된 프롬프트 로드
        self.prompts = self._load_custom_prompts(agent_config.get("prompts", {}))
        
        # 개인화된 도구 로드
        self.tools = self._load_custom_tools(agent_config.get("tools", {}))
```

### 3. 동적 모듈 로딩
```python
def _load_custom_prompts(self, prompt_config: Dict) -> Dict:
    """개인화된 프롬프트 동적 로딩"""
    custom_prompts = {}
    
    for prompt_type, file_name in prompt_config.items():
        try:
            # app/prompts/meal/soobin_custom_file.py 형태로 로드
            module_path = f"app.prompts.meal.{file_name}"
            module = importlib.import_module(module_path)
            
            # 프롬프트 상수 가져오기
            prompt_constant = getattr(module, f"{prompt_type.upper()}_PROMPT", None)
            if prompt_constant:
                custom_prompts[prompt_type] = prompt_constant
                print(f"✅ 개인화된 프롬프트 로드: {file_name}")
        
        except ImportError:
            print(f"⚠️ 개인화 프롬프트 없음: {file_name}, 기본값 사용")
    
    return custom_prompts
```

## 🔄 설정 관리 명령어

### 1. 설정 확인
```python
from config import get_personal_configs

# 현재 설정 확인
configs = get_personal_configs()
if configs:
    print("✅ 개인 설정이 활성화되어 있습니다")
    for agent, config in configs.items():
        print(f"  {agent}: {config.get('agent_name', '기본값')}")
else:
    print("ℹ️ 기본 설정을 사용하고 있습니다")
```

### 2. 설정 재로드
```python
from config import reload_personal_configs

# 설정 파일 수정 후 재로드
new_configs = reload_personal_configs()
print("🔄 설정이 재로드되었습니다")
```

## 🎯 개인화 예제

### 팀원별 특화 설정 예시

#### 수빈 - 상세한 기술 정보 선호
```python
MEAL_PLANNER_CONFIG = {
    "agent_name": "Tech-Savvy Keto Advisor",
    "prompts": {
        "generation": "soobin_detailed_generation"  # 영양소 상세 분석 포함
    }
}
```

#### 민수 - 간단하고 실용적인 접근
```python
MEAL_PLANNER_CONFIG = {
    "agent_name": "Simple Keto Helper",
    "prompts": {
        "generation": "minsu_simple_generation"  # 간단한 조리법 위주
    }
}
```

#### 지영 - 한식 전문가
```python
RESTAURANT_AGENT_CONFIG = {
    "agent_name": "한식 키토 마스터",
    "prompts": {
        "recommendation": "jiyoung_korean_specialist"  # 한식 위주 추천
    },
    "tools": {
        "place_search": "jiyoung_korean_search"  # 한식당 특화 검색
    }
}
```

## 🔒 보안 및 주의사항

### 1. .gitignore 설정
```gitignore
# 개인 설정 파일들
backend/config/.personal_config.py
backend/config/.*.py

# 개인화된 프롬프트/도구 파일들 (작성자이름_*.py 형태)
backend/app/prompts/**/soobin_*.py
backend/app/tools/**/soobin_*.py
backend/app/prompts/**/홍길동_*.py
backend/app/tools/**/홍길동_*.py
```

### 2. 설정 파일 보안
- API 키나 민감한 정보는 `.env` 파일 사용
- 개인 설정 파일은 절대 버전 관리에 포함하지 않음
- 팀 공유가 필요한 설정은 별도 문서화

### 3. 설정 검증
```python
def validate_personal_config(config: Dict) -> bool:
    """개인 설정 유효성 검사"""
    required_fields = ["agent_name"]
    
    for field in required_fields:
        if field not in config:
            print(f"❌ 필수 설정 누락: {field}")
            return False
    
    return True
```

## 🎯 Best Practices

1. **점진적 적용**: 한 번에 모든 것을 바꾸지 말고 필요한 부분부터
2. **백업**: 개인 설정 수정 전 백업 생성
3. **테스트**: 개인화 후 각 기능이 정상 작동하는지 확인
4. **문서화**: 개인 설정 변경 사항을 별도 문서로 관리
5. **공유**: 유용한 개인화 설정은 팀과 공유 (민감 정보 제외)
6. **일관성**: 개인 파일 명명 규칙을 일관되게 유지
7. **정리**: 사용하지 않는 개인화 파일은 주기적으로 정리

## 🚀 고급 활용

### 환경별 설정
```python
# .personal_config.py
import os

# 개발/운영 환경별 설정
if os.getenv("ENVIRONMENT") == "production":
    MEAL_PLANNER_CONFIG = {
        "agent_name": "Production Keto Agent",
        # 운영 환경 최적화 설정
    }
else:
    MEAL_PLANNER_CONFIG = {
        "agent_name": "Dev Keto Agent", 
        # 개발 환경 설정
    }
```

### 조건부 개인화
```python
# 특정 조건에서만 개인화 적용
import datetime

current_hour = datetime.datetime.now().hour

if 9 <= current_hour <= 17:  # 업무 시간
    CHAT_AGENT_CONFIG = {
        "agent_name": "Professional Keto Coach",
        "prompt_file_name": "professional_tone_chat"
    }
else:  # 개인 시간
    CHAT_AGENT_CONFIG = {
        "agent_name": "Friendly Keto Buddy",
        "prompt_file_name": "casual_tone_chat"
    }
```
