"""
식당 검색 및 추천 에이전트
키토 친화적 식당 검색과 개인화된 추천 시스템

팀원 개인화 가이드:
1. config/personal_config.py에서 RESTAURANT_AGENT_CONFIG 수정
2. 개인 프롬프트 파일을 restaurant/prompts/ 폴더에 생성
3. 개인 도구 파일을 restaurant/tools/ 폴더에 생성
4. USE_PERSONAL_CONFIG를 True로 설정하여 활성화
"""

from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
import importlib

from app.core.config import settings
from config import get_personal_configs, get_agent_config

class RestaurantAgent:
    """키토 친화적 식당 검색 및 추천 에이전트"""
    
    # 기본 설정 (개인 설정이 없을 때 사용)
    DEFAULT_AGENT_NAME = "Restaurant Agent"
    DEFAULT_PROMPT_FILES = {
        "search_improvement": "place_search_improvement",  # restaurant/prompts/ 폴더의 파일명
        "search_failure": "search_failure",
        "recommendation": "restaurant_recommendation"
    }
    DEFAULT_TOOL_FILES = {
        "place_search": "place_search"  # restaurant/tools/ 폴더의 파일명
    }
    
    def __init__(self, prompt_files: Dict[str, str] = None, tool_files: Dict[str, str] = None, agent_name: str = None):
        # 개인 설정 로드
        personal_configs = get_personal_configs()
        agent_config = get_agent_config("restaurant_agent", personal_configs)
        
        # 개인화된 설정 적용 (우선순위: 매개변수 > 개인설정 > 기본설정)
        self.prompt_files = prompt_files or agent_config.get("prompts", self.DEFAULT_PROMPT_FILES)
        self.tool_files = tool_files or agent_config.get("tools", self.DEFAULT_TOOL_FILES)
        self.agent_name = agent_name or agent_config.get("agent_name", self.DEFAULT_AGENT_NAME)
        
        # 동적 프롬프트 로딩
        self.prompts = self._load_prompts()
        
        # 동적 도구 로딩
        self.tools = self._load_tools()
        
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=settings.gemini_temperature,
                max_tokens=settings.gemini_max_tokens
            )
        except Exception as e:
            print(f"Gemini AI 초기화 실패: {e}")
            self.llm = None
    
    def _load_prompts(self) -> Dict[str, str]:
        """프롬프트 파일들 동적 로딩"""
        prompts = {}
        
        for key, filename in self.prompt_files.items():
            try:
                module_path = f"app.restaurant.prompts.{filename}"
                prompt_module = importlib.import_module(module_path)
                
                # 다양한 프롬프트 속성명 지원
                possible_names = [
                    f"{key.upper()}_PROMPT",
                    f"PLACE_{key.upper()}_PROMPT",
                    f"RESTAURANT_{key.upper()}_PROMPT",
                    "PROMPT",
                    filename.upper().replace("_", "_") + "_PROMPT"
                ]
                
                prompt_found = False
                for name in possible_names:
                    if hasattr(prompt_module, name):
                        prompts[key] = getattr(prompt_module, name)
                        prompt_found = True
                        break
                
                if not prompt_found:
                    print(f"경고: {filename}에서 프롬프트를 찾을 수 없습니다. 기본 프롬프트 사용.")
                    prompts[key] = self._get_default_prompt(key)
                    
            except ImportError:
                print(f"경고: {filename} 프롬프트 파일을 찾을 수 없습니다. 기본 프롬프트 사용.")
                prompts[key] = self._get_default_prompt(key)
        
        return prompts
    
    def _load_tools(self) -> Dict[str, Any]:
        """도구 파일들 동적 로딩"""
        tools = {}
        
        for key, filename in self.tool_files.items():
            try:
                module_path = f"app.restaurant.tools.{filename}"
                tool_module = importlib.import_module(module_path)
                
                # 클래스명 추정 (파일명을 CamelCase로 변환)
                class_name = "".join(word.capitalize() for word in filename.split("_"))
                
                if hasattr(tool_module, class_name):
                    tool_class = getattr(tool_module, class_name)
                    tools[key] = tool_class()
                else:
                    print(f"경고: {filename}에서 {class_name} 클래스를 찾을 수 없습니다.")
                    
            except ImportError:
                print(f"경고: {filename} 도구 파일을 찾을 수 없습니다.")
        
        return tools
    
    def _get_default_prompt(self, key: str) -> str:
        """기본 프롬프트 템플릿 (프롬프트 파일에서 로드)"""
        try:
            if key == "search_improvement":
                from app.restaurant.prompts.default_search_improvement import DEFAULT_SEARCH_IMPROVEMENT_PROMPT
                return DEFAULT_SEARCH_IMPROVEMENT_PROMPT
            elif key == "search_failure":
                from app.restaurant.prompts.default_search_failure import DEFAULT_SEARCH_FAILURE_PROMPT
                return DEFAULT_SEARCH_FAILURE_PROMPT
            elif key == "recommendation":
                from app.restaurant.prompts.default_recommendation import DEFAULT_RECOMMENDATION_PROMPT
                return DEFAULT_RECOMMENDATION_PROMPT
        except ImportError:
            pass
        
        # 폴백 프롬프트 파일에서 로드
        try:
            from app.restaurant.prompts.fallback_prompts import (
                FALLBACK_SEARCH_IMPROVEMENT_PROMPT,
                FALLBACK_SEARCH_FAILURE_PROMPT,
                FALLBACK_RECOMMENDATION_PROMPT
            )
            
            fallback_defaults = {
                "search_improvement": FALLBACK_SEARCH_IMPROVEMENT_PROMPT,
                "search_failure": FALLBACK_SEARCH_FAILURE_PROMPT,
                "recommendation": FALLBACK_RECOMMENDATION_PROMPT
            }
            
            return fallback_defaults.get(key, "프롬프트를 찾을 수 없습니다.")
            
        except ImportError:
            # 정말 마지막 폴백
            return f"키토 식당 {key} 작업을 수행하세요."
    
    async def search_restaurants(
        self,
        message: str,
        location: Dict[str, float],
        radius_km: float = 5.0,
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """식당 검색 메인 함수"""
        
        try:
            if not self.llm:
                return self._get_error_response("AI 서비스를 사용할 수 없습니다.")
            
            # 검색 키워드 개선
            improved_keywords = await self._improve_search_query(message)
            
            # 식당 검색 실행
            restaurants = await self._execute_search(improved_keywords, location, radius_km)
            
            if not restaurants:
                # 검색 실패 응답
                response = await self._generate_failure_response(message)
                return {
                    "response": response,
                    "restaurants": [],
                    "search_keywords": improved_keywords,
                    "tool_calls": [{"tool": "restaurant_search", "status": "no_results"}]
                }
            
            # 개인화된 추천 생성
            recommendation = await self._generate_recommendation(message, restaurants, profile)
            
            return {
                "response": recommendation,
                "restaurants": restaurants,
                "search_keywords": improved_keywords,
                "tool_calls": [{"tool": "restaurant_search", "results_count": len(restaurants)}]
            }
            
        except Exception as e:
            return self._get_error_response(f"식당 검색 중 오류 발생: {str(e)}")
    
    async def _improve_search_query(self, message: str) -> List[str]:
        """검색 쿼리 개선"""
        
        if "search_improvement" not in self.prompts:
            # 기본 키워드 추출
            return [message]
        
        try:
            prompt = self.prompts["search_improvement"].format(message=message)
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            # 키워드 추출
            keywords = [k.strip().strip('"') for k in response.content.split(",")]
            return keywords[:3]  # 최대 3개
            
        except Exception as e:
            print(f"검색 쿼리 개선 실패: {e}")
            return [message]
    
    async def _execute_search(
        self,
        keywords: List[str],
        location: Dict[str, float],
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """실제 식당 검색 실행"""
        
        if "place_search" not in self.tools:
            print("경고: place_search 도구를 찾을 수 없습니다.")
            return []
        
        try:
            search_tool = self.tools["place_search"]
            all_restaurants = []
            
            for keyword in keywords:
                restaurants = await search_tool.search(
                    query=keyword,
                    lat=location.get("lat", 37.4979),
                    lng=location.get("lng", 127.0276),
                    radius=int(radius_km * 1000)
                )
                
                all_restaurants.extend(restaurants)
            
            # 중복 제거
            unique_restaurants = {}
            for restaurant in all_restaurants:
                rest_id = restaurant.get("id", "")
                if rest_id not in unique_restaurants:
                    unique_restaurants[rest_id] = restaurant
            
            return list(unique_restaurants.values())[:10]  # 최대 10개
            
        except Exception as e:
            print(f"식당 검색 실행 실패: {e}")
            return []
    
    async def _generate_failure_response(self, message: str) -> str:
        """검색 실패 시 응답 생성"""
        
        if "search_failure" not in self.prompts:
            return "죄송합니다. 검색 결과를 찾을 수 없습니다. 다른 지역이나 키워드로 다시 시도해보세요."
        
        try:
            prompt = self.prompts["search_failure"].format(message=message)
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            print(f"실패 응답 생성 실패: {e}")
            return "검색 결과를 찾을 수 없습니다. 다시 시도해주세요."
    
    async def _generate_recommendation(
        self,
        message: str,
        restaurants: List[Dict[str, Any]],
        profile: Optional[Dict[str, Any]]
    ) -> str:
        """개인화된 추천 생성"""
        
        if "recommendation" not in self.prompts:
            # 기본 추천 응답
            return f"총 {len(restaurants)}개의 키토 친화적 식당을 찾았습니다."
        
        try:
            # 식당 정보 요약
            restaurant_summary = ""
            for i, restaurant in enumerate(restaurants[:5], 1):
                restaurant_summary += f"{i}. {restaurant.get('name', '이름 없음')}\n"
                restaurant_summary += f"   주소: {restaurant.get('address', '')}\n"
                if restaurant.get('keto_score'):
                    restaurant_summary += f"   키토 점수: {restaurant['keto_score']}\n"
            
            # 프로필 정보
            profile_text = ""
            if profile:
                allergies = profile.get("allergies", [])
                dislikes = profile.get("dislikes", [])
                if allergies:
                    profile_text += f"알레르기: {', '.join(allergies)}. "
                if dislikes:
                    profile_text += f"비선호 음식: {', '.join(dislikes)}. "
            
            prompt = self.prompts["recommendation"].format(
                message=message,
                restaurants=restaurant_summary,
                profile=profile_text if profile_text else "특별한 제약사항 없음"
            )
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            print(f"추천 생성 실패: {e}")
            return f"총 {len(restaurants)}개의 식당을 찾았습니다. 키토 식단에 적합한 곳들을 선별했습니다."
    
    def _get_error_response(self, error_message: str) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "response": error_message,
            "restaurants": [],
            "search_keywords": [],
            "tool_calls": [{"tool": "error", "message": error_message}]
        }
