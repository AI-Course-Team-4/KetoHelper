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
import random

from app.tools.shared.hybrid_search import hybrid_search_tool
from app.tools.shared.profile_tool import user_profile_tool
from app.tools.shared.date_parser import DateParser
from app.tools.shared.temporary_dislikes_extractor import temp_dislikes_extractor
from app.tools.meal.response_formatter import MealResponseFormatter
from app.core.llm_factory import create_chat_llm
from app.core.redis_cache import redis_cache
from config import get_personal_configs, get_agent_config

# 기본값 상수 정의
DEFAULT_MEAL_PLAN_DAYS = 7
MAX_MEAL_PLAN_DAYS = 7  # 최대 7일 제한

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
            # MealPlannerAgent 전용 LLM 설정 사용
            from app.core.config import settings
            self.llm = create_chat_llm(
                provider=settings.meal_planner_provider,
                model=settings.meal_planner_model,
                temperature=settings.meal_planner_temperature,
                max_tokens=settings.meal_planner_max_tokens,
                timeout=settings.meal_planner_timeout
            )
            print(f"✅ MealPlannerAgent LLM 초기화: {settings.meal_planner_provider}/{settings.meal_planner_model}")
        except Exception as e:
            print(f"❌ MealPlannerAgent LLM 초기화 실패: {e}")
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
        fast_mode: bool = True,  # 빠른 모드 기본 활성화
        global_used_groups: Optional[set] = None  # 🆕 전역 다양성 그룹
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
            
            # 🆕 전역 다양성 추적을 위한 재료 그룹 세트
            global_used_ingredient_groups = set()
            
            # 1단계: 임베딩된 데이터에서 식단표 생성 시도
            print("🔍 1단계: 임베딩된 레시피 데이터에서 식단표 생성 시도")
            embedded_plan = await self._generate_meal_plan_from_embeddings(days, constraints_text, user_id, fast_mode,
                                                                          allergies=allergies, dislikes=dislikes,
                                                                          global_used_groups=global_used_ingredient_groups)
            
            # 🆕 1단계에서 사용된 그룹 정보를 업데이트
            if embedded_plan and 'used_groups' in embedded_plan:
                global_used_ingredient_groups.update(embedded_plan['used_groups'])
                # print(f"🔍 1단계 완료 후 사용된 그룹: {sorted(global_used_ingredient_groups)}")  # 디버그용 제거
            
            # 1단계 결과가 있으면 (완전 성공 or 부분 성공)
            if embedded_plan and len(embedded_plan.get("days", [])) > 0:
                embedded_days = embedded_plan.get("days", [])
                
                # None 슬롯이 있는지 확인
                has_missing = any(
                    meal is None 
                    for day_meals in embedded_days 
                    for meal in day_meals.values()
                )
                
                if not has_missing:
                    # 완전 성공: 모든 슬롯 채워짐
                    print(f"✅ 1단계 완전 성공: 모든 슬롯 DB에서 찾음")
                    return embedded_plan
                
                # 2단계: 부족한 슬롯만 AI로 메뉴명 생성(placeholder 금지)
                print("🔍 2단계: 1단계 결과에서 부족한 부분만 AI로 메뉴명 생성")
                
                # 알레르기와 비선호 정보를 constraints에 명시
                fill_constraints = constraints_text
                if allergies:
                    allergy_list = ', '.join(allergies)
                    fill_constraints += f"\n\n🚨 알레르기 재료 (절대 사용 금지): {allergy_list}"
                if dislikes:
                    dislike_list = ', '.join(dislikes)
                    fill_constraints += f"\n❌ 비선호 재료 (가능한 피할 것): {dislike_list}"
                
                # structure.py로 구조 생성 (부족한 슬롯용)
                meal_structure = await self._plan_meal_structure(days, fill_constraints)
                
                # 1단계 결과의 None 슬롯만 채움 (AI 1회 생성, 실패 시 해당 슬롯만 no_result 처리)
                second_stage_missing = False
                second_stage_missing_slots: List[Dict[str, Any]] = []
                for day_idx, day_meals in enumerate(embedded_days):
                    for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                        if day_meals.get(slot) is None and day_idx < len(meal_structure):
                            # AI로 생성된 메뉴명 사용
                            menu_name = meal_structure[day_idx].get(f"{slot}_type")
                            if not menu_name or len(menu_name.strip()) < 3:
                                second_stage_missing = True
                                # 즉시 해당 슬롯만 no_result로 채워서 부분 실패로 반환
                                day_meals[slot] = {
                                    "type": "no_result",
                                    "title": "추천 식단이 없습니다😢",
                                    "reason": "구체적인 메뉴명을 생성하지 못했습니다",
                                    "tips": [
                                        "비선호 일부 완화(2~3개 해제)",
                                        "단백질 위주 키워드로 재시도(계란/닭가슴살/돼지고기)",
                                        "탄수 제한 +5~10g 완화",
                                        "기간 7일 → 3일로 단축 후 재시도"
                                    ]
                                }
                                second_stage_missing_slots.append({"day": day_idx+1, "slot": slot})
                                print(f"  ⚠️ {day_idx+1}일차 {slot}: AI 생성 부적절('{menu_name}') → 해당 슬롯만 no_result 처리")
                            else:
                                day_meals[slot] = {
                                    "type": "simple",
                                    "title": menu_name
                                }
                                print(f"  ✅ {day_idx+1}일차 {slot}: AI 생성 '{menu_name}'")
                
                # 2단계 결과 반환: 실패 슬롯이 있어도 부분 실패로 바로 반환(추가 재생성 없음)
                print(f"✅ 2단계 완료: 부분 실패 슬롯 수={len(second_stage_missing_slots)}")
                if second_stage_missing_slots:
                    # 키토 팁(notes) 추가(중복 문구 제거)
                    tips = [
                        "비선호 일부 완화(2~3개 해제)",
                        "단백질 위주 키워드로 재시도(계란/닭가슴살/돼지고기)",
                        "탄수 제한 +5~10g 완화",
                        "기간 7일 → 3일로 단축 후 재시도"
                    ]
                    note_lines = [
                        f"알레르기: {', '.join(allergies or []) or '없음'} | 비선호: {', '.join(dislikes or []) or '없음'} | 목표: {kcal_target or '-'}kcal, 탄수 {carbs_max}g"
                    ]
                    embedded_plan.setdefault("notes", [])
                    embedded_plan["notes"].extend(note_lines + ["가이드: " + "; ".join(tips)])
                    embedded_plan["missing_slots"] = second_stage_missing_slots
                return embedded_plan
            
            # 1단계 완전 실패 시 → 2단계로 넘어가지 않고 바로 3단계로
            print("⚠️ 1단계 실패: DB에서 아무것도 못 찾음")
            
            # 3단계: DB에 없으니 완전히 새로 생성 (알레르기/비선호 반영)
            print("🎨 3단계: DB에 없음, structure.py로 전체 식단표 생성 (알레르기/비선호 반영)")
            
            # 알레르기와 비선호 정보를 constraints에 강하게 명시
            full_constraints = constraints_text
            if allergies:
                allergy_list = ', '.join(allergies)
                full_constraints += f"\n\n🚨 알레르기 재료 (절대 사용 금지): {allergy_list}"
            if dislikes:
                dislike_list = ', '.join(dislikes)
                full_constraints += f"\n❌ 비선호 재료 (가능한 피할 것): {dislike_list}"
            
            # structure.py 프롬프트로 완전한 식단표 생성
            full_meal_structure = await self._plan_meal_structure(days, full_constraints)

            # 프롬프트 생성이 비어있거나 실패한 경우: 무결과 안내 반환
            if not full_meal_structure:
                return {
                    "type": "no_result",
                    "title": "추천 식단이 없습니다",
                    "reason": "알레르기/비선호 조건이 많거나 너무 엄격합니다",
                    "constraints": {
                        "allergies": allergies or [],
                        "dislikes": dislikes or [],
                        "goals_kcal": kcal_target,
                        "goals_carbs_g": carbs_max
                    },
                    "tips": [
                        "비선호 일부 완화(2~3개 해제)",
                        "단백질 위주 키워드로 재시도(계란/닭가슴살/돼지고기)",
                        "탄수 제한 +5~10g 완화",
                        "7일 → 3일로 기간 단축"
                    ]
                }
            
            # 구조를 식단표 형태로 변환(placeholder 금지, 슬롯별 부분 실패 허용)
            full_plan = []
            missing_slots: List[Dict[str, Any]] = []
            
            # 🆕 3단계에서도 다양성 필터링 적용
            used_ingredient_groups_3rd = global_used_ingredient_groups.copy() if global_used_ingredient_groups else set()
            
            for day_idx, day_plan in enumerate(full_meal_structure):
                day_meals = {
                    "breakfast": None,
                    "lunch": None,
                    "dinner": None,
                    "snack": None
                }
                for slot in ['breakfast','lunch','dinner','snack']:
                    name = day_plan.get(f"{slot}_type")
                    print(f"🔍 3단계 {day_idx+1}일차 {slot}: name='{name}', 길이={len(name.strip()) if name else 0}")
                    if name and len(name.strip()) >= 3:
                        # 🆕 3단계 다양성 필터링 적용
                        def get_main_ingredient_group_3rd(title):
                            """메뉴 제목에서 주요 재료 그룹 추출 (3단계용)"""
                            title_lower = title.lower()
                            
                            # 계란 그룹 (완전 포괄적인 키워드)
                            if any(keyword in title_lower for keyword in ['달걀', '계란', 'egg', '에그', '계란말이', '달걀찜', '스크램블', 'scramble', '달갈', '계란볶음', '달걀볶음', '계란샐러드', '달걀샐러드', '삶은달걀', '삶은계란', '프리타타', 'frittata', '지단', '계란지단', '달걀지단', '오믈렛', 'omelette', '동그랑땡', '동그랑떵', '계란탕']):
                                return 'egg_group'
                            
                            # 닭고기 그룹
                            if any(keyword in title_lower for keyword in ['닭', '치킨', '닭가슴', '닭다리', '닭날개']):
                                return 'chicken_group'
                            
                            # 돼지고기 그룹
                            if any(keyword in title_lower for keyword in ['돼지', '돼지고기', '삼겹', '목살', '베이컨']):
                                return 'pork_group'
                            
                            # 소고기 그룹
                            if any(keyword in title_lower for keyword in ['소고기', '소', '한우', '쇠고기', '스테이크']):
                                return 'beef_group'
                            
                            # 생선 그룹
                            if any(keyword in title_lower for keyword in ['생선', '연어', '참치', '고등어', '광어', '오징어']):
                                return 'fish_group'
                            
                            # 김밥 그룹
                            if any(keyword in title_lower for keyword in ['김밥', '초밥', '롤']):
                                return 'gimbap_group'
                            
                            # 샐러드 그룹
                            if any(keyword in title_lower for keyword in ['샐러드', '무침', '채소']):
                                return 'salad_group'
                            
                            # 기타 (고유 그룹)
                            return f'other_{hash(title) % 1000}'
                        
                        # 다양성 필터링 체크
                        ingredient_group = get_main_ingredient_group_3rd(name)
                        print(f"🔍 3단계 {day_idx+1}일차 {slot}: '{name}' → 그룹: {ingredient_group}")
                        print(f"    📊 현재 사용된 그룹들: {sorted(used_ingredient_groups_3rd)}")
                        
                        if ingredient_group not in used_ingredient_groups_3rd:
                            # 다양성 필터링 통과
                            used_ingredient_groups_3rd.add(ingredient_group)
                            day_meals[slot] = {"title": name, "type": "simple"}
                            print(f"    ✅ 다양성 필터링 통과")
                        else:
                            # 다양성 필터링 실패 - 다른 메뉴로 대체
                            day_meals[slot] = {
                                "type": "no_result",
                                "title": "추천 식단이 없습니다",
                                "reason": f"다양성을 위해 '{name}' 대신 다른 메뉴를 추천합니다",
                                "tips": ["다른 재료 그룹의 메뉴를 선택해주세요"]
                            }
                            print(f"    ❌ 다양성 필터링 실패 - 이미 사용된 그룹")
                    else:
                        # 슬롯별 부분 실패: 사유/가이드 포함해 표시
                        day_meals[slot] = {
                            "type": "no_result",
                            "title": "추천 식단이 없습니다",
                            "reason": "프로필에 있는 정보를 기반으로 식단표를 생성하지 못했습니다",
                            "tips": [
                                "비선호 일부 완화(2~3개 해제)",
                                "단백질 위주 키워드로 재시도(계란/닭가슴살/돼지고기)",
                                "탄수 제한 +5~10g 완화",
                                "기간 7일 → 3일로 단축 후 재시도"
                            ]
                        }
                        missing_slots.append({"slot": slot, "reason": "generic_or_empty"})
                full_plan.append(day_meals)
            

            # 기본 조언 생성 (notes.py 프롬프트 사용)
            notes = await self._generate_meal_notes(full_plan, constraints_text)
            
            print(f"✅ 3단계 완료: {days}일 식단 생성 (부분 실패 슬롯 수: {len(missing_slots)})")
            if missing_slots:
                notes.extend([
                    f"알레르기: {', '.join(allergies or []) or '없음'} | 비선호: {', '.join(dislikes or []) or '없음'} | 목표: {kcal_target or '-'}kcal, 탄수 {carbs_max}g",
                    "가이드: 비선호 일부 완화(2~3개), 단백질 위주 키워드(계란/닭가슴살/돼지고기), 탄수 +5~10g, 기간 7일→3일"
                ])
            return {
                "days": full_plan,
                "duration_days": days,
                "total_macros": {
                    "kcal": 0,
                    "carb": 0,
                    "protein": 0,
                    "fat": 0
                },
                "notes": notes,
                "missing_slots": missing_slots,
                "constraints": {
                    "kcal_target": kcal_target,
                    "carbs_max": carbs_max,
                    "allergies": allergies or [],
                    "dislikes": dislikes or []
                }
            }
            
        except Exception as e:
            print(f"Meal planning error: {e}")
            # 예외 발생 시에도 무결과 안내를 반환(사유/가이드 포함)
            return {
                "type": "no_result",
                "title": "추천 식단이 없습니다",
                "reason": "식단 생성 중 오류가 발생했습니다",
                "constraints": {
                    "goals_kcal": kcal_target,
                    "goals_carbs_g": carbs_max,
                    "allergies": allergies or [],
                    "dislikes": dislikes or []
                },
                "tips": [
                    "잠시 후 다시 시도",
                    "비선호 일부 완화(2~3개 해제)",
                    "단백질 위주 키워드로 재시도(계란/닭가슴살/돼지고기)",
                    "탄수 제한 +5~10g 완화",
                    "7일 → 3일로 기간 단축"
                ]
            }
    
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
            # 하이브리드 검색 실행 (알레르기/비선호 필터링 포함)
            search_results = await hybrid_search_tool.search(
                query=search_query,
                profile=constraints,
                max_results=min(max_results * 3, 50),  # 더 많이 가져오기
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
                    # print(f"  ✅ 수집: {result.get('title', 'Unknown')} (ID: {recipe_id})")
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
    
    async def _search_with_diversity_optimized(
        self,
        search_query: str,
        constraints: str,
        user_id: Optional[str],
        used_recipes: set,
        max_results: int = 35,
        processed_allergies: Optional[List[str]] = None,
        processed_dislikes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        최적화된 다양성 검색 (알레르기/비선호 정보 재사용)

        Args:
            search_query: 검색 쿼리
            constraints: 제약 조건
            user_id: 사용자 ID
            used_recipes: 이미 사용된 레시피 ID 집합
            max_results: 최대 결과 수
            processed_allergies: 사전 처리된 알레르기 목록
            processed_dislikes: 사전 처리된 비선호 목록

        Returns:
            중복되지 않은 레시피 목록
        """
        try:
            # 하이브리드 검색 실행 (사전 처리된 알레르기/비선호 정보 사용)
            search_results = await hybrid_search_tool.search(
                query=search_query,
                profile=constraints,
                max_results=min(max_results * 3, 50),  # 더 많이 가져오기
                user_id=user_id,
                allergies=processed_allergies,
                dislikes=processed_dislikes
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
                    # print(f"  ✅ 수집: {result.get('title', 'Unknown')} (ID: {recipe_id})")
                    if len(unique_results) >= max_results:
                        break
                else:
                    if recipe_id:
                        print(f"  ⚠️ 중복 제외: {result.get('title', 'Unknown')} (ID: {recipe_id})")

            print(f"🔍 _search_with_diversity_optimized 결과: 검색 {len(search_results)}개 → 중복제거 후 {len(unique_results)}개")
            return unique_results
            
        except Exception as e:
            print(f"❌ 최적화된 다양성 검색 실패: {e}")
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
                    "primary_keywords": ["아침", "브런치", "닭가슴살", "두부", "베이컨"],  # 계란 키워드 완전 제거
                    "secondary_keywords": ["아보카도", "치즈", "버터", "연어", "소시지"],  # 계란 관련 키워드 완전 제거
                    "cooking_methods": ["구이", "볶음", "찜", "스튜"],  # 계란 조리법 완전 제거
                    "time_keywords": ["아침", "브런치", "모닝"],
                    "variety_keywords": [  # 🆕 다양성 키워드 - 계란 완전 제거
                        ["닭가슴살", "돼지고기"],  # 단백질 다양성
                        ["베이컨", "소시지"],      # 육류 다양성
                        ["아보카도", "토마토"],    # 채소 다양성
                        ["치즈", "버터"],          # 유제품 다양성
                        ["두부", "연어"],          # 추가 단백질 다양성
                        ["샐러드", "구이"],        # 조리법 다양성
                        ["김밥", "롤"],            # 형태 다양성
                        ["찜", "스튜"]             # 계란 대신 다른 조리법
                    ]
                },
                "lunch": {
                    "primary_keywords": ["점심", "샐러드", "구이"],
                    "secondary_keywords": ["스테이크", "생선", "고기", "볶음"],
                    "cooking_methods": ["그릴", "찜", "스튜", "볶음"],
                    "time_keywords": ["점심", "런치", "미들데이"],
                    "variety_keywords": [  # 🆕 다양성 키워드 추가
                        ["소고기", "돼지고기"],  # 단백질 다양성
                        ["연어", "참치"],        # 생선 다양성
                        ["샐러드", "볶음"],      # 조리법 다양성
                        ["김밥", "롤"]          # 형태 다양성
                    ]
                },
                "dinner": {
                    "primary_keywords": ["저녁", "고기", "생선"],
                    "secondary_keywords": ["삼겹살", "연어", "찜", "구이"],
                    "cooking_methods": ["구이", "찜", "스튜", "그릴"],
                    "time_keywords": ["저녁", "디너", "이브닝"],
                    "variety_keywords": [  # 🆕 다양성 키워드 추가
                        ["삼겹살", "목살"],      # 돼지고기 다양성
                        ["연어", "고등어"],     # 생선 다양성
                        ["스테이크", "구이"],   # 조리법 다양성
                        ["찜", "스튜"]         # 조리법 다양성
                    ]
                },
                "snack": {
                    "primary_keywords": ["간식", "두부", "곤약", "해초"],
                    "secondary_keywords": ["단백질", "저탄수", "무설탕", "다이어트"],
                    "cooking_methods": ["구이", "볶음", "찜"],
                    "time_keywords": ["간식", "스낵", "애프터눈"],
                    "variety_keywords": [  # 🆕 다양성 키워드 추가
                        ["두부", "치즈"],        # 단백질 다양성
                        ["곤약", "해초"],        # 저칼로리 다양성
                        ["머핀", "스콘"],        # 형태 다양성
                        ["무설탕", "천연감미료"] # 감미료 다양성
                    ]
                }
            },
            "diversity_strategy": "매일 다른 키워드 조합과 다양한 검색어 사용",
            "search_priority": ["variety_keywords", "primary_keywords", "cooking_methods", "secondary_keywords"]
        }
    
    async def _generate_meal_plan_from_embeddings(self, days: int, constraints: str, user_id: Optional[str] = None, fast_mode: bool = True,
                                                  allergies: Optional[List[str]] = None, dislikes: Optional[List[str]] = None, 
                                                  global_used_groups: Optional[set] = None) -> Optional[Dict[str, Any]]:
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
            # print(f"🔍 DEBUG: 함수 시작 - days={days}, constraints='{constraints[:50]}...', user_id={user_id}")  # 임시 비활성화
            
            # 임베딩 기반 프롬프트 사용
            embedding_prompt = self.prompts.get("embedding_based", "").format(
                days=days,
                constraints=constraints
            )
            
            # 빠른 모드에 따른 전략 선택
            if fast_mode:
                # print("⚡ 빠른 검색 모드: 기본 전략 사용")  # 임시 비활성화
                meal_strategies = self._get_default_meal_strategies()["meal_strategies"]
            else:
                # print("🤖 AI 검색 모드: AI 전략 생성")  # 임시 비활성화
                ai_strategies = await self._generate_ai_meal_strategies(days, constraints)
                meal_strategies = ai_strategies.get("meal_strategies", self._get_default_meal_strategies()["meal_strategies"])
            
            # 효율적인 검색: 식사별로 한 번에 여러 개 검색
            meal_plan_days = []
            used_recipes = set()  # 중복 방지용
            
            # 각 식사별로 한 번에 여러 개 검색
            meal_collections = {}
            
            # 🆕 계란 레시피 1개만 미리 선별 (랜덤 배치용)
            egg_breakfast_recipe = None
            egg_day = None  # 계란을 배치할 날짜
            
            if days > 0:  # 최소 1일 이상일 때만
                # 계란 포함 확률 결정
                if days == 1:
                    include_egg = random.random() < 0.5  # 50% 확률
                else:
                    include_egg = True  # 2일 이상이면 무조건 포함
                
                if include_egg:
                    # 계란 레시피 검색
                    egg_search_results = await hybrid_search_tool.search(
                        query="계란 달걀 스크램블 오믈렛 키토 아침",
                        profile=constraints,
                        max_results=10,
                        user_id=user_id,
                        allergies=allergies,
                        dislikes=dislikes
                    )
                    if egg_search_results:
                        egg_breakfast_recipe = random.choice(egg_search_results)
                        egg_day = random.randint(0, days - 1)  # 랜덤 날짜 선택
                        # print(f"🥚 계란 레시피 선별: '{egg_breakfast_recipe.get('title', '')}' → {egg_day + 1}일차 아침")  # 디버그용 제거
                        
                        # 🆕 계란 레시피를 used_recipes에 미리 추가하여 다른 검색에서 제외
                        egg_recipe_id = egg_breakfast_recipe.get('id', f"egg_breakfast_{egg_day}")
                        used_recipes.add(egg_recipe_id)
                        # print(f"🚫 계란 레시피 ID '{egg_recipe_id}' 미리 제외 처리")  # 디버그용 제거
            
            # 알레르기/비선호 정보를 한 번만 처리하여 재사용
            # print(f"🔍 알레르기/비선호 정보 사전 처리 시작")  # 임시 비활성화
            processed_allergies = allergies or []
            processed_dislikes = dislikes or []
            # print(f"  - 알레르기: {processed_allergies}")  # 임시 비활성화
            # print(f"  - 비선호: {processed_dislikes}")  # 임시 비활성화
            
            # 병렬 검색을 위한 태스크 생성
            import asyncio
            
            async def search_slot(slot, strategy):
                """개별 식사 슬롯 검색 (병렬 실행용)"""
                # print(f"🔍 {slot} 레시피 {days}개 검색 중...")  # 임시 비활성화
                
                # 다양성을 위해 여러 검색 전략 시도
                all_search_results = []
                
                # 변수 초기화 (스코프 문제 해결)
                basic_results = []
                variety_results = []
                cooking_results = []
                total_variety_count = 0  # 전체 다양성 검색 결과 수
                
                # 1. 기본 키워드 검색 (알레르기 필터링 고려하여 증가)
                basic_query = f"{' '.join(strategy['primary_keywords'])} 키토"
                
                # 🆕 아침의 경우 계란 키워드 완전 제외
                if slot == 'breakfast':
                    basic_query = basic_query.replace('계란', '').replace('달걀', '').replace('스크램블', '').replace('오믈렛', '')
                    basic_query += ' 닭가슴살 두부 베이컨 연어'  # 계란 대신 다른 단백질 키워드 추가
                    # print(f"🚫 아침 검색 쿼리 (계란 제외): '{basic_query}'")  # 디버그용 제거
                else:
                    # print(f"🔍 DEBUG: {slot} 기본 검색어: '{basic_query}'")  # 디버그용 제거
                    pass
                
                basic_results = await self._search_with_diversity_optimized(
                    basic_query, constraints, user_id, used_recipes, max_results=days * 4,  # 2 → 4로 증가
                    processed_allergies=processed_allergies, processed_dislikes=processed_dislikes
                )
                all_search_results.extend(basic_results)
                
                # 2. 다양성 키워드 검색 (알레르기 필터링 고려하여 증가)
                if 'variety_keywords' in strategy and len(all_search_results) < days * 3:
                    # 모든 다양성 키워드 그룹을 순회하며 검색
                    for i, variety_group in enumerate(strategy['variety_keywords']):
                        variety_query = f"{' '.join(variety_group)} 키토"
                        
                        # 🆕 아침의 경우 계란 키워드 완전 제외
                        if slot == 'breakfast':
                            variety_query = variety_query.replace('계란', '').replace('달걀', '').replace('스크램블', '').replace('오믈렛', '')
                            variety_query += ' 닭가슴살 두부 베이컨 연어'  # 계란 대신 다른 단백질 키워드 추가
                            # print(f"🚫 아침 다양성 검색 쿼리 (계란 제외): '{variety_query}'")  # 디버그용 제거
                        else:
                            # print(f"🔍 DEBUG: {slot} 다양성 검색어 {i+1}: '{variety_query}'")  # 디버그용 제거
                            pass
                        
                        variety_results = await self._search_with_diversity_optimized(
                            variety_query, constraints, user_id, used_recipes, max_results=2,  # 각 그룹당 2개씩
                            processed_allergies=processed_allergies, processed_dislikes=processed_dislikes
                        )
                        all_search_results.extend(variety_results)
                        total_variety_count += len(variety_results)  # 다양성 결과 수 누적
                        
                        # 충분한 결과가 있으면 중단
                        if len(all_search_results) >= days * 3:
                            break
                
                # 3. 조리법 기반 검색 (알레르기 필터링 고려하여 증가)
                if 'cooking_methods' in strategy and len(all_search_results) < days * 3:
                    cooking_query = f"{' '.join(strategy['cooking_methods'][:2])} 키토 {slot}"  # 3 → 2로 감소
                    
                    # 🆕 아침의 경우 계란 키워드 완전 제외
                    if slot == 'breakfast':
                        cooking_query = cooking_query.replace('계란', '').replace('달걀', '').replace('스크램블', '').replace('오믈렛', '')
                        cooking_query += ' 닭가슴살 두부 베이컨 연어'  # 계란 대신 다른 단백질 키워드 추가
                        # print(f"🚫 아침 조리법 검색 쿼리 (계란 제외): '{cooking_query}'")  # 디버그용 제거
                    else:
                        # print(f"🔍 DEBUG: {slot} 조리법 검색어: '{cooking_query}'")  # 디버그용 제거
                        pass
                    
                    cooking_results = await self._search_with_diversity_optimized(
                        cooking_query, constraints, user_id, used_recipes, max_results=4,  # 2 → 4로 증가
                        processed_allergies=processed_allergies, processed_dislikes=processed_dislikes
                    )
                    all_search_results.extend(cooking_results)
                
                if all_search_results:
                    # 효율적인 중복 제거 (ID 기준) - dict comprehension 사용
                    seen_ids = set()
                    unique_results = [
                        result for result in all_search_results
                        if (result_id := result.get('id', '')) and result_id not in seen_ids and not seen_ids.add(result_id)
                    ]
                    
                    # 🆕 아침의 경우 계란 관련 레시피 추가 필터링
                    if slot == 'breakfast':
                        def is_egg_related(title):
                            """계란 관련 레시피인지 확인"""
                            title_lower = title.lower()
                            egg_keywords = ['달걀', '계란', 'egg', '에그', '계란말이', '달걀찜', '스크램블', 'scramble', '달갈', '계란볶음', '달걀볶음', '계란샐러드', '달걀샐러드', '삶은달걀', '삶은계란', '프리타타', 'frittata', '지단', '계란지단', '달걀지단', '오믈렛', 'omelette', '동그랑땡', '동그랑떵', '계란탕']
                            return any(keyword in title_lower for keyword in egg_keywords)
                        
                        # 계란 관련 레시피 제외
                        non_egg_results = [r for r in unique_results if not is_egg_related(r.get('title', ''))]
                        
                        if non_egg_results:
                            # print(f"🚫 아침 계란 레시피 추가 필터링: {len(unique_results)} → {len(non_egg_results)}개")  # 디버그용 제거
                            # 제외된 계란 레시피들 로그 출력
                            egg_filtered = [r for r in unique_results if is_egg_related(r.get('title', ''))]
                            # for egg_recipe in egg_filtered:
                            #     print(f"    ❌ 계란 레시피 제외: '{egg_recipe.get('title', '')}'")  # 디버그용 제거
                            unique_results = non_egg_results
                        else:
                            # print(f"⚠️ 비계란 레시피 없음 - 원본 사용")  # 디버그용 제거
                            pass
                    
                    # print(f"✅ {slot} 레시피 {len(unique_results)}개 수집 완료 (다양성 검색 적용)")  # 디버그용 제거
                    # print(f"    🔍 검색 전략별 결과: 기본={len(basic_results)}, 다양성={total_variety_count}, 조리법={len(cooking_results) if 'cooking_methods' in strategy else 0}")  # 디버그용 제거
                    return slot, unique_results
                else:
                    # print(f"❌ {slot} 레시피 검색 실패")  # 디버그용 제거
                    return slot, []
            
            # 모든 식사 슬롯을 병렬로 검색
            # print(f"🚀 {len(meal_strategies)}개 식사 슬롯 병렬 검색 시작...")  # 디버그용 제거
            search_tasks = [
                search_slot(slot, strategy) 
                for slot, strategy in meal_strategies.items()
            ]
            
            # 병렬 실행
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 결과 정리
            for result in search_results:
                if isinstance(result, Exception):
                    print(f"❌ 검색 오류: {result}")
                    continue
                
                slot, results = result
                meal_collections[slot] = results
            
            # 7일 식단표 구성 (다양성 보장) - 부분 성공도 허용
            missing_count = 0  # 못 찾은 슬롯 개수
            
            # 메뉴 다양성을 위한 재료 그룹 추적 (전체 식단 기준)
            used_ingredient_groups = global_used_groups if global_used_groups is not None else set()  # 전역 그룹 사용
            
            for day in range(days):
                day_meals = {}
                
                for slot in meal_strategies.keys():
                    # 🆕 랜덤으로 선택된 날짜의 아침에 계란 레시피 배치
                    if slot == 'breakfast' and day == egg_day and egg_breakfast_recipe:
                        # print(f"🥚 {day + 1}일차 아침: 계란 레시피 배치 - '{egg_breakfast_recipe.get('title', '')}'")  # 디버그용 제거
                        day_meals[slot] = {
                            "type": "recipe",
                            "id": egg_breakfast_recipe.get("id", ""),
                            "title": egg_breakfast_recipe.get("title", ""),
                            "macros": egg_breakfast_recipe.get("macros", {}),
                            "ingredients": egg_breakfast_recipe.get("ingredients", []),
                            "steps": egg_breakfast_recipe.get("steps", []),
                            "tips": egg_breakfast_recipe.get("tips", [])
                        }
                        used_recipes.add(egg_breakfast_recipe.get('id', f"egg_breakfast_{day}"))
                        continue
                    elif slot == 'breakfast' and day != egg_day:
                        # print(f"🚫 {day + 1}일차 아침: 계란 레시피 배치 안됨 (선택된 날짜: {egg_day + 1}일차)")  # 디버그용 제거
                        pass
                    
                    if slot in meal_collections and len(meal_collections[slot]) > 0:
                        # 중복 방지를 위해 선택된 레시피를 컬렉션에서 제거
                        available_recipes = meal_collections[slot]
                        
                        # 아직 사용되지 않은 레시피만 필터링 (더 정확한 필터링)
                        unused_recipes = []
                        for r in available_recipes:
                            recipe_id = r.get('id', f"embedded_{slot}_{day}")
                            if recipe_id not in used_recipes:
                                unused_recipes.append(r)
                        
                        # print(f"🔍 {day+1}일차 {slot}: 사용 가능한 레시피 {len(available_recipes)}개, 미사용 {len(unused_recipes)}개")  # 디버그용 제거
                        
                        # 🔍 아침 레시피는 이미 계란 키워드가 제외된 상태로 검색됨
                        
                        if unused_recipes:
                            # 🆕 재료 그룹 기반 다양성 필터링
                            def get_main_ingredient_group(title):
                                """메뉴 제목에서 주요 재료 그룹 추출"""
                                title_lower = title.lower()
                                
                                # 계란 그룹 (완전 포괄적인 키워드)
                                if any(keyword in title_lower for keyword in ['달걀', '계란', 'egg', '에그', '계란말이', '달걀찜', '스크램블', 'scramble', '달갈', '계란볶음', '달걀볶음', '계란샐러드', '달걀샐러드', '삶은달걀', '삶은계란', '프리타타', 'frittata', '지단', '계란지단', '달걀지단', '오믈렛', 'omelette', '동그랑땡', '동그랑떵', '계란탕']):
                                    return 'egg_group'
                                
                                # 닭고기 그룹
                                if any(keyword in title_lower for keyword in ['닭', '치킨', '닭가슴', '닭다리', '닭날개']):
                                    return 'chicken_group'
                                
                                # 돼지고기 그룹
                                if any(keyword in title_lower for keyword in ['돼지', '돼지고기', '삼겹', '목살', '베이컨']):
                                    return 'pork_group'
                                
                                # 소고기 그룹
                                if any(keyword in title_lower for keyword in ['소고기', '소', '한우', '쇠고기', '스테이크']):
                                    return 'beef_group'
                                
                                # 생선 그룹
                                if any(keyword in title_lower for keyword in ['생선', '연어', '참치', '고등어', '광어', '오징어']):
                                    return 'fish_group'
                                
                                # 김밥 그룹
                                if any(keyword in title_lower for keyword in ['김밥', '초밥', '롤']):
                                    return 'gimbap_group'
                                
                                # 샐러드 그룹
                                if any(keyword in title_lower for keyword in ['샐러드', '무침', '채소']):
                                    return 'salad_group'
                                
                                # 기타 (고유 그룹)
                                return f'other_{hash(title) % 1000}'
                            
                            # 이미 사용된 재료 그룹 제외 (더 강력한 필터링)
                            filtered_recipes = []
                            print(f"    🔍 {slot} 다양성 필터링 시작 - 사용된 그룹: {sorted(used_ingredient_groups)}")
                            print(f"    🚨 강제 디버그: used_ingredient_groups 타입={type(used_ingredient_groups)}, 길이={len(used_ingredient_groups)}")
                            
                            # 간단한 다양성 필터링
                            for recipe in unused_recipes:
                                title = recipe.get('title', '')
                                ingredient_group = get_main_ingredient_group(title)
                                # print(f"      📝 '{title}' → 그룹: {ingredient_group}")  # 디버그용 제거
                                
                                if ingredient_group not in used_ingredient_groups:
                                    filtered_recipes.append(recipe)
                                    # print(f"        ✅ 필터링 통과")  # 디버그용 제거
                                else:
                                    # print(f"        ❌ 필터링 제외 (이미 사용된 그룹)")  # 디버그용 제거
                                    pass
                            
                            # 필터링된 레시피가 있으면 사용
                            if filtered_recipes:
                                candidate_recipes = filtered_recipes
                                # print(f"    🔍 {slot} 다양성 필터링 성공: {len(unused_recipes)} → {len(filtered_recipes)}개")  # 디버그용 제거
                            else:
                                # 필터링된 레시피가 없으면 원래 레시피 사용하되 경고
                                candidate_recipes = unused_recipes
                                # print(f"    ⚠️ {slot} 다양성 필터링 실패: 모든 레시피가 이미 사용된 그룹")  # 디버그용 제거
                            
                            # 다양성을 위해 더 복잡한 선택 전략 적용
                            if day % 3 == 0:
                                # 3일마다: 유사도 기반 선택 (상위 5개 중 랜덤)
                                candidate_recipes.sort(key=lambda x: x.get('similarity', 0.0), reverse=True)
                                top_recipes = candidate_recipes[:min(5, len(candidate_recipes))]
                                selected_recipe = random.choice(top_recipes)
                            elif day % 3 == 1:
                                # 3일마다: 완전 랜덤 선택
                                selected_recipe = random.choice(candidate_recipes)
                            else:
                                # 3일마다: 중간 유사도 선택 (다양성 극대화)
                                candidate_recipes.sort(key=lambda x: x.get('similarity', 0.0), reverse=True)
                                mid_start = len(candidate_recipes) // 3
                                mid_end = (len(candidate_recipes) * 2) // 3
                                mid_recipes = candidate_recipes[mid_start:mid_end]
                                selected_recipe = random.choice(mid_recipes) if mid_recipes else random.choice(candidate_recipes)
                            
                            # 선택된 레시피의 재료 그룹을 사용된 그룹에 추가
                            selected_group = get_main_ingredient_group(selected_recipe.get('title', ''))
                            
                            # print(f"    🚨 그룹 추가 전: used_ingredient_groups={sorted(used_ingredient_groups)}")  # 디버그용 제거
                            used_ingredient_groups.add(selected_group)
                            # print(f"    🚨 그룹 추가 후: used_ingredient_groups={sorted(used_ingredient_groups)}")  # 디버그용 제거
                            # print(f"🔍 {day+1}일차 {slot}: '{selected_recipe.get('title', '')}' (그룹: {selected_group})")  # 디버그용 제거
                            # print(f"    📊 현재 사용된 그룹들: {sorted(used_ingredient_groups)}")  # 디버그용 제거
                            
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
                            "url": selected_recipe.get('url'),  # URL 추가
                            "metadata": selected_recipe.get('metadata', {}),
                            "allergens": selected_recipe.get('allergens', []),
                            "ingredients": selected_recipe.get('ingredients', [])
                        }
                        
                        print(f"✅ {slot}: {selected_recipe.get('title', 'Unknown')} (유사도: {selected_recipe.get('similarity', 0.0):.2f})")
                    else:
                        # 못 찾은 슬롯은 None으로 표시 (2단계에서 채움)
                        day_meals[slot] = None
                        missing_count += 1
                        print(f"⚠️ {slot}: 검색 결과 없음 (2단계에서 생성 예정)")
                
                meal_plan_days.append(day_meals)
            
            # 부분 성공도 반환 (2단계에서 채움)
            if len(meal_plan_days) == days:
                if missing_count > 0:
                    print(f"⚠️ 임베딩 데이터로 부분 성공: {missing_count}개 슬롯 부족 (2단계에서 생성)")
                else:
                    print(f"✅ 임베딩 데이터로 {days}일 식단표 생성 완전 성공")
                
                # 총 매크로 계산
                total_macros = self._calculate_total_macros(meal_plan_days)
                
                # 조언 생성
                notes = [
                    "검증된 레시피 데이터베이스에서 선별한 식단표입니다",
                    "하루 탄수화물은 20-50g 이하로 유지해주세요"
                ]
                
                return {
                    "days": meal_plan_days,
                    "duration_days": days,  # 요청된 일수 정보 추가
                    "total_macros": total_macros,
                    "notes": notes,
                    "source": "embeddings",
                    "used_groups": used_ingredient_groups,  # 🆕 사용된 재료 그룹 정보 추가
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
            import traceback
            print(f"🔍 DEBUG: 예외 상세 정보:")
            traceback.print_exc()
            return None
    
    async def _generate_detailed_meals_from_embeddings(self, structure: List[Dict[str, str]], constraints: str, user_id: Optional[str] = None, fast_mode: bool = True,
                                                       allergies: Optional[List[str]] = None, dislikes: Optional[List[str]] = None, 
                                                       global_used_groups: Optional[set] = None) -> Optional[Dict[str, Any]]:
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
            
            # 🆕 메뉴 다양성을 위한 재료 그룹 추적
            used_ingredient_groups = global_used_groups if global_used_groups is not None else set()
            
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
                    search_query, constraints, user_id, used_recipes, max_results=days_count * 5,  # 더 많은 후보
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
                            # 🆕 다양성 필터링 적용
                            def get_main_ingredient_group(title):
                                """메뉴 제목에서 주요 재료 그룹 추출"""
                                title_lower = title.lower()
                                
                                # 계란 그룹 (완전 포괄적인 키워드)
                                if any(keyword in title_lower for keyword in ['달걀', '계란', 'egg', '에그', '계란말이', '달걀찜', '스크램블', 'scramble', '달갈', '계란볶음', '달걀볶음', '계란샐러드', '달걀샐러드', '삶은달걀', '삶은계란', '프리타타', 'frittata', '지단', '계란지단', '달걀지단', '오믈렛', 'omelette', '동그랑땡', '동그랑떵', '계란탕']):
                                    return 'egg_group'
                                
                                # 닭고기 그룹
                                if any(keyword in title_lower for keyword in ['닭', '치킨', '닭가슴', '닭다리', '닭날개']):
                                    return 'chicken_group'
                                
                                # 돼지고기 그룹
                                if any(keyword in title_lower for keyword in ['돼지', '돼지고기', '삼겹', '목살', '베이컨']):
                                    return 'pork_group'
                                
                                # 소고기 그룹
                                if any(keyword in title_lower for keyword in ['소고기', '소', '한우', '쇠고기', '스테이크']):
                                    return 'beef_group'
                                
                                # 생선 그룹
                                if any(keyword in title_lower for keyword in ['생선', '연어', '참치', '고등어', '광어', '오징어']):
                                    return 'fish_group'
                                
                                # 김밥 그룹
                                if any(keyword in title_lower for keyword in ['김밥', '초밥', '롤']):
                                    return 'gimbap_group'
                                
                                # 샐러드 그룹
                                if any(keyword in title_lower for keyword in ['샐러드', '무침', '채소']):
                                    return 'salad_group'
                                
                                # 기타 (고유 그룹)
                                return f'other_{hash(title) % 1000}'
                            
                            # 사용 가능한 레시피들
                            available_recipes = meal_collections[slot]
                            
                            # 다양성 필터링 적용
                            filtered_recipes = []
                            print(f"    🔍 {day_idx+1}일차 {slot} 다양성 필터링 시작 - 사용된 그룹: {sorted(used_ingredient_groups)}")
                            
                            for recipe in available_recipes:
                                title = recipe.get('title', '')
                                ingredient_group = get_main_ingredient_group(title)
                                # print(f"      📝 '{title}' → 그룹: {ingredient_group}")  # 디버그용 제거
                                
                                if ingredient_group not in used_ingredient_groups:
                                    filtered_recipes.append(recipe)
                                    # print(f"        ✅ 필터링 통과")  # 디버그용 제거
                                else:
                                    # print(f"        ❌ 필터링 제외 (이미 사용된 그룹)")  # 디버그용 제거
                                    pass
                            
                            # 필터링된 레시피가 있으면 사용
                            if filtered_recipes:
                                candidate_recipes = filtered_recipes
                                print(f"    🔍 {slot} 다양성 필터링 성공: {len(available_recipes)} → {len(filtered_recipes)}개")
                            else:
                                # 필터링된 레시피가 없으면 원래 레시피 사용하되 경고
                                candidate_recipes = available_recipes
                                print(f"    ⚠️ {slot} 다양성 필터링 실패: 모든 레시피가 이미 사용된 그룹")
                            
                            # 랜덤 선택 적용
                            selected_recipe = random.choice(candidate_recipes)
                            
                            # 선택된 레시피의 재료 그룹을 사용된 그룹에 추가
                            selected_group = get_main_ingredient_group(selected_recipe.get('title', ''))
                            used_ingredient_groups.add(selected_group)
                            print(f"🔍 {day_idx+1}일차 {slot}: '{selected_recipe.get('title', '')}' (그룹: {selected_group})")
                            print(f"    📊 현재 사용된 그룹들: {sorted(used_ingredient_groups)}")
                            
                            recipe_id = selected_recipe.get('id', f"embedded_{slot}_{day_idx}")
                            used_recipes.add(recipe_id)
                            
                            day_meals[slot] = {
                                "type": "recipe",
                                "id": recipe_id,
                                "title": selected_recipe.get('title', f"키토 {slot}"),
                                "content": selected_recipe.get('content', ''),
                                "similarity": selected_recipe.get('similarity', 0.0),
                                "url": selected_recipe.get('url'),  # URL 추가
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
                    "AI가 생성한 검증된 레시피로 만든 맞춤 식단표입니다",
                    "하루 탄수화물은 20-50g 이하로 유지해주세요"
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
        
        # 폴백: 기본 구조 (계란 빈도 대폭 감소)
        return [
            {
                "day": i + 1,
                "breakfast_type": "계란 요리" if i % 7 == 0 else "닭가슴살 요리" if i % 7 == 1 else "두부 요리" if i % 7 == 2 else "베이컨 요리" if i % 7 == 3 else "연어 요리" if i % 7 == 4 else "샐러드" if i % 7 == 5 else "구이",  # 7일 중 1일만 계란
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
        
        # 아침 메뉴의 경우 계란 관련 키워드 완전 제외
        if slot == 'breakfast':
            if "계란" in meal_type:
                search_query = f"계란 달걀 스크램블 오믈렛 키토 {slot}"  # 계란 요리일 때만 계란 키워드 사용
            else:
                # 계란이 아닌 경우 계란 키워드 완전 제외하고 대안 키워드 사용
                search_query = f"{meal_type} 키토 {slot} 닭가슴살 두부 베이컨 연어"  # 계란 대신 다른 단백질 키워드 사용
        
        rag_results = await hybrid_search_tool.search(
            query=search_query,
            profile=constraints,
            max_results=10,  # 더 많이 가져와서 필터링
            user_id=getattr(self, '_current_user_id', None)  # 현재 사용자 ID 전달
        )
        
        if rag_results:
            # 아침 메뉴의 경우 계란 관련 레시피 제외
            if slot == 'breakfast' and "계란" not in meal_type:
                def is_egg_related(title):
                    """계란 관련 레시피인지 확인"""
                    title_lower = title.lower()
                    egg_keywords = ['달걀', '계란', 'egg', '에그', '계란말이', '달걀찜', '스크램블', 'scramble', '달갈', '계란볶음', '달걀볶음', '계란샐러드', '달걀샐러드', '삶은달걀', '삶은계란', '프리타타', 'frittata', '지단', '계란지단', '달걀지단', '오믈렛', 'omelette', '동그랑땡', '동그랑떵', '계란탕']
                    return any(keyword in title_lower for keyword in egg_keywords)
                
                # 계란 관련 레시피 제외
                non_egg_results = [r for r in rag_results if not is_egg_related(r.get('title', ''))]
                
                if non_egg_results:
                    # print(f"    🚫 아침 계란 레시피 제외: {len(rag_results)} → {len(non_egg_results)}개")  # 디버그용 제거
                    rag_results = non_egg_results
                else:
                    # print(f"    ⚠️ 비계란 레시피 없음 - 원본 사용")  # 디버그용 제거
                    pass
            
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
        """LLM을 통한 메뉴 생성 (골든셋 검증 적용)"""
        
        # 🆕 골든셋 기반 검증 시스템 사용
        try:
            from app.domains.recipe.services.recipe_validator import RecipeValidator
            
            # constraints 문자열을 딕셔너리로 변환
            constraints_dict = self._parse_constraints_string(constraints)
            
            # RecipeValidator로 검증된 레시피 생성
            validator = RecipeValidator()
            result = await validator.generate_validated_recipe(
                meal_type=meal_type,
                constraints=constraints_dict,
                user_id=getattr(self, '_current_user_id', None)
            )
            
            if result.get("success"):
                recipe = result.get("recipe", {})
                print(f"✅ 골든셋 검증 완료: {recipe.get('title', 'Unknown')} (시도 {result.get('attempts', 0)}회)")
                
                # MealPlannerAgent 형식으로 변환
                return {
                    "type": "recipe",
                    "id": recipe.get("id", f"validated_{slot}_{hash(recipe.get('title', '')) % 10000}"),
                    "title": recipe.get("title", "키토 레시피"),
                    "macros": recipe.get("macros", {}),
                    "ingredients": recipe.get("ingredients", []),
                    "steps": recipe.get("steps", []),
                    "tips": [f"✅ 검증 완료 (시도 {result.get('attempts', 0)}회)"],
                    "source": "golden_validated",
                    "validation": result.get("validation", {})
                }
            else:
                print(f"⚠️ 골든셋 검증 실패, 기존 방식으로 폴백: {result.get('error', 'Unknown')}")
                # 기존 방식으로 폴백
                return await self._generate_llm_meal_legacy(slot, meal_type, constraints)
        
        except ImportError:
            print(f"⚠️ RecipeValidator 모듈 없음, 기존 방식 사용")
            return await self._generate_llm_meal_legacy(slot, meal_type, constraints)
        except Exception as e:
            print(f"⚠️ 골든셋 검증 오류: {e}, 기존 방식으로 폴백")
            return await self._generate_llm_meal_legacy(slot, meal_type, constraints)
    
    def _parse_constraints_string(self, constraints: str) -> Dict[str, Any]:
        """constraints 문자열을 딕셔너리로 변환"""
        
        constraints_dict = {
            "allergies": [],
            "dislikes": [],
            "kcal_target": None,
            "carbs_max": 30
        }
        
        # 간단한 파싱 (예: "알레르기: 새우 | 비선호 음식: 브로콜리")
        if "알레르기:" in constraints:
            allergy_part = constraints.split("알레르기:")[1].split("|")[0].strip()
            if allergy_part and allergy_part != "특별한 제약사항 없음":
                constraints_dict["allergies"] = [a.strip() for a in allergy_part.split(",") if a.strip()]
        
        if "비선호 음식:" in constraints or "싫어하는 음식:" in constraints:
            dislike_key = "비선호 음식:" if "비선호 음식:" in constraints else "싫어하는 음식:"
            dislike_part = constraints.split(dislike_key)[1].split("|")[0].strip()
            if dislike_part:
                constraints_dict["dislikes"] = [d.strip() for d in dislike_part.split(",") if d.strip()]
        
        if "목표 칼로리:" in constraints or "일일 목표 칼로리:" in constraints:
            kcal_key = "목표 칼로리:" if "목표 칼로리:" in constraints else "일일 목표 칼로리:"
            kcal_part = constraints.split(kcal_key)[1].split("|")[0].strip().replace("kcal", "").strip()
            try:
                constraints_dict["kcal_target"] = int(kcal_part)
            except ValueError:
                pass
        
        if "탄수화물:" in constraints or "최대 탄수화물:" in constraints:
            carbs_key = "탄수화물:" if "탄수화물:" in constraints else "최대 탄수화물:"
            carbs_part = constraints.split(carbs_key)[1].split("|")[0].strip().replace("g", "").strip()
            try:
                constraints_dict["carbs_max"] = int(carbs_part)
            except ValueError:
                pass
        
        return constraints_dict
    
    async def _generate_llm_meal_legacy(
        self,
        slot: str,
        meal_type: str,
        constraints: str
    ) -> Dict[str, Any]:
        """기존 LLM 메뉴 생성 방식 (폴백용)"""
        
        # 아침 메뉴의 경우 계란 요리는 그대로 유지 (빈도는 상위에서 제어)
        # meal_type은 그대로 사용
        
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
                meal_data["source"] = "llm_legacy"
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
            "tips": ["키토 원칙을 지켜주세요"],
            "source": "fallback"
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
                # 🚨 None 슬롯 처리 (부분 성공 시)
                if meal is None:
                    continue
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
    
    async def generate_single_recipe(self, message: str, profile_context: str = "", user_id: str = None) -> str:
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
                # profile_context를 우선 사용 (임시 불호 포함)
                allergies = []
                dislikes = []
                
                if profile_context:
                    # profile_context에서 파싱 (임시 불호 포함됨)
                    if "알레르기:" in profile_context:
                        allergy_part = profile_context.split("알레르기:")[1].split("|")[0]
                        allergies = [a.strip() for a in allergy_part.split(",") if a.strip() and a.strip() != "없음"]
                    
                    if "비선호 재료:" in profile_context:
                        dislike_part = profile_context.split("비선호 재료:")[1].split("|")[0]
                        dislikes = [d.strip() for d in dislike_part.split(",") if d.strip() and d.strip() != "없음"]
                    
                    print(f"🔍 레시피 검색 - 알레르기: {allergies}, 비선호: {dislikes}")
                elif user_id:
                    # profile_context가 없으면 DB에서 조회 (백업)
                    from app.tools.shared.profile_tool import user_profile_tool
                    user_preferences = await user_profile_tool.get_user_preferences(user_id)
                    
                    if user_preferences.get("success"):
                        prefs = user_preferences["preferences"]
                        allergies = prefs.get("allergies", [])
                        dislikes = prefs.get("dislikes", [])
                        print(f"🔍 레시피 검색 - 알레르기: {allergies}, 비선호: {dislikes}")
                
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
            url = result.get('url')  # URL 추가
            
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
            # URL이 있으면 추가
            if url:
                recipe_info += f"\n**출처 URL:** {url}\n"
                print(f"  ✅ 레시피 '{title}' URL 포함: {url}")
            else:
                print(f"  ⚠️ 레시피 '{title}' URL 없음")
            
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
    
    async def generate_personalized_meal_plan(self, user_id: str, days: int = 7, fast_mode: bool = True, global_used_groups: Optional[set] = None) -> Dict[str, Any]:
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
        
        # 🆕 전역 다양성 추적을 위한 재료 그룹 세트
        global_used_ingredient_groups = global_used_groups if global_used_groups is not None else set()
        
        # 현재 사용자 ID 저장 (검색 시 프로필 필터링용)
        self._current_user_id = user_id
        
        # 사용자 프로필 조회
        profile_result = await user_profile_tool.get_user_preferences(user_id)
        
        if not profile_result["success"]:
            print(f"⚠️ 프로필 조회 실패, 기본값으로 진행: {profile_result.get('error')}")
            return await self.generate_meal_plan(days=days, user_id=user_id, global_used_groups=global_used_ingredient_groups)
        
        prefs = profile_result["preferences"]
        
        # 프로필 정보로 식단 생성
        return await self.generate_meal_plan(
            days=days,
            kcal_target=prefs.get("goals_kcal"),
            carbs_max=prefs.get("goals_carbs_g", 30),
            allergies=prefs.get("allergies"),
            dislikes=prefs.get("dislikes"),
            user_id=user_id,
            fast_mode=fast_mode,
            global_used_groups=global_used_ingredient_groups  # 🆕 전역 그룹 전달
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
        
        return await self.generate_single_recipe(message, profile_context, user_id=user_id)
    
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
        
        # 🆕 전역 다양성 추적을 위한 재료 그룹 세트
        global_used_ingredient_groups = set()
        
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
            result = await self.generate_personalized_meal_plan(user_id, days, global_used_groups=global_used_ingredient_groups)
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
        
        # 🆕 전역 다양성 추적을 위한 재료 그룹 세트
        global_used_ingredient_groups = set()
        
        # 1. 날짜 파싱
        days = self._parse_days(message, state)
        if days is None:
            # plans.py의 기본값 상수 사용
            days = DEFAULT_MEAL_PLAN_DAYS
            print(f"📅 일수 파악 실패 → plans.py 기본값 {days}일 사용")
        
        # 🚨 일수 제한 가드 (최대 7일) - 사용자 친화적 메시지
        if days > MAX_MEAL_PLAN_DAYS:
            original_days = days
            days = MAX_MEAL_PLAN_DAYS
            print(f"⚠️ 요청 일수({original_days}일)가 최대 제한({MAX_MEAL_PLAN_DAYS}일)을 초과합니다.")
            print(f"✅ 일수를 {MAX_MEAL_PLAN_DAYS}일로 제한합니다.")
            
            # 사용자에게 친화적인 메시지 추가
            state["days_limited_message"] = f"💡 **안내**: 식단 생성은 최대 {MAX_MEAL_PLAN_DAYS}일까지만 가능합니다.\n\n요청하신 {original_days}일 대신 {MAX_MEAL_PLAN_DAYS}일 식단을 생성해드릴게요. 매주 새로운 식단을 받아보시면 더욱 다양하고 신선한 메뉴를 즐기실 수 있어요! 🍽️"
        
        print(f"📅 최종 일수: {days}일")
        
        # 🚀 식단 생성 캐싱 로직 (풀 캐시 기반 재조합)
        constraints = self._extract_all_constraints(message, state)
        cache_key = f"meal_plan_{days}_{constraints.get('kcal_target', '')}_{constraints.get('carbs_max', 30)}_{hash(tuple(sorted(constraints.get('allergies', []))))}_{hash(tuple(sorted(constraints.get('dislikes', []))))}_{state.get('profile', {}).get('user_id', '')}"
        
        # Redis 캐시 확인
        cached_result = redis_cache.get(cache_key)
        if cached_result:
            print(f"    📊 Redis 식단 생성 캐시 히트: {days}일 식단 (풀 재조합)")
            try:
                base_meal_plan = cached_result.get("meal_plan_data") or (
                    cached_result.get("results", [{}])[0].get("days")
                )
                reshuffled_plan = self._reshuffle_meal_plan_from_pool(base_meal_plan, days)
                formatted_response = self.response_formatter.format_meal_plan(reshuffled_plan, days)
                frontend_meal_result = {
                    "type": "meal_plan",
                    "days": reshuffled_plan.get("days", []),
                    "duration_days": days,
                    "total_macros": reshuffled_plan.get("total_macros"),
                    "notes": reshuffled_plan.get("notes", []),
                    "source": "meal_planner(pool_recombine)"
                }
                result_data = {
                    "results": [frontend_meal_result],
                    "response": formatted_response,
                    "formatted_response": formatted_response,
                    "meal_plan_days": days,
                    "meal_plan_data": reshuffled_plan,
                    "tool_calls": [{
                        "tool": "meal_planner",
                        "method": "handle_meal_request(pool_recombine)",
                        "days": days,
                        "fast_mode": state.get("fast_mode"),
                        "personalized": state.get("use_personalized", False)
                    }]
                }
                return result_data
            except Exception as e:
                print(f"  ⚠️ 풀 재조합 실패, 일반 생성으로 폴백: {e}")
        
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
                # 직접 개인화 생성 (constraints 반영)
                meal_plan = await self.generate_meal_plan(
                    days=days,
                    kcal_target=constraints.get("kcal_target"),
                    carbs_max=constraints.get("carbs_max", 30),
                    allergies=constraints.get("allergies", []),
                    dislikes=constraints.get("dislikes", []),
                    user_id=user_id,
                    fast_mode=fast_mode,
                    global_used_groups=global_used_ingredient_groups  # 🆕 전역 그룹 전달
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
                fast_mode=fast_mode,
                global_used_groups=global_used_ingredient_groups  # 🆕 전역 그룹 전달
            )
        
        # 6. 응답 포맷팅
        print(f"🔍 DEBUG: format_meal_plan 호출 - days: {days}, meal_plan.days 길이: {len(meal_plan.get('days', []))}")
        formatted_response = self.response_formatter.format_meal_plan(
            meal_plan, days
        )
        
        # 금지 문구가 있는 슬롯 확인
        banned_substrings = ['추천 식단이 없', '추천 불가']
        has_banned_content = False
        banned_slots = []
        
        for day_idx, day in enumerate(meal_plan.get("days", [])):
            for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                if slot in day and day[slot]:
                    slot_data = day[slot]
                    title = ""
                    if isinstance(slot_data, dict):
                        title = slot_data.get('title', '')
                    elif isinstance(slot_data, str):
                        title = slot_data
                    else:
                        title = str(slot_data)
                    
                    if title and any(bs in title for bs in banned_substrings):
                        has_banned_content = True
                        banned_slots.append(f"{day_idx + 1}일차 {slot}")
        
        # 금지 문구가 있으면 해당 슬롯을 None으로 설정하고 키토 팁과 안내 메시지 추가
        if has_banned_content:
            slot_names = {'breakfast': '아침', 'lunch': '점심', 'dinner': '저녁', 'snack': '간식'}
            banned_slots_korean = []
            
            # 금지 문구가 있는 슬롯을 None으로 설정
            for day_idx, day in enumerate(meal_plan.get("days", [])):
                for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                    if slot in day and day[slot]:
                        slot_data = day[slot]
                        title = ""
                        if isinstance(slot_data, dict):
                            title = slot_data.get('title', '')
                        elif isinstance(slot_data, str):
                            title = slot_data
                        else:
                            title = str(slot_data)
                        
                        if title and any(bs in title for bs in banned_substrings):
                            # 해당 슬롯을 None으로 설정
                            meal_plan["days"][day_idx][slot] = None
                            banned_slots_korean.append(f"{day_idx + 1}일차 {slot_names.get(slot, slot)}")
                            print(f"🚨 {day_idx + 1}일차 {slot} 슬롯을 None으로 설정: '{title}'")
            
            # 키토 팁 추가
            keto_tip = f"\n\n💡 **키토 팁**: 식단 생성이 어려울 때는 목표 칼로리를 100-200kcal 늘리거나, 탄수화물 한도를 5-10g 늘려보세요. 또한 알레르기나 비선호 음식을 일시적으로 완화하면 더 다양한 식단을 만들 수 있어요!"
            
            # 안내 메시지 추가
            guidance_message = f"\n\n⚠️ **안내**: 일부 날짜의 특정 식단을 생성하지 못했습니다 ({', '.join(banned_slots_korean)}). 해당 식단을 제외하고 저장하려면 **캘린더에 저장해줘**라고 말해보세요!"
            
            formatted_response += keto_tip + guidance_message
        
        # 7. 결과 반환 - 프론트엔드가 인식할 수 있는 형태로 results 구성
        # 프론트엔드 MealParserService가 찾는 형태: result.type === 'meal_plan' || result.days
        
        # 제한 메시지가 있으면 응답에 추가
        if state.get("days_limited_message"):
            formatted_response = state["days_limited_message"] + "\n\n" + formatted_response
        
        # 프론트엔드로 전송할 데이터 구성
        frontend_meal_result = {
            "type": "meal_plan",
            "days": meal_plan.get("days", []),  # 원본 데이터 그대로 사용
            "duration_days": days,
            "total_macros": meal_plan.get("total_macros"),
            "notes": meal_plan.get("notes", []),
            "source": meal_plan.get("source", "meal_planner")
        }

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
        
        # 🚀 풀 캐시 저장 (TTL: 5분) - 최종 결과가 아니라 풀로 저장하여 재조합에 사용
        try:
            redis_cache.set(cache_key, result_data, ttl=300)
            print(f"    💾 풀 캐시 저장: {days}일 식단 (TTL 300s)")
        except Exception as e:
            print(f"  ⚠️ 풀 캐시 저장 실패: {e}")
        
        print("🔍 DEBUG: 최종 반환 데이터 구조:")
        print(f"  - results length: {len(result_data.get('results', []))}")
        print(f"  - meal_plan_data 존재: {bool(result_data.get('meal_plan_data'))}")
        
        return result_data

    def _reshuffle_meal_plan_from_pool(self, base_plan: Dict[str, Any], days: int) -> Dict[str, Any]:
        """캐시된 식단 풀에서 빠르게 재조합하여 새 식단을 생성.
        - 슬롯별 후보를 모아 랜덤 샘플링
        - 추가 검색 없이 즉시 반환
        """
        import copy
        if not base_plan:
            return {"days": []}
        # base_plan이 dict(meal_plan_data) 또는 days 배열일 수 있음
        plan_days = base_plan.get("days") if isinstance(base_plan, dict) else base_plan
        plan_days = plan_days or []
        slot_names = ["breakfast", "lunch", "dinner", "snack"]
        slot_pool: Dict[str, List[Any]] = {s: [] for s in slot_names}
        for day in plan_days:
            for s in slot_names:
                item = day.get(s) if isinstance(day, dict) else None
                if item:
                    slot_pool[s].append(item)
        new_days: List[Dict[str, Any]] = []
        for _ in range(days):
            day_obj: Dict[str, Any] = {}
            for s in slot_names:
                candidates = slot_pool.get(s, [])
                if not candidates:
                    day_obj[s] = None
                    continue
                choice = random.choice(candidates)
                day_obj[s] = copy.deepcopy(choice)
            new_days.append(day_obj)
        return {
            "days": new_days,
            "notes": base_plan.get("notes") if isinstance(base_plan, dict) else [],
            "total_macros": base_plan.get("total_macros") if isinstance(base_plan, dict) else None,
        }
    
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
        
        # 🚀 레시피 요청 캐싱 로직 추가
        constraints = self._extract_all_constraints(message, state)
        user_id = state.get("profile", {}).get("user_id", "")
        cache_key = f"recipe_{hash(message)}_{constraints.get('kcal_target', '')}_{constraints.get('carbs_max', 30)}_{hash(tuple(sorted(constraints.get('allergies', []))))}_{hash(tuple(sorted(constraints.get('dislikes', []))))}_{user_id}"
        
        # Redis 캐시 확인
        cached_result = redis_cache.get(cache_key)
        if cached_result:
            print(f"    📊 Redis 레시피 요청 캐시 히트: {message[:30]}...")
            return cached_result
        
        # 1. 제약조건 추출
        constraints = self._extract_all_constraints(message, state)
        
        # 2. 사용자 ID 확인
        user_id = state.get("profile", {}).get("user_id")
        
        # 3. 프로필 기반 vs 일반 레시피
        if user_id and state.get("profile"):
            print(f"👤 프로필 기반 레시피 생성: user_id={user_id}")
            # 프로필 컨텍스트 생성 (임시 불호 포함)
            profile_context = self._build_profile_context(constraints)
            recipe = await self.generate_single_recipe(
                message=message,
                profile_context=profile_context,
                user_id=user_id
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
        
        # 5. 결과 반환 (response 제거하여 _answer_node에서 템플릿 처리)
        result_data = {
            "results": [{
                "title": f"AI 생성: {message}",
                "content": recipe,
                "source": "meal_planner_agent",
                "type": "recipe"
            }],
            # "response": formatted_response,  # 제거하여 _answer_node에서 템플릿 처리
            "formatted_response": formatted_response,
            "tool_calls": [{
                "tool": "meal_planner",
                "method": "handle_recipe_request",
                "query": message,
                "has_profile": bool(user_id and state.get("profile"))
            }]
        }
        
        # 🚀 레시피 요청 결과 캐싱 (TTL: 30분)
        redis_cache.set(cache_key, result_data, ttl=1800)
        print(f"    📊 레시피 요청 결과 캐시 저장: {message[:30]}...")
        
        return result_data
    
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
        print(f"🔍 DEBUG: _parse_days 시작 - 메시지: '{message}'")
        
        # LLM 파싱 시도 (대화 맥락 포함)
        try:
            chat_history = state.get("chat_history", [])
            print(f"🔍 DEBUG: chat_history 길이: {len(chat_history)}")
            parsed_date = self.date_parser.parse_natural_date_with_context(message, chat_history)
            print(f"🔍 DEBUG: parsed_date 결과: {parsed_date}")
            if parsed_date and parsed_date.duration_days:
                days = parsed_date.duration_days
                print(f"📅 DateParser LLM이 감지한 days: {days}")
                
                # 🚨 일수 제한 가드 (최대 7일)
                if days > MAX_MEAL_PLAN_DAYS:
                    print(f"⚠️ 파싱된 일수({days}일)가 최대 제한({MAX_MEAL_PLAN_DAYS}일)을 초과합니다.")
                    days = MAX_MEAL_PLAN_DAYS
                    print(f"✅ 일수를 {MAX_MEAL_PLAN_DAYS}일로 제한합니다.")
                
                return days
            else:
                print(f"⚠️ DateParser LLM 파싱 결과: duration_days 없음")
        except Exception as e:
            print(f"⚠️ DateParser LLM 파싱 오류: {e}")
        
        # 슬롯에서 가져오기 (백업)
        slots_days = state.get("slots", {}).get("days")
        print(f"🔍 DEBUG: slots에서 days: {slots_days}")
        if slots_days:
            days = int(slots_days)
            print(f"📅 슬롯에서 추출된 days: {days}")
            
            # 🚨 일수 제한 가드 (최대 7일)
            if days > MAX_MEAL_PLAN_DAYS:
                print(f"⚠️ 슬롯에서 추출된 일수({days}일)가 최대 제한({MAX_MEAL_PLAN_DAYS}일)을 초과합니다.")
                days = MAX_MEAL_PLAN_DAYS
                print(f"✅ 일수를 {MAX_MEAL_PLAN_DAYS}일로 제한합니다.")
            
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
        else:
            context_parts.append("알레르기: 없음")
        
        if constraints.get("dislikes"):
            context_parts.append(f"비선호 재료: {', '.join(constraints['dislikes'])}")
        else:
            context_parts.append("비선호 재료: 없음")
        
        return " | ".join(context_parts) if context_parts else ""
    
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
