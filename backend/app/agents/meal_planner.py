"""
식단표 생성 에이전트
AI 기반 7일 키토 식단 계획 생성

팀원 개인화 가이드:
1. config/personal_config.py에서 MEAL_PLANNER_CONFIG 수정
2. 개인 프롬프트 파일을 meal/prompts/ 폴더에 생성
3. 개인 도구 파일을 meal/tools/ 폴더에 생성
4. USE_PERSONAL_CONFIG를 True로 설정하여 활성화
"""

import asyncio
import json
import random
from typing import Dict, Any, List, Optional
from datetime import date, timedelta
from langchain.schema import HumanMessage
import importlib

from app.tools.shared.hybrid_search import hybrid_search_tool
from app.tools.shared.profile_tool import user_profile_tool
from app.tools.shared.date_parser import DateParser
from app.tools.shared.temporary_dislikes_extractor import temp_dislikes_extractor
from app.tools.meal.response_formatter import MealResponseFormatter
from app.core.llm_factory import create_chat_llm
from config import get_personal_configs, get_agent_config

# 기본값 상수 정의
DEFAULT_MEAL_PLAN_DAYS = 7

class MealPlannerAgent:
    """7일 키토 식단표 생성 에이전트"""
    
    # 기본 설정 (개인 설정이 없을 때 사용)
    DEFAULT_AGENT_NAME = "Meal Planner Agent"
    DEFAULT_PROMPT_FILES = {
        "structure": "structure",  # meal/prompts/ 폴더의 파일명
        "generation": "generation",
        "notes": "notes",
        "embedding_based": "embedding_based",  # 임베딩 데이터 기반 프롬프트
        "search_query": "embedding_based",  # AI 검색 쿼리 생성 프롬프트
        "search_strategy": "embedding_based"  # AI 검색 전략 생성 프롬프트
    }
    DEFAULT_TOOL_FILES = {
        "keto_score": "keto_score"  # meal/tools/ 폴더의 파일명
    }
    
    def __init__(self, prompt_files: Dict[str, str] = None, tool_files: Dict[str, str] = None, agent_name: str = None):
        # 개인 설정 로드
        personal_configs = get_personal_configs()
        agent_config = get_agent_config("meal_planner", personal_configs)
        
        # 개인화된 설정 적용 (우선순위: 매개변수 > 개인설정 > 기본설정)
        self.prompt_files = prompt_files or agent_config.get("prompts", self.DEFAULT_PROMPT_FILES)
        self.tool_files = tool_files or agent_config.get("tools", self.DEFAULT_TOOL_FILES) 
        self.agent_name = agent_name or agent_config.get("agent_name", self.DEFAULT_AGENT_NAME)
        
        # 동적 프롬프트 로딩
        self.prompts = self._load_prompts()
        
        # 동적 도구 로딩
        self.tools = self._load_tools()
        
        try:
            self.llm = create_chat_llm()
        except Exception as e:
            print(f"LLM 초기화 실패: {e}")
            self.llm = None
        
        
        # 새로운 도구들 초기화
        self.date_parser = DateParser()
        self.response_formatter = MealResponseFormatter()
        self.temp_dislikes_extractor = temp_dislikes_extractor
        
        # 벡터 검색 도구 초기화
        try:
            from app.tools.meal.korean_search import KoreanSearchTool
            self.korean_search_tool = KoreanSearchTool()
        except ImportError as e:
            print(f"KoreanSearchTool 초기화 실패: {e}")
            self.korean_search_tool = None
    
    def _load_prompts(self) -> Dict[str, str]:
        """프롬프트 파일들 동적 로딩"""
        prompts = {}
        
        for key, filename in self.prompt_files.items():
            try:
                module_path = f"app.prompts.meal.{filename}"
                prompt_module = importlib.import_module(module_path)
                
                # 다양한 프롬프트 속성명 지원
                possible_names = [
                    f"{key.upper()}_PROMPT",
                    f"MEAL_{key.upper()}_PROMPT", 
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
                module_path = f"app.tools.meal.{filename}"
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
            if key == "structure":
                from app.prompts.meal.structure import DEFAULT_STRUCTURE_PROMPT
                return DEFAULT_STRUCTURE_PROMPT
            elif key == "generation":
                from app.prompts.meal.generation import DEFAULT_GENERATION_PROMPT
                return DEFAULT_GENERATION_PROMPT
            elif key == "notes":
                from app.prompts.meal.notes import DEFAULT_NOTES_PROMPT
                return DEFAULT_NOTES_PROMPT
            elif key == "embedding_based":
                from app.prompts.meal.embedding_based import EMBEDDING_MEAL_PLAN_PROMPT
                return EMBEDDING_MEAL_PLAN_PROMPT
            elif key == "search_query":
                from app.prompts.meal.embedding_based import AI_SEARCH_QUERY_GENERATION_PROMPT
                return AI_SEARCH_QUERY_GENERATION_PROMPT
            elif key == "search_strategy":
                from app.prompts.meal.embedding_based import AI_MEAL_SEARCH_STRATEGY_PROMPT
                return AI_MEAL_SEARCH_STRATEGY_PROMPT
        except ImportError:
            pass
        
        # 최종 폴백 - 폴백 프롬프트 파일에서 로드
        try:
            from app.prompts.meal.fallback import (
                FALLBACK_STRUCTURE_PROMPT,
                FALLBACK_GENERATION_PROMPT, 
                FALLBACK_NOTES_PROMPT
            )
            
            fallback_defaults = {
                "structure": FALLBACK_STRUCTURE_PROMPT,
                "generation": FALLBACK_GENERATION_PROMPT,
                "notes": FALLBACK_NOTES_PROMPT,
                "embedding_based": FALLBACK_STRUCTURE_PROMPT  # 임베딩 기반은 구조 프롬프트 사용
            }
            
            try:
                from app.prompts.meal.fallback import PROMPT_NOT_FOUND_MESSAGE
                return fallback_defaults.get(key, PROMPT_NOT_FOUND_MESSAGE)
            except ImportError:
                return fallback_defaults.get(key, "프롬프트를 찾을 수 없습니다.")
            
        except ImportError:
            # 정말 마지막 폴백
            try:
                from app.prompts.meal.fallback import FINAL_FALLBACK_PROMPT
                return FINAL_FALLBACK_PROMPT.format(key=key)
            except ImportError:
                return f"키토 {key} 작업을 수행하세요."
    
    async def generate_meal_plan(
        self,
        days: int = 7,
        kcal_target: Optional[int] = None,
        carbs_max: int = 30,
        allergies: List[str] = None,
        dislikes: List[str] = None,
        user_id: Optional[str] = None,
        fast_mode: bool = True  # 빠른 모드 기본 활성화
    ) -> Dict[str, Any]:
        """
        7일 키토 식단표 생성 (임베딩 데이터 우선 → AI 생성 폴백)
        
        Args:
            days: 생성할 일수 (기본 7일)
            kcal_target: 목표 칼로리 (일일)
            carbs_max: 최대 탄수화물 (일일, g)
            allergies: 알레르기 목록
            dislikes: 비선호 음식 목록
            user_id: 사용자 ID (제공되면 자동으로 프로필에서 선호도 정보 가져옴)
            fast_mode: 빠른 모드 (AI 호출 최소화, 기본 True)
        
        Returns:
            생성된 식단표 데이터
        """
        
        try:
            # 사용자 ID가 제공되면 프로필에서 선호도 정보 가져오기
            if user_id:
                profile_result = await user_profile_tool.get_user_preferences(user_id)
                if profile_result["success"]:
                    prefs = profile_result["preferences"]
                    
                    # 프로필에서 가져온 정보가 매개변수보다 우선하지 않음 (매개변수가 우선)
                    if kcal_target is None and prefs.get("goals_kcal"):
                        kcal_target = prefs["goals_kcal"]
                    
                    if carbs_max == 30 and prefs.get("goals_carbs_g"):  # 기본값일 때만 덮어씀
                        carbs_max = prefs["goals_carbs_g"]
                    
                    if allergies is None and prefs.get("allergies"):
                        allergies = prefs["allergies"]
                    
                    if dislikes is None and prefs.get("dislikes"):
                        dislikes = prefs["dislikes"]
                    
                    print(f"🔧 사용자 프로필 적용 완료: 목표 {kcal_target}kcal, 탄수화물 {carbs_max}g, 알레르기 {len(allergies or [])}개, 비선호 {len(dislikes or [])}개")
                else:
                    print(f"⚠️ 사용자 프로필 조회 실패: {profile_result.get('error', '알 수 없는 오류')}")
            
            # 제약 조건 텍스트 생성
            constraints_text = self._build_constraints_text(
                kcal_target, carbs_max, allergies, dislikes
            )
            
            # 1단계: 임베딩된 데이터에서 식단표 생성 시도
            print("🔍 1단계: 임베딩된 레시피 데이터에서 식단표 생성 시도")
            embedded_plan = await self._generate_meal_plan_from_embeddings(days, constraints_text, user_id, fast_mode,
                                                                          allergies=allergies, dislikes=dislikes)
            
            if embedded_plan and len(embedded_plan.get("days", [])) > 0:
                print(f"✅ 임베딩 데이터로 식단표 생성 성공: {len(embedded_plan['days'])}일")
                return embedded_plan
            
            # 2단계: 임베딩 데이터로 부족하면 AI 생성
            print("🤖 2단계: AI로 식단표 구조 생성")
            meal_structure = await self._plan_meal_structure(days, constraints_text)
            
            # 3단계: AI 구조를 바탕으로 임베딩 데이터에서 구체적 메뉴 검색
            print("🔍 3단계: AI 구조 + 임베딩 데이터로 구체적 메뉴 생성")
            detailed_plan = await self._generate_detailed_meals_from_embeddings(meal_structure, constraints_text, user_id, fast_mode,
                                                                                allergies=allergies, dislikes=dislikes)
            
            if detailed_plan and len(detailed_plan.get("days", [])) > 0:
                print(f"✅ AI + 임베딩 데이터로 식단표 생성 성공: {len(detailed_plan['days'])}일")
                return detailed_plan
            
            # 4단계: 최종 폴백 - 간단한 AI 생성
            print("🔄 4단계: 최종 폴백 - 간단한 AI 생성")
            simple_plan = []
            for day_plan in meal_structure:
                day_meals = {
                    "breakfast": {"title": day_plan.get("breakfast_type", "아침 메뉴"), "type": "simple"},
                    "lunch": {"title": day_plan.get("lunch_type", "점심 메뉴"), "type": "simple"},
                    "dinner": {"title": day_plan.get("dinner_type", "저녁 메뉴"), "type": "simple"},
                    "snack": {"title": day_plan.get("snack_type", "간식"), "type": "simple"}
                }
                simple_plan.append(day_meals)
            
            # 기본 조언 생성 (notes.py 프롬프트 사용)
            notes = await self._generate_meal_notes(simple_plan, constraints_text)
            
            return {
                "days": simple_plan,
                "duration_days": days,  # 요청된 일수 정보 추가
                "total_macros": {
                    "kcal": 0,
                    "carb": 0,
                    "protein": 0,
                    "fat": 0
                },
                "notes": notes + ["⚠️ 간단 버전에서는 영양 계산이 제외됩니다"],
                "constraints": {
                    "kcal_target": kcal_target,
                    "carbs_max": carbs_max,
                    "allergies": allergies or [],
                    "dislikes": dislikes or []
                }
            }
            
        except Exception as e:
            print(f"Meal planning error: {e}")
            return await self._generate_fallback_plan(days)
    
    def _build_constraints_text(
        self,
        kcal_target: Optional[int],
        carbs_max: int,
        allergies: Optional[List[str]],
        dislikes: Optional[List[str]]
    ) -> str:
        """제약 조건을 텍스트로 변환"""
        
        constraints = []
        
        if kcal_target:
            constraints.append(f"일일 목표 칼로리: {kcal_target}kcal")
        
        constraints.append(f"일일 최대 탄수화물: {carbs_max}g")
        
        if allergies:
            constraints.append(f"알레르기: {', '.join(allergies)}")
        
        if dislikes:
            constraints.append(f"비선호 음식: {', '.join(dislikes)}")
        
        return " | ".join(constraints)
    
    async def _search_with_diversity(
        self,
        search_query: str,
        constraints: str,
        user_id: Optional[str],
        used_recipes: set,
        max_results: int = 35,
        allergies: Optional[List[str]] = None,
        dislikes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        다양성을 고려한 레시피 검색 (중복 방지)

        Args:
            search_query: 검색 쿼리
            constraints: 제약 조건
            user_id: 사용자 ID
            used_recipes: 이미 사용된 레시피 ID 집합
            max_results: 최대 결과 수
            allergies: 알레르기 목록 (임시 + 프로필)
            dislikes: 비선호 목록 (임시 + 프로필)

        Returns:
            중복되지 않은 레시피 목록
        """
        try:
            # 하이브리드 검색 실행 (결과 수 제한)
            search_results = await hybrid_search_tool.search(
                query=search_query,
                profile=constraints,
                max_results=min(max_results * 2, 30),  # 최대 10개로 제한
                user_id=user_id,
                allergies=allergies,
                dislikes=dislikes
            )
            
            if not search_results:
                return []
            
            # 중복되지 않은 레시피만 필터링
            unique_results = []

            for result in search_results:
                recipe_id = result.get('id', '')

                # 디버깅: ID 확인
                if not recipe_id:
                    print(f"⚠️ ID 없는 레시피 발견: {result.get('title', 'Unknown')}")
                    # ID가 없으면 title로 대체
                    recipe_id = result.get('title', '')

                if recipe_id and recipe_id not in used_recipes:
                    unique_results.append(result)
                    used_recipes.add(recipe_id)  # 중복 방지를 위해 추가
                    print(f"  ✅ 수집: {result.get('title', 'Unknown')} (ID: {recipe_id})")
                    if len(unique_results) >= max_results:
                        break
                else:
                    if recipe_id:
                        print(f"  ⚠️ 중복 제외: {result.get('title', 'Unknown')} (ID: {recipe_id})")

            print(f"🔍 _search_with_diversity 결과: 검색 {len(search_results)}개 → 중복제거 후 {len(unique_results)}개")
            return unique_results
            
        except Exception as e:
            print(f"❌ 다양성 검색 실패: {e}")
            return []
    
    async def _generate_ai_search_query(
        self, 
        meal_slot: str, 
        meal_type: str, 
        constraints: str, 
        used_recipes: set, 
        search_strategy: str = "기본 키워드 조합"
    ) -> Dict[str, Any]:
        """
        AI를 사용해서 최적의 검색 쿼리 생성
        
        Args:
            meal_slot: 식사 슬롯 (breakfast, lunch, dinner, snack)
            meal_type: 식사 타입 (계란 요리, 샐러드 등)
            constraints: 제약 조건
            used_recipes: 이미 사용된 레시피 ID 집합
            search_strategy: 검색 전략
            
        Returns:
            생성된 검색 쿼리 정보
        """
        try:
            if not self.llm:
                # LLM이 없으면 기본 쿼리 반환
                return {
                    "primary_query": f"{meal_type} 키토 {meal_slot}",
                    "alternative_queries": [f"{meal_type} 키토", f"키토 {meal_slot}"],
                    "excluded_keywords": [],
                    "search_strategy": "기본",
                    "reasoning": "LLM 없음"
                }
            
            # AI 검색 쿼리 생성 프롬프트 사용
            search_prompt = self.prompts.get("search_query", "").format(
                meal_slot=meal_slot,
                meal_type=meal_type,
                constraints=constraints,
                used_recipes=list(used_recipes)[:5],  # 최근 5개만 표시
                search_strategy=search_strategy
            )
            
            response = await self.llm.ainvoke([HumanMessage(content=search_prompt)])
            
            # JSON 파싱
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            print(f"❌ AI 검색 쿼리 생성 실패: {e}")
        
        # 폴백: 기본 쿼리
        return {
            "primary_query": f"{meal_type} 키토 {meal_slot}",
            "alternative_queries": [f"{meal_type} 키토", f"키토 {meal_slot}"],
            "excluded_keywords": [],
            "search_strategy": "폴백",
            "reasoning": "AI 생성 실패"
        }
    
    async def _generate_ai_meal_strategies(self, days: int, constraints: str) -> Dict[str, Any]:
        """
        AI를 사용해서 식사별 검색 전략 생성
        
        Args:
            days: 생성할 일수
            constraints: 제약 조건
            
        Returns:
            생성된 검색 전략
        """
        try:
            if not self.llm:
                # LLM이 없으면 기본 전략 반환
                return self._get_default_meal_strategies()
            
            # AI 검색 전략 생성 프롬프트 사용
            strategy_prompt = self.prompts.get("search_strategy", "").format(
                days=days,
                constraints=constraints
            )
            
            response = await self.llm.ainvoke([HumanMessage(content=strategy_prompt)])
            
            # JSON 파싱
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            print(f"❌ AI 검색 전략 생성 실패: {e}")
        
        # 폴백: 기본 전략
        return self._get_default_meal_strategies()
    
    def _get_default_meal_strategies(self) -> Dict[str, Any]:
        """기본 식사별 검색 전략"""
        return {
            "meal_strategies": {
                "breakfast": {
                    "primary_keywords": ["아침", "브런치", "계란"],
                    "secondary_keywords": ["베이컨", "아보카도", "치즈", "버터"],
                    "cooking_methods": ["스크램블", "구이", "볶음", "오믈렛"],
                    "time_keywords": ["아침", "브런치", "모닝"]
                },
                "lunch": {
                    "primary_keywords": ["점심", "샐러드", "구이"],
                    "secondary_keywords": ["스테이크", "생선", "고기", "볶음"],
                    "cooking_methods": ["그릴", "찜", "스튜", "볶음"],
                    "time_keywords": ["점심", "런치", "미들데이"]
                },
                "dinner": {
                    "primary_keywords": ["저녁", "고기", "생선"],
                    "secondary_keywords": ["삼겹살", "연어", "찜", "구이"],
                    "cooking_methods": ["구이", "찜", "스튜", "그릴"],
                    "time_keywords": ["저녁", "디너", "이브닝"]
                },
                "snack": {
                    "primary_keywords": ["간식", "견과류", "치즈"],
                    "secondary_keywords": ["아몬드", "호두", "올리브", "베리"],
                    "cooking_methods": ["구이", "볶음"],
                    "time_keywords": ["간식", "스낵", "애프터눈"]
                }
            },
            "diversity_strategy": "매일 다른 키워드 조합과 다양한 검색어 사용",
            "search_priority": ["variety_keywords", "primary_keywords", "cooking_methods", "secondary_keywords"]
        }
    
    async def _generate_meal_plan_from_embeddings(self, days: int, constraints: str, user_id: Optional[str] = None, fast_mode: bool = True,
                                                  allergies: Optional[List[str]] = None, dislikes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        1단계: 임베딩된 레시피 데이터에서 직접 식단표 생성

        Args:
            days: 생성할 일수
            constraints: 제약 조건
            user_id: 사용자 ID
            allergies: 알레르기 목록
            dislikes: 비선호 목록

        Returns:
            생성된 식단표 또는 None
        """
        try:
            print(f"🔍 임베딩 데이터에서 {days}일 식단표 생성 시도")
            
            # 임베딩 기반 프롬프트 사용
            embedding_prompt = self.prompts.get("embedding_based", "").format(
                days=days,
                constraints=constraints
            )
            
            # 빠른 모드에 따른 전략 선택
            if fast_mode:
                print("⚡ 빠른 검색 모드: 기본 전략 사용")
                meal_strategies = self._get_default_meal_strategies()["meal_strategies"]
            else:
                print("🤖 AI 검색 모드: AI 전략 생성")
                ai_strategies = await self._generate_ai_meal_strategies(days, constraints)
                meal_strategies = ai_strategies.get("meal_strategies", self._get_default_meal_strategies()["meal_strategies"])
            
            # 효율적인 검색: 식사별로 한 번에 여러 개 검색
            meal_plan_days = []
            used_recipes = set()  # 중복 방지용
            
            # 각 식사별로 한 번에 여러 개 검색
            meal_collections = {}
            
            for slot, strategy in meal_strategies.items():
                print(f"🔍 {slot} 레시피 {days}개 검색 중...")
                
                # 다양성을 위해 여러 검색 전략 시도
                all_search_results = []
                
                # 1. 기본 키워드 검색
                basic_query = f"{' '.join(strategy['primary_keywords'])} 키토"
                basic_results = await self._search_with_diversity(
                    basic_query, constraints, user_id, used_recipes, max_results=days * 2,
                    allergies=allergies, dislikes=dislikes
                )
                all_search_results.extend(basic_results)
                
                # 2. 다양성 키워드 검색 (각 날짜별로 다른 키워드 조합)
                if 'variety_keywords' in strategy:
                    for day_idx in range(min(days, len(strategy['variety_keywords']))):
                        variety_query = f"{' '.join(strategy['variety_keywords'][day_idx])} 키토"
                        variety_results = await self._search_with_diversity(
                            variety_query, constraints, user_id, used_recipes, max_results=2,
                            allergies=allergies, dislikes=dislikes
                        )
                        all_search_results.extend(variety_results)
                
                # 3. 조리법 기반 검색
                if 'cooking_methods' in strategy:
                    cooking_query = f"{' '.join(strategy['cooking_methods'][:3])} 키토 {slot}"
                    cooking_results = await self._search_with_diversity(
                        cooking_query, constraints, user_id, used_recipes, max_results=3,
                        allergies=allergies, dislikes=dislikes
                    )
                    all_search_results.extend(cooking_results)
                
                if all_search_results:
                    # 중복 제거 (ID 기준)
                    seen_ids = set()
                    unique_results = []
                    for result in all_search_results:
                        result_id = result.get('id', '')
                        if result_id and result_id not in seen_ids:
                            seen_ids.add(result_id)
                            unique_results.append(result)
                    
                    meal_collections[slot] = unique_results
                    print(f"✅ {slot} 레시피 {len(unique_results)}개 수집 완료 (다양성 검색 적용)")
                else:
                    meal_collections[slot] = []
                    print(f"❌ {slot} 레시피 검색 실패")
            
            # 7일 식단표 구성 (다양성 보장)
            for day in range(days):
                day_meals = {}
                
                for slot in meal_strategies.keys():
                    if slot in meal_collections and len(meal_collections[slot]) > 0:
                        # 중복 방지를 위해 선택된 레시피를 컬렉션에서 제거
                        available_recipes = meal_collections[slot]
                        
                        # 아직 사용되지 않은 레시피만 필터링
                        unused_recipes = [r for r in available_recipes if r.get('id', f"embedded_{slot}_{day}") not in used_recipes]
                        
                        if unused_recipes:
                            # 다양성을 위해 날짜별로 다른 선택 전략 적용
                            if day % 2 == 0:
                                # 짝수 날: 유사도가 높은 순으로 정렬 후 상위에서 선택
                                unused_recipes.sort(key=lambda x: x.get('similarity', 0.0), reverse=True)
                                selected_recipe = unused_recipes[min(2, len(unused_recipes)-1)]  # 상위 3개 중에서 선택
                            else:
                                # 홀수 날: 랜덤 선택
                                selected_recipe = random.choice(unused_recipes)
                        else:
                            # 모든 레시피가 사용되었으면 다시 랜덤 선택 (다양성 우선)
                            selected_recipe = random.choice(available_recipes)
                        
                        recipe_id = selected_recipe.get('id', f"embedded_{slot}_{day}")
                        used_recipes.add(recipe_id)
                        
                        # 선택된 레시피를 컬렉션에서 제거하여 다음 선택에서 제외
                        try:
                            meal_collections[slot].remove(selected_recipe)
                        except ValueError:
                            # 이미 제거된 경우 무시
                            pass
                        
                        day_meals[slot] = {
                            "type": "recipe",
                            "id": recipe_id,
                            "title": selected_recipe.get('title', f"키토 {slot}"),
                            "content": selected_recipe.get('content', ''),
                            "similarity": selected_recipe.get('similarity', 0.0),
                            "metadata": selected_recipe.get('metadata', {}),
                            "allergens": selected_recipe.get('allergens', []),
                            "ingredients": selected_recipe.get('ingredients', [])
                        }
                        
                        print(f"✅ {slot}: {selected_recipe.get('title', 'Unknown')} (유사도: {selected_recipe.get('similarity', 0.0):.2f})")
                    else:
                        print(f"⚠️ {slot}: 검색 결과 없음, AI 생성으로 넘어감")
                        return None  # AI 생성 단계로 넘어가기
                
                meal_plan_days.append(day_meals)
            
            # 성공적으로 모든 슬롯에 레시피를 찾았으면
            if len(meal_plan_days) == days:
                print(f"✅ 임베딩 데이터로 {days}일 식단표 생성 성공")
                
                # 총 매크로 계산
                total_macros = self._calculate_total_macros(meal_plan_days)
                
                # 조언 생성
                notes = [
                    "임베딩된 레시피 데이터에서 생성된 식단표입니다",
                    "키토 식단의 핵심은 탄수화물 제한입니다"
                ]
                
                return {
                    "days": meal_plan_days,
                    "duration_days": days,  # 요청된 일수 정보 추가
                    "total_macros": total_macros,
                    "notes": notes,
                    "source": "embeddings",
                    "constraints": {
                        "kcal_target": None,  # 임베딩 데이터에서는 정확한 목표 설정 어려움
                        "carbs_max": None,
                        "allergies": [],
                        "dislikes": []
                    }
                }
            
            return None
            
        except Exception as e:
            print(f"❌ 임베딩 데이터 식단표 생성 실패: {e}")
            return None
    
    async def _generate_detailed_meals_from_embeddings(self, structure: List[Dict[str, str]], constraints: str, user_id: Optional[str] = None, fast_mode: bool = True,
                                                       allergies: Optional[List[str]] = None, dislikes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        3단계: AI 구조를 바탕으로 임베딩 데이터에서 구체적 메뉴 생성

        Args:
            structure: AI가 생성한 식단 구조
            constraints: 제약 조건
            user_id: 사용자 ID
            allergies: 알레르기 목록
            dislikes: 비선호 목록

        Returns:
            생성된 식단표 또는 None
        """
        try:
            print(f"🔍 AI 구조 + 임베딩 데이터로 구체적 메뉴 생성")
            
            # 효율적인 검색: 식사별로 한 번에 여러 개 검색
            detailed_days = []
            used_recipes = set()  # 중복 방지용
            
            # 각 식사별로 한 번에 여러 개 검색
            meal_collections = {}
            days_count = len(structure)
            
            for slot in ['breakfast', 'lunch', 'dinner']:
                print(f"🔍 {slot} 레시피 {days_count}개 검색 중...")
                
                # AI 구조에서 가장 많이 나온 키워드 추출
                slot_keywords = []
                for day_plan in structure:
                    meal_type = day_plan.get(f"{slot}_type", "")
                    if meal_type:
                        slot_keywords.append(meal_type)
                
                # 가장 많이 나온 키워드로 검색
                if slot_keywords:
                    # 가장 많이 나온 키워드 선택
                    from collections import Counter
                    most_common = Counter(slot_keywords).most_common(1)[0][0]
                    search_query = f"{most_common} 키토 {slot}"
                else:
                    search_query = f"키토 {slot}"
                
                search_results = await self._search_with_diversity(
                    search_query, constraints, user_id, used_recipes, max_results=days_count * 3,
                    allergies=allergies, dislikes=dislikes
                )

                if search_results:
                    # _search_with_diversity에서 이미 중복 제거 완료
                    meal_collections[slot] = search_results
                    print(f"✅ {slot} 레시피 {len(search_results)}개 수집 완료")
                else:
                    meal_collections[slot] = []
                    print(f"❌ {slot} 레시피 검색 실패")
            
            # 7일 식단표 구성
            for day_idx, day_plan in enumerate(structure):
                day_meals = {}
                
                for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                    if slot == 'snack':
                        # 간식은 간단하게 처리
                        meal_type = day_plan.get(f"{slot}_type", "")
                        day_meals[slot] = await self._generate_simple_snack(meal_type)
                    else:
                        if slot in meal_collections and len(meal_collections[slot]) > day_idx:
                            # 랜덤 선택 적용
                            selected_recipe = random.choice(meal_collections[slot])
                            recipe_id = selected_recipe.get('id', f"embedded_{slot}_{day_idx}")
                            used_recipes.add(recipe_id)
                            
                            day_meals[slot] = {
                                "type": "recipe",
                                "id": recipe_id,
                                "title": selected_recipe.get('title', f"키토 {slot}"),
                                "content": selected_recipe.get('content', ''),
                                "similarity": selected_recipe.get('similarity', 0.0),
                                "metadata": selected_recipe.get('metadata', {}),
                                "allergens": selected_recipe.get('allergens', []),
                                "ingredients": selected_recipe.get('ingredients', [])
                            }
                            
                            print(f"✅ {slot}: {selected_recipe.get('title', 'Unknown')} (유사도: {selected_recipe.get('similarity', 0.0):.2f})")
                        else:
                            print(f"⚠️ {slot}: 검색 결과 없음, AI 생성으로 넘어감")
                            return None  # AI 생성 단계로 넘어가기
                
                detailed_days.append(day_meals)
            
            # 성공적으로 모든 슬롯에 레시피를 찾았으면
            if len(detailed_days) == days_count:
                print(f"✅ AI + 임베딩 데이터로 {days_count}일 식단표 생성 성공")
                
                # 총 매크로 계산
                total_macros = self._calculate_total_macros(detailed_days)
                
                # 조언 생성
                notes = [
                    "AI 구조 + 임베딩된 레시피 데이터에서 생성된 식단표입니다",
                    "키토 식단의 핵심은 탄수화물 제한입니다"
                ]
                
                return {
                    "type": "meal_plan",
                    "days": detailed_days,
                    "duration_days": days_count,  # 요청된 일수 정보 추가
                    "total_macros": total_macros,
                    "notes": notes,
                    "source": "ai_structure_plus_embeddings"
                }
            else:
                print(f"❌ AI + 임베딩 데이터로 식단표 생성 실패")
                return None
            
        except Exception as e:
            print(f"❌ AI 구조 + 임베딩 데이터 식단표 생성 실패: {e}")
            return None
    
    async def _plan_meal_structure(self, days: int, constraints: str) -> List[Dict[str, str]]:
        """전체 식단 구조 계획"""
        
        structure_prompt = self.prompts["structure"].format(
            days=days,
            constraints=constraints
        )
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=structure_prompt)])
            
            # JSON 파싱
            import re
            json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            print(f"Structure planning error: {e}")
        
        # 폴백: 기본 구조
        return [
            {
                "day": i + 1,
                "breakfast_type": "계란 요리",
                "lunch_type": "샐러드" if i % 2 == 0 else "구이",
                "dinner_type": "고기 요리" if i % 2 == 0 else "생선 요리",
                "snack_type": "견과류"
            }
            for i in range(days)
        ]
    
    async def _generate_detailed_meals(
        self,
        structure: List[Dict[str, str]],
        constraints: str
    ) -> List[Dict[str, Any]]:
        """구체적인 메뉴 생성"""
        
        detailed_days = []
        
        for day_plan in structure:
            day_meals = {}
            
            # 각 슬롯별 메뉴 생성
            for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                meal_type = day_plan.get(f"{slot}_type", "")
                
                if slot == 'snack':
                    # 간식은 간단하게
                    day_meals[slot] = await self._generate_simple_snack(meal_type)
                else:
                    # 메인 식사는 RAG 검색 또는 생성
                    meal = await self._generate_main_meal(slot, meal_type, constraints)
                    day_meals[slot] = meal
            
            detailed_days.append(day_meals)
        
        return detailed_days
    
    async def _generate_main_meal(
        self,
        slot: str,
        meal_type: str,
        constraints: str
    ) -> Dict[str, Any]:
        """메인 식사 메뉴 생성"""
        
        # 하이브리드 검색 시도 (사용자 프로필 필터링 포함)
        search_query = f"{meal_type} 키토 {slot}"
        rag_results = await hybrid_search_tool.search(
            query=search_query,
            profile=constraints,
            max_results=5,  # 1 → 5로 변경
            user_id=getattr(self, '_current_user_id', None)  # 현재 사용자 ID 전달
        )
        
        if rag_results:
            recipe = random.choice(rag_results)  # 랜덤 선택
            return {
                "type": "recipe",
                "id": recipe.get("id", ""),
                "title": recipe.get("title", ""),
                "macros": recipe.get("macros", {}),
                "ingredients": recipe.get("ingredients", []),
                "steps": recipe.get("steps", []),
                "tips": recipe.get("tips", [])
            }
        
        # RAG 결과가 없으면 LLM 생성
        return await self._generate_llm_meal(slot, meal_type, constraints)
    
    async def _generate_llm_meal(
        self,
        slot: str,
        meal_type: str,
        constraints: str
    ) -> Dict[str, Any]:
        """LLM을 통한 메뉴 생성"""
        
        meal_prompt = self.prompts["generation"].format(
            slot=slot,
            meal_type=meal_type,
            constraints=constraints
        )
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=meal_prompt)])
            
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                meal_data = json.loads(json_match.group())
                meal_data["id"] = f"generated_{slot}_{hash(meal_data['title']) % 10000}"
                return meal_data
            
        except Exception as e:
            print(f"LLM meal generation error: {e}")
        
        # 폴백 메뉴
        return {
            "type": "recipe",
            "id": f"fallback_{slot}",
            "title": f"키토 {meal_type}",
            "macros": {"kcal": 400, "carb": 8, "protein": 25, "fat": 30},
            "ingredients": [{"name": "기본 재료", "amount": 1, "unit": "개"}],
            "steps": ["간단히 조리하세요"],
            "tips": ["키토 원칙을 지켜주세요"]
        }
    
    async def _generate_simple_snack(self, snack_type: str) -> Dict[str, Any]:
        """간단한 간식 생성"""
        
        snack_options = {
            "견과류": {
                "title": "아몬드 & 치즈",
                "macros": {"kcal": 200, "carb": 3, "protein": 8, "fat": 18}
            },
            "치즈": {
                "title": "체다 치즈 큐브",
                "macros": {"kcal": 150, "carb": 1, "protein": 10, "fat": 12}
            },
            "올리브": {
                "title": "올리브 & 허브",
                "macros": {"kcal": 120, "carb": 2, "protein": 1, "fat": 12}
            }
        }
        
        snack = snack_options.get(snack_type, snack_options["견과류"])
        
        return {
            "type": "snack",
            "id": f"snack_{hash(snack['title']) % 1000}",
            "title": snack["title"],
            "macros": snack["macros"],
            "tips": ["적당량만 섭취하세요"]
        }
    
    async def _validate_and_adjust(
        self,
        plan: List[Dict[str, Any]],
        carbs_max: int,
        kcal_target: Optional[int]
    ) -> List[Dict[str, Any]]:
        """식단 검증 및 조정"""
        
        validated_plan = []
        
        for day_meals in plan:
            # 일일 매크로 계산
            daily_carbs = 0
            daily_kcal = 0
            
            for slot, meal in day_meals.items():
                macros = meal.get("macros", {})
                daily_carbs += macros.get("carb", 0)
                daily_kcal += macros.get("kcal", 0)
            
            # 탄수화물 초과 시 조정
            if daily_carbs > carbs_max:
                day_meals = await self._adjust_carbs(day_meals, carbs_max)
            
            # 칼로리 조정 (목표가 있는 경우)
            if kcal_target and abs(daily_kcal - kcal_target) > 200:
                day_meals = await self._adjust_calories(day_meals, kcal_target)
            
            validated_plan.append(day_meals)
        
        return validated_plan
    
    async def _adjust_carbs(
        self,
        day_meals: Dict[str, Any],
        carbs_max: int
    ) -> Dict[str, Any]:
        """탄수화물 조정"""
        
        # 간단한 조정: 가장 탄수화물이 높은 메뉴의 탄수화물 감소
        max_carb_slot = None
        max_carbs = 0
        
        for slot, meal in day_meals.items():
            carbs = meal.get("macros", {}).get("carb", 0)
            if carbs > max_carbs:
                max_carbs = carbs
                max_carb_slot = slot
        
        if max_carb_slot:
            # 탄수화물 20% 감소
            meal = day_meals[max_carb_slot]
            if "macros" in meal:
                meal["macros"]["carb"] = int(meal["macros"]["carb"] * 0.8)
                # 팁 추가
                if "tips" not in meal:
                    meal["tips"] = []
                meal["tips"].append("탄수화물 조정된 버전입니다")
        
        return day_meals
    
    async def _adjust_calories(
        self,
        day_meals: Dict[str, Any],
        kcal_target: int
    ) -> Dict[str, Any]:
        """칼로리 조정"""
        
        current_kcal = sum(
            meal.get("macros", {}).get("kcal", 0)
            for meal in day_meals.values()
        )
        
        ratio = kcal_target / current_kcal if current_kcal > 0 else 1.0
        
        # 모든 메뉴의 칼로리를 비례적으로 조정
        for meal in day_meals.values():
            if "macros" in meal:
                for macro in ["kcal", "protein", "fat"]:
                    if macro in meal["macros"]:
                        meal["macros"][macro] = int(meal["macros"][macro] * ratio)
        
        return day_meals
    
    def _calculate_total_macros(self, plan: List[Dict[str, Any]]) -> Dict[str, int]:
        """전체 매크로 영양소 계산"""
        
        total = {"kcal": 0, "carb": 0, "protein": 0, "fat": 0}
        
        for day_meals in plan:
            for meal in day_meals.values():
                macros = meal.get("macros", {})
                for key in total.keys():
                    total[key] += macros.get(key, 0)
        
        # 평균 계산
        days = len(plan)
        avg_total = {f"avg_{key}": round(value / days, 1) for key, value in total.items()}
        
        return {**total, **avg_total}
    
    async def _generate_meal_notes(
        self,
        plan: List[Dict[str, Any]],
        constraints: str
    ) -> List[str]:
        """식단표 조언 생성"""
        
        notes_prompt = self.prompts["notes"].format(constraints=constraints)
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=notes_prompt)])
            
            # 응답을 줄 단위로 분할하여 리스트로 변환
            notes = [
                line.strip().lstrip('- ').lstrip('• ')
                for line in response.content.split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]
            
            return notes[:5]  # 최대 5개
            
        except Exception as e:
            print(f"Notes generation error: {e}")
            return [
                "충분한 물을 섭취하세요 (하루 2-3L)",
                "전해질 보충을 위해 소금을 적절히 섭취하세요",
                "식단 초기 2-3일은 컨디션 난조가 있을 수 있습니다",
                "미리 재료를 준비해두면 식단 유지가 쉬워집니다",
                "일주일에 1-2회 치팅 데이를 가져도 괜찮습니다"
            ]
    
    async def _generate_fallback_plan(self, days: int) -> Dict[str, Any]:
        """폴백 식단표 생성"""
        
        fallback_meals = {
            "breakfast": {
                "type": "recipe",
                "title": "키토 스크램블 에그",
                "macros": {"kcal": 350, "carb": 5, "protein": 25, "fat": 25}
            },
            "lunch": {
                "type": "recipe", 
                "title": "키토 그린 샐러드",
                "macros": {"kcal": 400, "carb": 8, "protein": 20, "fat": 32}
            },
            "dinner": {
                "type": "recipe",
                "title": "키토 삼겹살 구이",
                "macros": {"kcal": 500, "carb": 6, "protein": 30, "fat": 40}
            },
            "snack": {
                "type": "snack",
                "title": "아몬드 & 치즈",
                "macros": {"kcal": 200, "carb": 3, "protein": 8, "fat": 18}
            }
        }
        
        plan_days = [fallback_meals.copy() for _ in range(days)]
        
        return {
            "days": plan_days,
            "duration_days": days,  # 요청된 일수 정보 추가
            "total_macros": self._calculate_total_macros(plan_days),
            "notes": ["기본 키토 식단입니다", "개인 취향에 맞게 조정하세요"]
        }
    
    async def generate_single_recipe(self, message: str, profile_context: str = "") -> str:
        """단일 레시피 생성 (벡터 검색 기반)"""
        
        if not self.llm:
            return self._get_recipe_fallback(message)
        
        try:
            # 1단계: 벡터 검색으로 관련 레시피들 찾기
            print(f"🔍 벡터 검색으로 관련 레시피 찾기: '{message}'")
            vector_results = []
            
            try:
                # hybrid_search 사용 (알레르기 필터링 포함)
                from app.tools.shared.hybrid_search import HybridSearchTool
                hybrid_search = HybridSearchTool()
                
                # 프로필에서 알레르기/비선호 추출
                user_id = None
                allergies = []
                dislikes = []
                
                # profile_context에서 알레르기/비선호 파싱
                if "알레르기:" in profile_context:
                    allergy_part = profile_context.split("알레르기:")[1].split(".")[0]
                    allergies = [a.strip() for a in allergy_part.split(",") if a.strip()]
                
                if "싫어하는 음식:" in profile_context:
                    dislike_part = profile_context.split("싫어하는 음식:")[1].split(".")[0]
                    dislikes = [d.strip() for d in dislike_part.split(",") if d.strip()]
                
                vector_results = await hybrid_search.search(
                    query=message,
                    max_results=5,
                    user_id=user_id,
                    allergies=allergies,
                    dislikes=dislikes
                )
                print(f"✅ 벡터 검색 완료: {len(vector_results)}개 레시피 발견 (알레르기 필터링 적용)")
            except Exception as e:
                print(f"⚠️ 벡터 검색 실패: {e}, 기존 방식으로 진행")
                vector_results = []
            
            # 2단계: 검색 결과를 AI가 이해할 수 있는 형태로 변환
            context_recipes = self._format_vector_results_for_ai(vector_results)
            
            # 3단계: AI가 검색 결과를 참고하여 새 레시피 생성
            if vector_results:
                # 벡터 검색 결과가 있으면 기존 프롬프트 템플릿 사용
                try:
                    from app.prompts.meal.recipe_response import RECIPE_RESPONSE_GENERATION_PROMPT
                    prompt = RECIPE_RESPONSE_GENERATION_PROMPT.format(
                        message=message,
                        context=context_recipes,
                        profile_context=profile_context or ""
                    )
                except ImportError:
                    # 폴백: 기본 프롬프트 사용
                    prompt = f"""
키토 식단 전문가로서 사용자의 레시피 요청에 답변해주세요.

사용자 요청: {message}

검색된 레시피 정보:
{context_recipes}

다음 형식으로 답변해주세요:

## 🍽️ 추천 키토 레시피

위에서 검색된 레시피들을 바탕으로 키토 식단에 적합한 레시피를 추천드립니다.

### 💡 키토 팁
검색된 레시피와 관련된 실용적인 키토 식단 조언을 2~3가지만 간단하게 작성해주세요.

더 자세한 정보가 필요하시면 언제든 말씀해주세요!
"""
            else:
                # 검색 결과가 없으면 기존 방식으로 생성
                try:
                    from app.prompts.meal.single_recipe import SINGLE_RECIPE_GENERATION_PROMPT
                    prompt = SINGLE_RECIPE_GENERATION_PROMPT.format(
                        message=message,
                        profile_context=profile_context if profile_context else '특별한 제약사항 없음'
                    )
                except ImportError:
                    # 폴백 프롬프트 파일에서 로드
                    try:
                        from app.prompts.meal.fallback import FALLBACK_SINGLE_RECIPE_PROMPT
                        prompt = FALLBACK_SINGLE_RECIPE_PROMPT.format(
                            message=message,
                            profile_context=profile_context if profile_context else '특별한 제약사항 없음'
                        )
                    except ImportError:
                        # 정말 마지막 폴백
                        prompt = f"'{message}'에 대한 키토 레시피를 생성하세요. 사용자 정보: {profile_context if profile_context else '없음'}"
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            print(f"Single recipe generation error: {e}")
            return self._get_recipe_fallback(message)
    
    def _format_vector_results_for_ai(self, vector_results: List[Dict]) -> str:
        """벡터 검색 결과를 AI가 이해할 수 있는 형태로 변환"""
        if not vector_results:
            return "관련 레시피를 찾을 수 없습니다."
        
        formatted_recipes = []
        for i, result in enumerate(vector_results[:5], 1):  # 상위 5개만
            # 기본 정보 추출
            title = result.get('title', 'Unknown')
            ingredients = result.get('ingredients', 'Unknown')
            content = result.get('content', 'Unknown')
            similarity = result.get('similarity_score', 0.0)
            
            # 내용이 너무 길면 잘라내기
            if len(content) > 300:
                content = content[:300] + "..."
            
            recipe_info = f"""
### 🍽️ {title} (유사도: {similarity:.2f})

**재료:**
{ingredients}

**조리법:**
{content}
"""
            formatted_recipes.append(recipe_info)
        
        return "\n".join(formatted_recipes)
    
    def _get_recipe_fallback(self, message: str) -> str:
        """레시피 생성 실패 시 폴백 응답 (프롬프트 파일에서 로드)"""
        try:
            from app.prompts.meal.single_recipe import RECIPE_FALLBACK_PROMPT
            return RECIPE_FALLBACK_PROMPT.format(message=message)
        except ImportError:
            # 폴백 프롬프트 파일에서 로드
            try:
                from app.prompts.meal.fallback import FALLBACK_RECIPE_ERROR_PROMPT
                return FALLBACK_RECIPE_ERROR_PROMPT.format(message=message)
            except ImportError:
                # 정말 마지막 폴백
                try:
                    from app.prompts.meal.fallback import FINAL_RECIPE_FALLBACK_PROMPT
                    return FINAL_RECIPE_FALLBACK_PROMPT.format(message=message)
                except ImportError:
                    return f"키토 레시피 '{message}' 생성에 실패했습니다. 키토 원칙에 맞는 재료로 직접 조리해보세요."

    # ==========================================
    # 프로필 통합 편의 함수들 
    # ==========================================
    
    async def generate_personalized_meal_plan(self, user_id: str, days: int = 7, fast_mode: bool = True) -> Dict[str, Any]:
        """
        사용자 ID만으로 개인화된 식단 계획 생성
        
        Args:
            user_id (str): 사용자 ID
            days (int): 생성할 일수 (기본 7일)
            fast_mode (bool): 빠른 모드 (기본 True)
            
        Returns:
            Dict[str, Any]: 생성된 개인화 식단표 데이터
        """
        print(f"🔧 개인화 식단 계획 생성 시작: 사용자 {user_id}, {days}일")
        
        # 현재 사용자 ID 저장 (검색 시 프로필 필터링용)
        self._current_user_id = user_id
        
        # 사용자 프로필 조회
        profile_result = await user_profile_tool.get_user_preferences(user_id)
        
        if not profile_result["success"]:
            print(f"⚠️ 프로필 조회 실패, 기본값으로 진행: {profile_result.get('error')}")
            return await self.generate_meal_plan(days=days, user_id=user_id)
        
        prefs = profile_result["preferences"]
        
        # 프로필 정보로 식단 생성
        return await self.generate_meal_plan(
            days=days,
            kcal_target=prefs.get("goals_kcal"),
            carbs_max=prefs.get("goals_carbs_g", 30),
            allergies=prefs.get("allergies"),
            dislikes=prefs.get("dislikes"),
            user_id=user_id,
            fast_mode=fast_mode
        )
    
    async def generate_recipe_with_profile(self, user_id: str, message: str) -> str:
        """
        사용자 프로필을 고려한 레시피 생성
        
        Args:
            user_id (str): 사용자 ID
            message (str): 레시피 요청 메시지
            
        Returns:
            str: 생성된 레시피
        """
        print(f"🔧 개인화 레시피 생성 시작: 사용자 {user_id}, 요청 '{message}'")
        
        # 사용자 프로필 조회
        profile_result = await user_profile_tool.get_user_preferences(user_id)
        
        if profile_result["success"]:
            # 프로필 정보를 프롬프트용 텍스트로 포맷팅
            profile_context = user_profile_tool.format_preferences_for_prompt(profile_result)
            print(f"✅ 프로필 적용: {profile_context}")
        else:
            profile_context = "사용자 프로필 정보를 가져올 수 없습니다."
            print(f"⚠️ 프로필 조회 실패: {profile_result.get('error')}")
        
        return await self.generate_single_recipe(message, profile_context)
    
    async def check_user_access_and_generate(self, user_id: str, request_type: str = "meal_plan", **kwargs) -> Dict[str, Any]:
        """
        사용자 접근 권한 확인 후 식단/레시피 생성
        
        Args:
            user_id (str): 사용자 ID
            request_type (str): 요청 타입 ("meal_plan" 또는 "recipe")
            **kwargs: 추가 매개변수
            
        Returns:
            Dict[str, Any]: 결과 또는 접근 제한 메시지
        """
        print(f"🔧 사용자 접근 권한 확인: {user_id}")
        
        # 접근 권한 확인
        access_result = await user_profile_tool.check_user_access(user_id)
        
        if not access_result["success"]:
            return {
                "success": False,
                "error": f"접근 권한 확인 실패: {access_result.get('error')}"
            }
        
        access_info = access_result["access"]
        
        if not access_info["has_access"]:
            return {
                "success": False,
                "error": f"접근 권한이 없습니다. 현재 상태: {access_info['state']}",
                "access_info": access_info
            }
        
        print(f"✅ 접근 권한 확인 완료: {access_info['state']}")
        
        # 요청 타입에 따라 처리
        if request_type == "meal_plan":
            days = kwargs.get("days", 7)
            result = await self.generate_personalized_meal_plan(user_id, days)
            return {"success": True, "data": result, "access_info": access_info}
        
        elif request_type == "recipe":
            message = kwargs.get("message", "키토 레시피")
            result = await self.generate_recipe_with_profile(user_id, message)
            return {"success": True, "data": result, "access_info": access_info}
        
        else:
            return {
                "success": False,
                "error": f"지원하지 않는 요청 타입: {request_type}"
            }
    
    # ==========================================
    # 새로운 통합 처리 메서드들
    # ==========================================
    
    async def handle_meal_request(self, message: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        모든 식단 요청 처리의 진입점
        Orchestrator로부터 모든 처리 위임받음
        
        Args:
            message (str): 사용자 메시지
            state (Dict): 전체 상태
            
        Returns:
            Dict[str, Any]: 업데이트할 상태 정보
        """
        print(f"🍽️ 식단 요청 처리 시작: '{message}'")
        
        # 1. 날짜 파싱
        days = self._parse_days(message, state)
        if days is None:
            # plans.py의 기본값 상수 사용
            days = DEFAULT_MEAL_PLAN_DAYS
            print(f"📅 일수 파악 실패 → plans.py 기본값 {days}일 사용")
        
        # 2. 제약조건 추출
        constraints = self._extract_all_constraints(message, state)
        
        # 3. fast_mode 결정
        fast_mode = state.get("fast_mode", self._determine_fast_mode(message))
        
        # 4. 사용자 ID 확인
        user_id = state.get("profile", {}).get("user_id")
        
        # 5. 개인화 vs 일반 식단 결정
        if state.get("use_personalized") and user_id:
            print(f"👤 개인화 식단 생성: user_id={user_id}")
            
            # 접근 권한 확인 옵션
            if state.get("check_access", False):
                result = await self.check_user_access_and_generate(
                    user_id=user_id,
                    request_type="meal_plan",
                    days=days
                )
                if not result["success"]:
                    return {
                        "response": result["error"],
                        "results": []
                    }
                meal_plan = result["data"]
            else:
                # 직접 개인화 생성
                meal_plan = await self.generate_personalized_meal_plan(
                    user_id=user_id,
                    days=days,
                    fast_mode=fast_mode
                )
        else:
            # 일반 식단 생성
            meal_plan = await self.generate_meal_plan(
                days=days,
                kcal_target=constraints.get("kcal_target"),
                carbs_max=constraints.get("carbs_max", 30),
                allergies=constraints.get("allergies", []),
                dislikes=constraints.get("dislikes", []),
                user_id=user_id,
                fast_mode=fast_mode
            )
        
        # 6. 응답 포맷팅
        formatted_response = self.response_formatter.format_meal_plan(
            meal_plan, days
        )
        
        # 7. 결과 반환 - 프론트엔드가 인식할 수 있는 형태로 results 구성
        # 프론트엔드 MealParserService가 찾는 형태: result.type === 'meal_plan' || result.days
        frontend_meal_result = {
            "type": "meal_plan",
            "days": meal_plan.get("days", []),
            "duration_days": days,
            "total_macros": meal_plan.get("total_macros"),
            "notes": meal_plan.get("notes", []),
            "source": meal_plan.get("source", "meal_planner")
        }
        
        # 디버그: 프론트엔드로 전송될 데이터 로깅
        print("🔍 DEBUG: 프론트엔드로 전송될 frontend_meal_result:")
        print(f"  - type: {frontend_meal_result.get('type')}")
        print(f"  - days length: {len(frontend_meal_result.get('days', []))}")
        if frontend_meal_result.get("days") and len(frontend_meal_result["days"]) > 0:
            first_day = frontend_meal_result["days"][0]
            print(f"  - first_day keys: {list(first_day.keys())}")
            for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                if slot in first_day:
                    slot_data = first_day[slot]
                    if isinstance(slot_data, dict):
                        print(f"  - {slot}: {slot_data.get('title', 'NO_TITLE')}")
                    else:
                        print(f"  - {slot}: {slot_data}")
        
        result_data = {
            "results": [frontend_meal_result],  # 프론트엔드가 인식할 수 있는 형태
            "response": formatted_response,
            "formatted_response": formatted_response,  # 포맷된 응답 저장
            "meal_plan_days": days,
            "meal_plan_data": meal_plan,  # 구조화된 데이터
            "tool_calls": [{
                "tool": "meal_planner",
                "method": "handle_meal_request",
                "days": days,
                "fast_mode": fast_mode,
                "personalized": state.get("use_personalized", False)
            }]
        }
        
        print("🔍 DEBUG: 최종 반환 데이터 구조:")
        print(f"  - results length: {len(result_data.get('results', []))}")
        print(f"  - meal_plan_data 존재: {bool(result_data.get('meal_plan_data'))}")
        
        return result_data
    
    async def handle_recipe_request(self, message: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        모든 레시피 요청 처리의 진입점
        
        Args:
            message (str): 사용자 메시지
            state (Dict): 전체 상태
            
        Returns:
            Dict[str, Any]: 업데이트할 상태 정보
        """
        print(f"🍳 레시피 요청 처리 시작: '{message}'")
        
        # 1. 제약조건 추출
        constraints = self._extract_all_constraints(message, state)
        
        # 2. 사용자 ID 확인
        user_id = state.get("profile", {}).get("user_id")
        
        # 3. 프로필 기반 vs 일반 레시피
        if user_id and state.get("profile"):
            print(f"👤 프로필 기반 레시피 생성: user_id={user_id}")
            recipe = await self.generate_recipe_with_profile(
                user_id=user_id,
                message=message
            )
        else:
            # 프로필 컨텍스트 생성
            profile_context = self._build_profile_context(constraints)
            recipe = await self.generate_single_recipe(
                message=message,
                profile_context=profile_context
            )
        
        # 4. 응답 포맷팅
        formatted_response = self.response_formatter.format_recipe(
            recipe, message
        )
        
        # 5. 결과 반환
        return {
            "results": [{
                "title": f"AI 생성: {message}",
                "content": recipe,
                "source": "meal_planner_agent",
                "type": "recipe"
            }],
            "response": formatted_response,
            "formatted_response": formatted_response,
            "tool_calls": [{
                "tool": "meal_planner",
                "method": "handle_recipe_request",
                "query": message,
                "has_profile": bool(user_id and state.get("profile"))
            }]
        }
    
    # ==========================================
    # 헬퍼 메서드들
    # ==========================================
    
    def _parse_days(self, message: str, state: Dict) -> Optional[int]:
        """
        메시지에서 날짜/일수 파싱 (LLM 기반)
        
        Args:
            message (str): 사용자 메시지
            state (Dict): 상태 정보
            
        Returns:
            Optional[int]: 파싱된 일수 또는 None
        """
        # LLM 파싱 시도 (대화 맥락 포함)
        try:
            chat_history = state.get("chat_history", [])
            parsed_date = self.date_parser.parse_natural_date_with_context(message, chat_history)
            if parsed_date and parsed_date.duration_days:
                print(f"📅 DateParser LLM이 감지한 days: {parsed_date.duration_days}")
                return parsed_date.duration_days
        except Exception as e:
            print(f"⚠️ DateParser LLM 파싱 오류: {e}")
        
        # 슬롯에서 가져오기 (백업)
        slots_days = state.get("slots", {}).get("days")
        if slots_days:
            days = int(slots_days)
            print(f"📅 슬롯에서 추출된 days: {days}")
            return days
        
        # 기본값 없이 None 반환
        print("⚠️ 일수를 파악할 수 없음")
        return None
    
    def _extract_all_constraints(self, message: str, state: Dict) -> Dict[str, Any]:
        """
        메시지와 프로필에서 모든 제약조건 추출
        
        Args:
            message (str): 사용자 메시지  
            state (Dict): 상태 정보
            
        Returns:
            Dict: 추출된 제약조건들
        """
        constraints = {
            "kcal_target": None,
            "carbs_max": 30,
            "allergies": [],
            "dislikes": []
        }
        
        # 임시 불호 식재료 추출
        temp_dislikes = self.temp_dislikes_extractor.extract_from_message(message)
        
        # 프로필 정보 병합
        if state.get("profile"):
            profile = state["profile"]
            constraints["kcal_target"] = profile.get("goals_kcal")
            constraints["carbs_max"] = profile.get("goals_carbs_g", 30)
            constraints["allergies"] = profile.get("allergies", [])
            
            profile_dislikes = profile.get("dislikes", [])
            # 임시 불호와 프로필 불호 합치기
            constraints["dislikes"] = self.temp_dislikes_extractor.combine_with_profile_dislikes(
                temp_dislikes, profile_dislikes
            )
        else:
            constraints["dislikes"] = temp_dislikes
        
        print(f"📋 추출된 제약조건: 칼로리 {constraints['kcal_target']}, "
              f"탄수화물 {constraints['carbs_max']}g, "
              f"알레르기 {len(constraints['allergies'])}개, "
              f"불호 {len(constraints['dislikes'])}개")
        
        return constraints
    
    def _determine_fast_mode(self, message: str) -> bool:
        """
        메시지 내용에 따라 fast_mode 결정
        
        Args:
            message (str): 사용자 메시지
            
        Returns:
            bool: fast_mode 여부
        """
        # 정확한 검색이 필요한 키워드
        accurate_keywords = ["정확한", "자세한", "맞춤", "개인", "추천", "최적"]
        
        # 빠른 응답이 필요한 키워드
        fast_keywords = ["빠르게", "간단히", "대충", "아무거나", "급해"]
        
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in accurate_keywords):
            print("🔍 정확한 검색 모드")
            return False
        
        if any(keyword in message_lower for keyword in fast_keywords):
            print("⚡ 빠른 검색 모드")
            return True
        
        # 기본값: 빠른 모드
        return True
    
    def _build_profile_context(self, constraints: Dict[str, Any]) -> str:
        """
        제약조건을 프롬프트용 텍스트로 변환
        
        Args:
            constraints (Dict): 제약조건
            
        Returns:
            str: 프로필 컨텍스트 문자열
        """
        context_parts = []
        
        if constraints.get("kcal_target"):
            context_parts.append(f"목표 칼로리: {constraints['kcal_target']}kcal")
        
        if constraints.get("carbs_max"):
            context_parts.append(f"탄수화물 제한: {constraints['carbs_max']}g")
        
        if constraints.get("allergies"):
            context_parts.append(f"알레르기: {', '.join(constraints['allergies'])}")
        
        if constraints.get("dislikes"):
            context_parts.append(f"싫어하는 음식: {', '.join(constraints['dislikes'])}")
        
        return ". ".join(context_parts) if context_parts else ""
    
    def _should_use_personalized(self, message: str, state: Dict) -> bool:
        """
        개인화 기능 사용 여부 결정
        
        Args:
            message (str): 사용자 메시지
            state (Dict): 상태 정보
            
        Returns:
            bool: 개인화 사용 여부
        """
        # 명시적 플래그 확인
        if state.get("use_personalized"):
            return True
        
        # 개인화 키워드 확인
        personalized_keywords = ["맞춤", "개인", "나한테", "내게", "나에게", "내 취향"]
        if any(keyword in message.lower() for keyword in personalized_keywords):
            return True
        
        return False
