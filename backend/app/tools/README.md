# 🛠️ Tools (중앙집중화 도구)

모든 도메인의 유틸리티 도구들을 중앙에서 관리하는 폴더입니다.

## 📁 구조

```
tools/
├── meal/              # 식단 관련 도구
│   ├── keto_score.py              # 키토 친화도 점수 계산
│   ├── korean_search.py           # 한글 최적화 검색
│   └── recipe_response_formatter.py # 레시피 응답 포맷팅
├── restaurant/        # 식당 관련 도구
│   └── place_search.py            # 카카오 로컬 API 장소 검색
└── shared/            # 공통 도구
    ├── hybrid_search.py           # 하이브리드 검색 (벡터+키워드)
    └── recipe_rag.py             # 레시피 RAG 검색
```

## 🎯 도구별 설명

### 🥗 Meal Tools

#### `keto_score.py` - 키토 친화도 계산기
```python
from app.tools.meal.keto_score import KetoScoreCalculator

calculator = KetoScoreCalculator()
result = calculator.calculate_score(
    name="삼겹살구이",
    category="한식",
    description="고기구이 전문점"
)
# result: {"score": 85, "reasons": [...], "tips": [...]}
```

#### `korean_search.py` - 한글 최적화 검색
```python
from app.tools.meal.korean_search import korean_search_tool

results = await korean_search_tool.korean_hybrid_search("김치찌개", k=5)
# 벡터 + Full-Text + Trigram 검색 통합
```

#### `recipe_response_formatter.py` - 레시피 응답 포맷터
```python
from app.tools.meal.recipe_response_formatter import RecipeResponseFormatter

formatter = RecipeResponseFormatter()
response = await formatter.format_hybrid_response(
    message="키토 김치찌개",
    recipes=search_results,
    profile_context="알레르기: 없음"
)
```

### 🏪 Restaurant Tools

#### `place_search.py` - 장소 검색 도구
```python
from app.tools.restaurant.place_search import PlaceSearchTool

search_tool = PlaceSearchTool()
places = await search_tool.search(
    query="스테이크",
    lat=37.5665,
    lng=126.9780,
    radius=1000
)
```

### 🔄 Shared Tools

#### `hybrid_search.py` - 하이브리드 검색
```python
from app.tools.shared.hybrid_search import hybrid_search_tool

results = await hybrid_search_tool.search(
    query="키토 레시피",
    profile="알레르기: 견과류",
    max_results=5
)
```

#### `recipe_rag.py` - 레시피 RAG 검색
```python
from app.tools.shared.recipe_rag import recipe_rag_tool

results = await recipe_rag_tool.search_recipes(
    query="아침식사 레시피",
    profile="키토식단",
    max_results=3
)
```

## 🔧 도구 개발 가이드

### 1. 새 도구 만들기

#### 파일 구조
```python
"""
도구 설명 및 용도
"""

import asyncio
from typing import List, Dict, Any, Optional

class MyCustomTool:
    """도구 클래스 설명"""
    
    def __init__(self):
        """초기화"""
        pass
    
    async def main_function(self, param1: str, param2: int) -> Dict[str, Any]:
        """주요 기능"""
        try:
            # 도구 로직 구현
            result = self._process(param1, param2)
            return {"success": True, "data": result}
        
        except Exception as e:
            print(f"❌ {self.__class__.__name__} 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def _process(self, param1: str, param2: int) -> Any:
        """내부 처리 로직"""
        # 구현
        pass

# 전역 인스턴스 (선택사항)
my_custom_tool = MyCustomTool()
```

### 2. 도구 명명 규칙

#### 파일명
- `작성자이름_purpose.py` (예: `soobin_keto_score.py`)
- 기능을 명확히 표현하는 이름

#### 클래스명
- `PascalCase` + "Tool" 접미사 (예: `KetoScoreCalculator`, `PlaceSearchTool`)

#### 함수명
- `snake_case` (예: `calculate_score`, `search_recipes`)
- 동사로 시작 (search, calculate, format, parse 등)

### 3. 비동기 처리
외부 API나 DB 연결이 있는 도구는 비동기로 구현:

```python
async def search(self, query: str) -> List[Dict]:
    """비동기 검색"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"api/search?q={query}")
        return response.json()
```

### 4. 에러 처리
```python
try:
    result = await external_api_call()
    return {"success": True, "data": result}
except httpx.HTTPError as e:
    print(f"❌ API 에러: {e}")
    return {"success": False, "error": "API 연결 실패"}
except Exception as e:
    print(f"❌ 예상치 못한 오류: {e}")
    return {"success": False, "error": str(e)}
```

## 🔄 Integration with Agents

도구들은 주로 에이전트에서 사용됩니다:

```python
# agents/meal_planner.py
from app.tools.meal.keto_score import KetoScoreCalculator
from app.tools.shared.hybrid_search import hybrid_search_tool

class MealPlannerAgent:
    def __init__(self):
        self.keto_calculator = KetoScoreCalculator()
        self.search_tool = hybrid_search_tool
    
    async def plan_meal(self, requirements: str):
        # 도구 사용
        recipes = await self.search_tool.search(requirements)
        scores = [self.keto_calculator.calculate_score(r) for r in recipes]
        return self._format_plan(recipes, scores)
```

## 🧪 테스트

### 단위 테스트 예시
```python
import pytest
from app.tools.meal.keto_score import KetoScoreCalculator

@pytest.fixture
def calculator():
    return KetoScoreCalculator()

def test_keto_score_calculation(calculator):
    result = calculator.calculate_score(
        name="삼겹살구이",
        category="고기요리"
    )
    
    assert result["score"] > 70  # 키토 친화적
    assert "reasons" in result
    assert "tips" in result
```

## 🚀 성능 최적화

### 1. 캐싱
자주 사용되는 결과는 캐싱:

```python
from functools import lru_cache

class MyTool:
    @lru_cache(maxsize=100)
    def expensive_calculation(self, param: str) -> str:
        # 비용이 많이 드는 계산
        return result
```

### 2. 배치 처리
여러 항목을 한 번에 처리:

```python
async def batch_process(self, items: List[str]) -> List[Dict]:
    """배치 처리로 효율성 향상"""
    tasks = [self.process_item(item) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

## 🛠️ 유지보수

### 1. 로깅
```python
import logging

logger = logging.getLogger(__name__)

class MyTool:
    async def process(self, data):
        logger.info(f"🔧 {self.__class__.__name__} 처리 시작: {data}")
        try:
            result = await self._process(data)
            logger.info(f"✅ 처리 완료: {len(result)}개 결과")
            return result
        except Exception as e:
            logger.error(f"❌ 처리 실패: {e}")
            raise
```

### 2. 설정 관리
```python
from app.core.config import settings

class MyTool:
    def __init__(self):
        self.api_key = settings.my_api_key
        self.timeout = settings.request_timeout
```

## 🎯 Best Practices

1. **단일 책임**: 각 도구는 하나의 명확한 역할만
2. **재사용성**: 여러 에이전트에서 사용 가능하도록 설계
3. **에러 처리**: 모든 외부 의존성에 대한 에러 처리
4. **비동기**: I/O 작업은 비동기로 구현
5. **테스트 가능**: 단위 테스트가 쉽도록 설계
6. **문서화**: docstring과 타입 힌트 필수
7. **성능**: 필요시 캐싱과 배치 처리 적용
