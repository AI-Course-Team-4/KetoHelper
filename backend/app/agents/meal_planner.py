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
from typing import Dict, Any, List, Optional
from datetime import date, timedelta
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
import importlib

from app.core.config import settings
from app.tools.shared.hybrid_search import hybrid_search_tool
from app.tools.shared.profile_tool import user_profile_tool
from app.tools.restaurant.place_search import PlaceSearchTool
from config import get_personal_configs, get_agent_config

class MealPlannerAgent:
    """7일 키토 식단표 생성 에이전트"""
    
    # 기본 설정 (개인 설정이 없을 때 사용)
    DEFAULT_AGENT_NAME = "Meal Planner Agent"
    DEFAULT_PROMPT_FILES = {
        "structure": "structure",  # meal/prompts/ 폴더의 파일명
        "generation": "generation",
        "notes": "notes"
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
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=settings.gemini_temperature
            )
        except Exception as e:
            print(f"Gemini AI 초기화 실패: {e}")
            self.llm = None
        
        # 하이브리드 검색 도구 사용
        self.place_search = PlaceSearchTool()
    
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
                "notes": FALLBACK_NOTES_PROMPT
            }
            
            return fallback_defaults.get(key, "프롬프트를 찾을 수 없습니다.")
            
        except ImportError:
            # 정말 마지막 폴백
            return f"키토 {key} 작업을 수행하세요."
    
    async def generate_meal_plan(
        self,
        days: int = 7,
        kcal_target: Optional[int] = None,
        carbs_max: int = 30,
        allergies: List[str] = None,
        dislikes: List[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        7일 키토 식단표 생성
        
        Args:
            days: 생성할 일수 (기본 7일)
            kcal_target: 목표 칼로리 (일일)
            carbs_max: 최대 탄수화물 (일일, g)
            allergies: 알레르기 목록
            dislikes: 비선호 음식 목록
            user_id: 사용자 ID (제공되면 자동으로 프로필에서 선호도 정보 가져옴)
        
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
            
            # 1차: 전체 식단 구조 계획만 (간단 버전)
            meal_structure = await self._plan_meal_structure(days, constraints_text)
            
            # 간단한 형태로 변환 (메뉴 타입만)
            simple_plan = []
            for day_plan in meal_structure:
                day_meals = {
                    "breakfast": {"title": day_plan.get("breakfast_type", "아침 메뉴"), "type": "simple"},
                    "lunch": {"title": day_plan.get("lunch_type", "점심 메뉴"), "type": "simple"},
                    "dinner": {"title": day_plan.get("dinner_type", "저녁 메뉴"), "type": "simple"},
                    "snack": {"title": day_plan.get("snack_type", "간식"), "type": "simple"}
                }
                simple_plan.append(day_meals)
            
            # 기본 조언 생성
            notes = [
                "각 메뉴를 클릭하면 상세 레시피를 볼 수 있습니다",
                "키토 식단의 핵심은 탄수화물 제한입니다",
                "충분한 수분 섭취를 잊지 마세요"
            ]
            
            return {
                "days": simple_plan,
                "total_macros": {"message": "간단 버전에서는 영양 계산이 제외됩니다"},
                "notes": notes,
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
            max_results=1,
            user_id=getattr(self, '_current_user_id', None)  # 현재 사용자 ID 전달
        )
        
        if rag_results:
            recipe = rag_results[0]
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
            "total_macros": self._calculate_total_macros(plan_days),
            "notes": ["기본 키토 식단입니다", "개인 취향에 맞게 조정하세요"]
        }
    
    async def generate_single_recipe(self, message: str, profile_context: str = "") -> str:
        """단일 레시피 생성 (orchestrator용)"""
        
        if not self.llm:
            return self._get_recipe_fallback(message)
        
        try:
            # 프롬프트 파일에서 로드
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
                return f"키토 레시피 '{message}' 생성에 실패했습니다. 키토 원칙에 맞는 재료로 직접 조리해보세요."

    # ==========================================
    # 프로필 통합 편의 함수들 
    # ==========================================
    
    async def generate_personalized_meal_plan(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        사용자 ID만으로 개인화된 식단 계획 생성
        
        Args:
            user_id (str): 사용자 ID
            days (int): 생성할 일수 (기본 7일)
            
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
            user_id=user_id
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
