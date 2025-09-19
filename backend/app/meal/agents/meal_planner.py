"""
식단표 생성 에이전트
AI 기반 7일 키토 식단 계획 생성
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import date, timedelta
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

from app.core.config import settings
from app.shared.tools.hybrid_search import hybrid_search_tool
from app.restaurant.tools.place_search import PlaceSearchTool
from app.meal.tools.keto_score import KetoScoreCalculator

# 프롬프트 모듈 import
from app.meal.prompts.meal_plan_structure import MEAL_PLAN_STRUCTURE_PROMPT
from app.meal.prompts.meal_generation import MEAL_GENERATION_PROMPT
from app.meal.prompts.meal_plan_notes import MEAL_PLAN_NOTES_PROMPT

class MealPlannerAgent:
    """7일 키토 식단표 생성 에이전트"""
    
    def __init__(self):
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
        self.keto_score = KetoScoreCalculator()
    
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
            user_id: 사용자 ID
        
        Returns:
            생성된 식단표 데이터
        """
        
        try:
            # 제약 조건 텍스트 생성
            constraints_text = self._build_constraints_text(
                kcal_target, carbs_max, allergies, dislikes
            )
            
            # 1차: 전체 식단 구조 계획
            meal_structure = await self._plan_meal_structure(days, constraints_text)
            
            # 2차: 각 슬롯별 구체적 메뉴 생성
            detailed_plan = await self._generate_detailed_meals(
                meal_structure, constraints_text
            )
            
            # 3차: 검증 및 조정
            validated_plan = await self._validate_and_adjust(
                detailed_plan, carbs_max, kcal_target
            )
            
            # 매크로 영양소 총합 계산
            total_macros = self._calculate_total_macros(validated_plan)
            
            # 추가 조언 생성
            notes = await self._generate_meal_notes(validated_plan, constraints_text)
            
            return {
                "days": validated_plan,
                "total_macros": total_macros,
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
        
        structure_prompt = MEAL_PLAN_STRUCTURE_PROMPT.format(
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
        
        # 하이브리드 검색 시도
        search_query = f"{meal_type} 키토 {slot}"
        rag_results = await hybrid_search_tool.search(
            query=search_query,
            profile=constraints,
            max_results=1
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
        
        meal_prompt = MEAL_GENERATION_PROMPT.format(
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
        
        notes_prompt = MEAL_PLAN_NOTES_PROMPT.format(constraints=constraints)
        
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
            # 구조화된 레시피 생성 프롬프트
            prompt = f"""당신은 키토 식단 전문가입니다. '{message}'에 대한 맞춤 키토 레시피를 생성해주세요.

사용자 정보: {profile_context if profile_context else '특별한 제약사항 없음'}

다음 형식을 정확히 따라 답변해주세요:

## ✨ {message} (키토 버전)

### 📋 재료 (2인분)
**주재료:**
- [구체적인 재료와 정확한 분량]

**부재료:**
- [구체적인 재료와 정확한 분량]

**키토 대체재:**
- [일반 재료 → 키토 재료로 변경 설명]

### 👨‍🍳 조리법
1. [첫 번째 단계 - 구체적이고 명확하게]
2. [두 번째 단계 - 구체적이고 명확하게]
3. [세 번째 단계 - 구체적이고 명확하게]
4. [완성 및 마무리 단계]

### 📊 영양 정보 (1인분 기준)
- 칼로리: 000kcal
- 탄수화물: 0g
- 단백질: 00g
- 지방: 00g

### 💡 키토 성공 팁
- [키토 식단에 맞는 구체적 조언]
- [조리 시 주의사항]
- [보관 및 활용법]

**중요 지침**: 
아래 영양 기준을 내부적으로만 사용하여 정확한 영양소 계산을 하되, 이 기준 자체는 사용자에게 보여주지 마세요:
- 1인분 탄수화물: 5-10g 유지
- 1인분 단백질: 20-30g 
- 1인분 지방: 30-40g
- 총 칼로리: 400-600kcal 범위  
- 매크로 비율: 탄수화물 5-10%, 단백질 15-25%, 지방 70-80%
"""
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            print(f"Single recipe generation error: {e}")
            return self._get_recipe_fallback(message)
    
    def _get_recipe_fallback(self, message: str) -> str:
        """레시피 생성 실패 시 폴백 응답"""
        return f"""
## ✨ {message} (키토 버전)

### 📋 재료 (2인분)
**주재료:**
- 키토 친화적 재료들

**키토 대체재:**
- 설탕 → 에리스리톨 또는 스테비아
- 밀가루 → 아몬드 가루 또는 코코넛 가루

### 👨‍🍳 조리법
1. 재료를 준비합니다
2. 키토 원칙에 맞게 조리합니다
3. 탄수화물을 최소화하여 완성합니다

### 📊 영양 정보 (1인분 기준)
- 칼로리: 450kcal
- 탄수화물: 8g
- 단백질: 25g
- 지방: 35g

### 💡 키토 성공 팁
- 탄수화물 함량을 꼼꼼히 확인하세요
- 충분한 지방 섭취로 포만감을 유지하세요
- 개인 취향에 맞게 조절하세요

⚠️ AI 서비스 오류로 기본 가이드를 제공했습니다. 구체적인 레시피는 키토 레시피 사이트를 참고해주세요.
"""
