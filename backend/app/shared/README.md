# Shared 모듈 🔄

프로젝트 전체에서 공통으로 사용되는 도구, 서비스, 모델을 관리하는 모듈입니다.

## 📁 폴더 구조

```
shared/
├── api/            # 공통 API 기능 (인증 등)
├── models/         # 공통 데이터 모델
├── services/       # 공통 서비스 (데이터베이스, 벡터DB 등)
├── tools/          # 공통 도구 (하이브리드 검색, RAG 등)
└── README.md       # 이 파일
```

## 🛠️ 공통 도구 개인화 가이드

### 하이브리드 검색 도구 커스터마이징

`tools/hybrid_search.py`의 검색 도구를 개인화하여 자신만의 검색 로직을 만들 수 있습니다.

#### 기본 사용법

```python
from app.shared.tools.hybrid_search import hybrid_search_tool

# 기본 검색
results = await hybrid_search_tool.search(
    query="키토 아이스크림 레시피",
    max_results=5
)

# 프로필 기반 검색
results = await hybrid_search_tool.search(
    query="저녁 메뉴",
    profile="알레르기: 견과류, 목표: 1500kcal",
    max_results=3
)
```

#### 개인화된 검색 도구 생성

```python
# tools/my_hybrid_search.py
from typing import List, Dict, Any, Optional
import numpy as np

class MyHybridSearchTool:
    """개인화된 하이브리드 검색 도구"""
    
    def __init__(self):
        # 개인 설정
        self.weight_semantic = 0.7  # 의미 검색 가중치
        self.weight_keyword = 0.3   # 키워드 검색 가중치
        self.personal_preferences = self._load_preferences()
    
    async def search(
        self,
        query: str,
        profile: str = "",
        max_results: int = 5,
        filter_criteria: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """개인화된 검색 실행"""
        
        # 1. 쿼리 전처리
        enhanced_query = self._enhance_query(query, profile)
        
        # 2. 의미 검색
        semantic_results = await self._semantic_search(enhanced_query)
        
        # 3. 키워드 검색
        keyword_results = await self._keyword_search(query)
        
        # 4. 개인화된 점수 계산
        combined_results = self._combine_and_score(
            semantic_results, 
            keyword_results,
            profile
        )
        
        # 5. 필터링 및 정렬
        filtered_results = self._apply_filters(combined_results, filter_criteria)
        
        return filtered_results[:max_results]
    
    def _enhance_query(self, query: str, profile: str) -> str:
        """개인 스타일에 맞게 쿼리 향상"""
        # 개인만의 쿼리 향상 로직
        enhanced = f"{query} {profile}"
        
        # 개인 선호도 반영
        if "단백질" in self.personal_preferences:
            enhanced += " 고단백"
        
        return enhanced
    
    def _combine_and_score(self, semantic_results, keyword_results, profile):
        """개인화된 점수 계산"""
        # 자신만의 점수 계산 알고리즘
        combined = {}
        
        # 의미 검색 결과 처리
        for result in semantic_results:
            result_id = result.get("id", "")
            combined[result_id] = {
                **result,
                "personal_score": self._calculate_personal_score(result, profile)
            }
        
        return list(combined.values())
    
    def _calculate_personal_score(self, result, profile):
        """개인 맞춤 점수 계산"""
        base_score = result.get("final_score", 0)
        
        # 개인 선호도 보정
        personal_bonus = 0
        
        # 예: 특정 키워드 선호
        if any(pref in result.get("title", "") for pref in self.personal_preferences):
            personal_bonus += 0.2
        
        # 알레르기 체크
        if profile and "알레르기" in profile:
            allergies = self._extract_allergies(profile)
            if any(allergy in result.get("ingredients", "") for allergy in allergies):
                personal_bonus -= 0.5  # 페널티
        
        return min(1.0, base_score + personal_bonus)
    
    def _load_preferences(self):
        """개인 선호도 로드"""
        return ["닭가슴살", "연어", "아보카도", "브로콜리"]
    
    def _extract_allergies(self, profile):
        """프로필에서 알레르기 정보 추출"""
        # 간단한 파싱 로직
        if "알레르기:" in profile:
            allergy_part = profile.split("알레르기:")[1].split(",")[0]
            return [item.strip() for item in allergy_part.split(",")]
        return []
```

### RAG 도구 커스터마이징

`tools/recipe_rag.py`를 개인화하여 자신만의 RAG 시스템을 구축할 수 있습니다.

```python
# tools/my_recipe_rag.py
from typing import List, Dict, Any
import chromadb

class MyRecipeRAG:
    """개인화된 레시피 RAG 시스템"""
    
    def __init__(self):
        self.client = chromadb.Client()
        self.collection_name = "my_keto_recipes"
        self.personal_weights = {
            "difficulty": 0.2,    # 난이도
            "time": 0.3,         # 조리시간
            "taste": 0.5         # 맛 선호도
        }
    
    async def search_recipes(
        self,
        query: str,
        dietary_restrictions: List[str] = None,
        max_cooking_time: int = None,
        difficulty_level: str = "any"
    ) -> List[Dict[str, Any]]:
        """개인화된 레시피 검색"""
        
        # 1. 벡터 검색
        vector_results = await self._vector_search(query)
        
        # 2. 개인 필터 적용
        filtered_results = self._apply_personal_filters(
            vector_results,
            dietary_restrictions,
            max_cooking_time,
            difficulty_level
        )
        
        # 3. 개인 선호도 점수 적용
        scored_results = self._apply_personal_scoring(filtered_results)
        
        return scored_results
    
    def _apply_personal_filters(self, results, restrictions, max_time, difficulty):
        """개인 맞춤 필터링"""
        filtered = []
        
        for result in results:
            # 식이 제한 확인
            if restrictions:
                if any(restriction in result.get("ingredients", "") for restriction in restrictions):
                    continue
            
            # 조리 시간 확인
            if max_time and result.get("cooking_time", 0) > max_time:
                continue
            
            # 난이도 확인
            if difficulty != "any" and result.get("difficulty") != difficulty:
                continue
            
            filtered.append(result)
        
        return filtered
    
    def _apply_personal_scoring(self, results):
        """개인 선호도 기반 점수 적용"""
        for result in results:
            personal_score = 0
            
            # 난이도 점수 (쉬운 것 선호)
            difficulty_map = {"easy": 1.0, "medium": 0.7, "hard": 0.3}
            difficulty_score = difficulty_map.get(result.get("difficulty", "medium"), 0.7)
            personal_score += difficulty_score * self.personal_weights["difficulty"]
            
            # 조리 시간 점수 (빠른 것 선호)
            time_score = max(0, 1.0 - (result.get("cooking_time", 30) / 60))
            personal_score += time_score * self.personal_weights["time"]
            
            # 맛 선호도 점수 (개인 취향)
            taste_score = self._calculate_taste_score(result)
            personal_score += taste_score * self.personal_weights["taste"]
            
            result["personal_score"] = personal_score
        
        # 개인 점수로 정렬
        return sorted(results, key=lambda x: x.get("personal_score", 0), reverse=True)
    
    def _calculate_taste_score(self, result):
        """개인 맛 선호도 점수"""
        favorite_flavors = ["매콤한", "고소한", "담백한"]
        
        taste_score = 0
        for flavor in favorite_flavors:
            if flavor in result.get("description", ""):
                taste_score += 0.3
        
        return min(1.0, taste_score)
```

## 🔧 서비스 개인화 가이드

### ChromaDB 서비스 커스터마이징

`services/chromadb_service.py`를 개인화하여 자신만의 벡터 데이터베이스 로직을 구현할 수 있습니다.

```python
# services/my_chromadb_service.py
import chromadb
from typing import List, Dict, Any
import uuid

class MyChromaDBService:
    """개인화된 ChromaDB 서비스"""
    
    def __init__(self):
        self.client = chromadb.Client()
        self.personal_collections = {}
        self.embedding_model = "my-preferred-model"
    
    def create_personal_collection(self, user_id: str, collection_type: str):
        """사용자별 개인 컬렉션 생성"""
        collection_name = f"{user_id}_{collection_type}_collection"
        
        collection = self.client.create_collection(
            name=collection_name,
            metadata={"user_id": user_id, "type": collection_type}
        )
        
        self.personal_collections[f"{user_id}_{collection_type}"] = collection
        return collection
    
    def add_personal_recipe(self, user_id: str, recipe_data: Dict[str, Any]):
        """개인 레시피 추가"""
        collection_key = f"{user_id}_recipes"
        
        if collection_key not in self.personal_collections:
            self.create_personal_collection(user_id, "recipes")
        
        collection = self.personal_collections[collection_key]
        
        # 개인 메타데이터 추가
        enhanced_metadata = {
            **recipe_data.get("metadata", {}),
            "user_id": user_id,
            "added_date": "2024-01-01",  # 실제로는 현재 날짜
            "personal_rating": recipe_data.get("rating", 0),
            "tried": recipe_data.get("tried", False)
        }
        
        collection.add(
            documents=[recipe_data["content"]],
            metadatas=[enhanced_metadata],
            ids=[str(uuid.uuid4())]
        )
    
    def search_personal_recipes(
        self,
        user_id: str,
        query: str,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """개인 레시피 검색"""
        collection_key = f"{user_id}_recipes"
        
        if collection_key not in self.personal_collections:
            return []
        
        collection = self.personal_collections[collection_key]
        
        # 개인 필터 적용
        where_clause = {"user_id": user_id}
        if filters:
            where_clause.update(filters)
        
        results = collection.query(
            query_texts=[query],
            n_results=10,
            where=where_clause
        )
        
        return self._format_results(results)
    
    def _format_results(self, raw_results):
        """검색 결과 포맷팅"""
        formatted = []
        
        for i, doc in enumerate(raw_results["documents"][0]):
            formatted.append({
                "id": raw_results["ids"][0][i],
                "content": doc,
                "metadata": raw_results["metadatas"][0][i],
                "distance": raw_results["distances"][0][i] if "distances" in raw_results else 0
            })
        
        return formatted
```

## 📊 공통 모델 확장 가이드

### 개인화된 데이터 모델

`models/schemas.py`를 확장하여 개인 맞춤 스키마를 정의할 수 있습니다.

```python
# models/my_schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PersonalRecipe(BaseModel):
    """개인 레시피 모델"""
    id: str
    title: str
    ingredients: List[str]
    instructions: List[str]
    macros: Dict[str, float]
    
    # 개인화 필드
    personal_rating: Optional[float] = Field(0, ge=0, le=10)
    tried_date: Optional[datetime] = None
    modifications: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    difficulty_personal: Optional[str] = None  # 개인적으로 느낀 난이도
    notes: Optional[str] = ""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PersonalMealPlan(BaseModel):
    """개인 식단표 모델"""
    id: str
    user_id: str
    week_start: datetime
    days: List[Dict[str, Any]]
    
    # 개인화 필드
    completion_rate: Optional[float] = 0  # 실제 따라한 비율
    satisfaction_score: Optional[float] = 0
    modifications_made: Optional[List[str]] = []
    next_week_preferences: Optional[Dict[str, Any]] = {}
    
class PersonalRestaurant(BaseModel):
    """개인 맛집 모델"""
    id: str
    name: str
    address: str
    category: str
    
    # 개인화 필드
    visited_dates: Optional[List[datetime]] = []
    personal_rating: Optional[float] = Field(0, ge=0, le=10)
    favorite_menus: Optional[List[str]] = []
    keto_friendly_level: Optional[int] = Field(5, ge=1, le=10)
    personal_notes: Optional[str] = ""
    recommended_by: Optional[str] = ""  # 추천인
    
class UserPreferences(BaseModel):
    """사용자 선호도 모델"""
    user_id: str
    
    # 식단 선호도
    preferred_cuisines: List[str] = []
    disliked_ingredients: List[str] = []
    allergies: List[str] = []
    
    # 키토 목표
    keto_strictness: str = "moderate"  # strict, moderate, flexible
    daily_carb_limit: int = 20
    daily_calorie_target: Optional[int] = None
    
    # 개인 스타일
    cooking_skill: str = "beginner"  # beginner, intermediate, advanced
    available_cooking_time: int = 30  # 분
    budget_level: str = "medium"  # low, medium, high
    
    # 검색 선호도
    search_weights: Dict[str, float] = {
        "taste": 0.4,
        "health": 0.3,
        "convenience": 0.2,
        "cost": 0.1
    }
```

## 🔐 인증 시스템 확장

### 개인화된 인증 서비스

```python
# api/my_auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Dict, Any

class PersonalAuthService:
    """개인화된 인증 서비스"""
    
    def __init__(self):
        self.security = HTTPBearer()
        self.secret_key = "your-personal-secret"
        self.algorithm = "HS256"
    
    def create_personal_token(self, user_data: Dict[str, Any]) -> str:
        """개인 맞춤 토큰 생성"""
        payload = {
            "user_id": user_data["id"],
            "preferences": user_data.get("preferences", {}),
            "subscription_level": user_data.get("subscription", "free"),
            "personal_features": user_data.get("features", [])
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_personal_token(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """개인 토큰 검증"""
        try:
            payload = jwt.decode(credentials.credentials, self.secret_key, algorithms=[self.algorithm])
            return {
                "user_id": payload["user_id"],
                "preferences": payload.get("preferences", {}),
                "features": payload.get("personal_features", [])
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 만료되었습니다")
        except jwt.JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다")
    
    def check_personal_permission(self, required_feature: str):
        """개인 권한 확인 데코레이터"""
        def decorator(current_user: dict = Depends(self.verify_personal_token)):
            if required_feature not in current_user.get("features", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{required_feature} 기능 사용 권한이 없습니다"
                )
            return current_user
        return decorator

# 사용 예시
personal_auth = PersonalAuthService()

@app.post("/api/personal/recipe")
async def create_personal_recipe(
    recipe_data: PersonalRecipe,
    current_user: dict = Depends(personal_auth.check_personal_permission("create_recipe"))
):
    # 개인 레시피 생성 로직
    pass
```

## 🎯 실용적인 활용 사례

### 1. 팀원별 전문 분야 도구

```python
# 팀원 A - 영양 분석 전문
class NutritionAnalyzer(MyHybridSearchTool):
    def __init__(self):
        super().__init__()
        self.weight_nutrition = 0.8  # 영양소 가중치 높임
        self.specialized_filters = ["protein_content", "vitamin_density"]

# 팀원 B - 한식 전문
class KoreanFoodSearchTool(MyHybridSearchTool):
    def __init__(self):
        super().__init__()
        self.korean_keywords = ["김치", "된장", "고추장", "젓갈"]
        self.regional_specialties = True

# 팀원 C - 베이킹 전문
class KetoBakingTool(MyRecipeRAG):
    def __init__(self):
        super().__init__()
        self.baking_specific_weights = {
            "texture": 0.4,
            "sweetness": 0.3,
            "appearance": 0.3
        }
```

### 2. 사용자 세그먼트별 서비스

```python
# 초보자용 서비스
class BeginnerKetoService(MyChromaDBService):
    def __init__(self):
        super().__init__()
        self.difficulty_filter = "easy"
        self.max_ingredients = 5
        self.simple_instructions = True

# 전문가용 서비스
class AdvancedKetoService(MyChromaDBService):
    def __init__(self):
        super().__init__()
        self.include_complex_recipes = True
        self.advanced_nutritional_analysis = True
        self.meal_timing_optimization = True
```

### 3. 지역별 맞춤 서비스

```python
# 서울 특화 서비스
class SeoulKetoService:
    def __init__(self):
        self.local_markets = ["남대문", "동대문", "가락시장"]
        self.delivery_zones = ["강남", "홍대", "명동"]
        self.local_specialties = ["한우", "곱창", "족발"]

# 부산 특화 서비스  
class BusanKetoService:
    def __init__(self):
        self.seafood_focus = True
        self.local_markets = ["자갈치", "부평깡통시장"]
        self.coastal_specialties = ["회", "조개구이", "대게"]
```

## 📚 개발자 가이드

### 1. 새로운 공통 도구 추가

```python
# tools/my_new_tool.py
class MyNewTool:
    """새로운 공통 도구"""
    
    def __init__(self):
        self.config = self._load_config()
    
    async def process(self, input_data):
        """메인 처리 로직"""
        result = await self._internal_process(input_data)
        return self._format_output(result)
    
    def _load_config(self):
        """설정 로드"""
        return {"key": "value"}
    
    async def _internal_process(self, data):
        """내부 처리"""
        return data
    
    def _format_output(self, result):
        """출력 포맷팅"""
        return {"status": "success", "data": result}

# __init__.py에 추가
from .my_new_tool import MyNewTool
my_new_tool = MyNewTool()
```

### 2. 공통 서비스 확장

```python
# services/my_service.py
from typing import Protocol

class SearchServiceProtocol(Protocol):
    async def search(self, query: str) -> List[Dict]: ...
    def filter_results(self, results: List[Dict], criteria: Dict) -> List[Dict]: ...

class MySearchService:
    """프로토콜을 구현한 검색 서비스"""
    
    async def search(self, query: str) -> List[Dict]:
        # 검색 구현
        return []
    
    def filter_results(self, results: List[Dict], criteria: Dict) -> List[Dict]:
        # 필터링 구현
        return results
```

### 3. 에러 처리 및 로깅

```python
# services/error_handler.py
import logging
from typing import Any, Callable
from functools import wraps

class PersonalErrorHandler:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.logger = logging.getLogger(f"user_{user_id}")
    
    def handle_errors(self, fallback_value: Any = None):
        """에러 처리 데코레이터"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Function {func.__name__} failed for user {self.user_id}: {e}")
                    
                    if fallback_value is not None:
                        return fallback_value
                    
                    # 사용자 친화적 에러 메시지
                    return {
                        "error": True,
                        "message": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "user_id": self.user_id
                    }
            return wrapper
        return decorator

# 사용 예시
error_handler = PersonalErrorHandler("user123")

@error_handler.handle_errors(fallback_value=[])
async def search_personal_recipes(query: str):
    # 검색 로직
    pass
```

## 🤝 협업 및 확장성

### 플러그인 시스템

```python
# plugin_system.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class KetoPlugin(ABC):
    """키토 플러그인 기본 인터페이스"""
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        pass
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class PluginManager:
    """플러그인 매니저"""
    
    def __init__(self):
        self.plugins: Dict[str, KetoPlugin] = {}
    
    def register_plugin(self, plugin: KetoPlugin):
        """플러그인 등록"""
        self.plugins[plugin.get_name()] = plugin
    
    async def execute_plugin(self, plugin_name: str, data: Dict[str, Any]):
        """플러그인 실행"""
        if plugin_name in self.plugins:
            return await self.plugins[plugin_name].process(data)
        raise ValueError(f"Plugin {plugin_name} not found")
    
    def list_plugins(self) -> List[str]:
        """등록된 플러그인 목록"""
        return list(self.plugins.keys())

# 플러그인 예시
class NutritionAnalysisPlugin(KetoPlugin):
    def get_name(self) -> str:
        return "nutrition_analysis"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # 영양 분석 로직
        return {"nutrition_score": 8.5, "recommendations": ["더 많은 채소 섭취"]}
```

---

💡 **새로운 공통 도구나 서비스 아이디어가 있다면 팀과 논의하여 shared 모듈에 추가해주세요!**
