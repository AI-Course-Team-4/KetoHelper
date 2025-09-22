# 🤖 Agents (중앙집중화 에이전트)

모든 도메인의 AI 에이전트들을 중앙에서 관리하는 폴더입니다.

## 📁 구조

```
agents/
├── chat_agent.py          # 일반 채팅 에이전트
├── meal_planner.py        # 식단 계획 에이전트
└── restaurant_agent.py    # 식당 추천 에이전트
```

## 🎯 에이전트별 설명

### 💬 Chat Agent (`chat_agent.py`)
일반적인 키토 식단 상담을 담당하는 에이전트

**주요 기능:**
- 키토 식단 기본 상담
- 일반적인 질문 응답
- 사용자 의도에 따른 전문 에이전트 라우팅

**사용 예시:**
```python
from app.agents.chat_agent import SimpleKetoCoachAgent

agent = SimpleKetoCoachAgent()
response = await agent.process_message(
    message="키토 식단 시작하는 방법 알려줘",
    profile_context="키토 초보자"
)
```

### 🍽️ Meal Planner (`meal_planner.py`)
키토 식단표 생성 및 레시피 추천 에이전트

**주요 기능:**
- 7일 키토 식단표 자동 생성
- 개별 레시피 검색 및 생성
- 사용자 프로필 기반 맞춤 추천
- 영양 정보 계산 및 조언

**사용 예시:**
```python
from app.agents.meal_planner import MealPlannerAgent

agent = MealPlannerAgent()

# 식단표 생성
meal_plan = await agent.create_meal_plan(
    days=7,
    constraints="1일 탄수화물 20g 이하",
    profile_context="알레르기: 견과류"
)

# 단일 레시피 생성
recipe = await agent.generate_single_recipe(
    message="키토 김치찌개",
    profile_context="매운 음식 선호"
)
```

### 🏪 Restaurant Agent (`restaurant_agent.py`)
키토 친화적 식당 검색 및 추천 에이전트

**주요 기능:**
- 위치 기반 식당 검색
- 키토 친화도 점수 계산
- 개인화된 식당 추천
- 메뉴 주문 팁 제공

**사용 예시:**
```python
from app.agents.restaurant_agent import RestaurantAgent

agent = RestaurantAgent()
recommendations = await agent.recommend_restaurants(
    message="강남역 근처 키토 식당 추천해줘",
    lat=37.4979,
    lng=127.0276,
    profile="알레르기: 해산물"
)
```

## 🔧 에이전트 개발 가이드

### 1. 에이전트 구조

#### 기본 템플릿
```python
"""
에이전트 설명 및 용도
"""

from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

from app.core.config import settings
from app.prompts.domain.prompt_file import MAIN_PROMPT
from app.tools.domain.tool_file import SomeTool

class MyCustomAgent:
    """커스텀 에이전트 클래스"""
    
    def __init__(self, agent_name: str = "My Custom Agent"):
        """에이전트 초기화"""
        self.agent_name = agent_name
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=0.1,
            google_api_key=settings.google_api_key
        )
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """도구 초기화"""
        return {
            "tool_name": SomeTool()
        }
    
    async def process_request(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """주요 처리 메서드"""
        try:
            # 1. 입력 전처리
            processed_input = self._preprocess_input(message, context)
            
            # 2. 도구 사용 (필요시)
            tool_results = await self._use_tools(processed_input)
            
            # 3. AI 응답 생성
            response = await self._generate_response(processed_input, tool_results)
            
            # 4. 후처리
            final_response = self._postprocess_response(response)
            
            return final_response
            
        except Exception as e:
            print(f"❌ {self.agent_name} 오류: {e}")
            return self._get_fallback_response(message)
    
    def _preprocess_input(self, message: str, context: Dict) -> Dict[str, Any]:
        """입력 전처리"""
        return {
            "message": message.strip(),
            "context": context or {},
            "timestamp": datetime.now()
        }
    
    async def _use_tools(self, input_data: Dict) -> Dict[str, Any]:
        """도구 사용"""
        results = {}
        
        # 필요한 도구들 실행
        if self._should_use_tool("search", input_data):
            results["search"] = await self.tools["search"].search(
                input_data["message"]
            )
        
        return results
    
    async def _generate_response(self, input_data: Dict, tool_results: Dict) -> str:
        """AI 응답 생성"""
        prompt = MAIN_PROMPT.format(
            message=input_data["message"],
            context=input_data["context"],
            tool_results=tool_results
        )
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content
    
    def _postprocess_response(self, response: str) -> str:
        """응답 후처리"""
        # 응답 검증, 포맷팅 등
        return response.strip()
    
    def _get_fallback_response(self, message: str) -> str:
        """폴백 응답"""
        return f"죄송합니다. '{message}'에 대한 처리 중 오류가 발생했습니다."
    
    def _should_use_tool(self, tool_name: str, input_data: Dict) -> bool:
        """도구 사용 여부 판단"""
        # 조건에 따른 도구 사용 결정 로직
        return True
```

### 2. 개인화 지원

에이전트는 개인 설정을 지원합니다:

```python
from config import get_personal_configs, get_agent_config

class MyAgent:
    def __init__(self):
        # 개인 설정 로드
        personal_configs = get_personal_configs()
        agent_config = get_agent_config("my_agent", personal_configs)
        
        # 개인 설정 적용
        self.agent_name = agent_config.get("agent_name", "Default Agent")
        self.custom_prompts = self._load_custom_prompts(agent_config)
        self.custom_tools = self._load_custom_tools(agent_config)
```

### 3. 에러 처리 및 폴백

```python
async def process_request(self, message: str) -> str:
    try:
        # 메인 처리 로직
        return await self._main_process(message)
        
    except APIError as e:
        print(f"🌐 API 오류: {e}")
        return await self._api_fallback(message)
        
    except ValidationError as e:
        print(f"📝 입력 검증 오류: {e}")
        return self._validation_fallback(message)
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return self._general_fallback(message)

def _api_fallback(self, message: str) -> str:
    """API 오류 시 폴백"""
    from app.prompts.domain.fallback import API_FALLBACK_PROMPT
    return API_FALLBACK_PROMPT.format(message=message)
```

## 🔄 에이전트 간 통신

### 1. Orchestrator를 통한 라우팅
```python
# core/orchestrator.py에서 에이전트 간 통신 관리
from app.agents.chat_agent import SimpleKetoCoachAgent
from app.agents.meal_planner import MealPlannerAgent
from app.agents.restaurant_agent import RestaurantAgent

class Orchestrator:
    def __init__(self):
        self.chat_agent = SimpleKetoCoachAgent()
        self.meal_agent = MealPlannerAgent()
        self.restaurant_agent = RestaurantAgent()
    
    async def route_request(self, intent: str, message: str) -> str:
        if intent == "recipe":
            return await self.meal_agent.generate_single_recipe(message)
        elif intent == "place":
            return await self.restaurant_agent.search_restaurants(message)
        else:
            return await self.chat_agent.process_message(message)
```

### 2. 에이전트 간 데이터 공유
```python
class SharedContext:
    """에이전트 간 공유되는 컨텍스트"""
    def __init__(self):
        self.user_profile = {}
        self.conversation_history = []
        self.session_data = {}

# 에이전트에서 사용
async def process_with_context(self, message: str, shared_context: SharedContext):
    # 공유 컨텍스트 활용
    user_preferences = shared_context.user_profile.get("preferences", [])
    # 처리 로직...
```

## 🧪 테스트

### 단위 테스트
```python
import pytest
from app.agents.meal_planner import MealPlannerAgent

@pytest.fixture
def meal_agent():
    return MealPlannerAgent()

@pytest.mark.asyncio
async def test_recipe_generation(meal_agent):
    response = await meal_agent.generate_single_recipe(
        message="키토 김치찌개",
        profile_context="알레르기: 없음"
    )
    
    assert "김치찌개" in response
    assert "키토" in response
    assert len(response) > 100  # 충분한 길이의 응답
```

### 통합 테스트
```python
@pytest.mark.asyncio
async def test_agent_integration():
    orchestrator = Orchestrator()
    
    # 의도 분류 테스트
    intent = await orchestrator.classify_intent("키토 김치찌개 만들어줘")
    assert intent == "recipe"
    
    # 에이전트 라우팅 테스트
    response = await orchestrator.route_request(intent, "키토 김치찌개")
    assert response is not None
```

## 🚀 성능 최적화

### 1. 응답 스트리밍
```python
async def stream_response(self, message: str):
    """실시간 응답 스트리밍"""
    async for chunk in self.llm.astream([HumanMessage(content=message)]):
        yield chunk.content
```

### 2. 캐싱
```python
from functools import lru_cache

class MyAgent:
    @lru_cache(maxsize=100)
    def _get_prompt_template(self, prompt_type: str) -> str:
        """프롬프트 템플릿 캐싱"""
        return self._load_prompt(prompt_type)
```

### 3. 배치 처리
```python
async def process_batch_requests(self, requests: List[str]) -> List[str]:
    """여러 요청을 배치로 처리"""
    tasks = [self.process_request(req) for req in requests]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in responses if not isinstance(r, Exception)]
```

## 📊 모니터링 및 로깅

### 에이전트 성능 추적
```python
import time
import logging

logger = logging.getLogger(__name__)

class MyAgent:
    async def process_request(self, message: str) -> str:
        start_time = time.time()
        
        try:
            logger.info(f"🤖 {self.agent_name} 요청 처리 시작: {message[:50]}...")
            
            response = await self._main_process(message)
            
            duration = time.time() - start_time
            logger.info(f"✅ 처리 완료 ({duration:.2f}s): {len(response)} chars")
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ 처리 실패 ({duration:.2f}s): {e}")
            raise
```

## 🎯 Best Practices

1. **단일 책임**: 각 에이전트는 명확한 도메인 담당
2. **상태 관리**: 필요시 대화 컨텍스트 유지
3. **에러 처리**: 모든 예외 상황에 대한 적절한 폴백
4. **성능**: 비동기 처리와 캐싱 활용
5. **확장성**: 새로운 기능 추가가 쉽도록 설계
6. **테스트**: 단위/통합 테스트로 품질 보장
7. **모니터링**: 성능과 오류 추적
8. **개인화**: 팀원별 커스터마이징 지원

## 🔧 설정 관리

에이전트 개인화는 `backend/config/personal_config.py`에서 관리:

```python
# config/personal_config.py
MEAL_PLANNER_CONFIG = {
    "agent_name": "My Custom Meal Agent",
    "prompts": {
        "structure": "my_custom_structure",
        "generation": "my_custom_generation"
    },
    "tools": {
        "keto_score": "my_custom_keto_score"
    }
}
```

자세한 설정 방법은 `backend/config/README.md`를 참고하세요.
