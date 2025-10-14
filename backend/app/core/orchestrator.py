"""
LangGraph 기반 키토 코치 에이전트 오케스트레이터
의도 분류 → 도구 실행 → 응답 생성의 전체 플로우 관리
하이브리드 방식: IntentClassifier(키워드) + LLM 병합
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from langgraph.graph import StateGraph, START, END
from langchain.schema import HumanMessage, AIMessage, BaseMessage
import json
import re
from datetime import datetime

from app.core.intent_classifier import IntentClassifier, Intent  # 추가
from app.tools.shared.hybrid_search import hybrid_search_tool
from app.tools.shared.temporary_dislikes_extractor import temp_dislikes_extractor
from app.agents.meal_planner import MealPlannerAgent
from app.agents.chat_agent import SimpleKetoCoachAgent
from app.agents.place_search_agent import PlaceSearchAgent
from app.shared.utils.calendar_utils import CalendarUtils
from app.tools.calendar.calendar_saver import CalendarSaver
from app.core.llm_factory import create_chat_llm

# 프롬프트 모듈 import (중앙집중화된 구조)
from app.prompts.chat.intent_classification import INTENT_CLASSIFICATION_PROMPT, get_intent_prompt
from app.prompts.chat.response_generation import RESPONSE_GENERATION_PROMPT, PLACE_RESPONSE_GENERATION_PROMPT
from app.prompts.meal.guest_recipe_templates import get_guest_recipe_template, format_guest_recipe_template
from app.prompts.meal.recipe_response import RECIPE_RESPONSE_GENERATION_PROMPT
from app.prompts.restaurant.search_failure import PLACE_SEARCH_FAILURE_PROMPT
from app.prompts.shared.common_templates import create_standard_prompt
from app.prompts.chat.general_templates import get_general_response_template
from app.prompts.calendar import (
    CALENDAR_SAVE_CONFIRMATION_PROMPT,
    CALENDAR_SAVE_FAILURE_PROMPT,
    CALENDAR_MEAL_PLAN_VALIDATION_PROMPT
)

from typing_extensions import TypedDict, NotRequired, List

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AgentState(TypedDict):
    """에이전트 상태 관리 클래스"""
    messages: List[BaseMessage]
    intent: NotRequired[str]
    slots: NotRequired[Dict[str, Any]]
    results: NotRequired[List[Dict[str, Any]]]
    response: NotRequired[str]
    tool_calls: NotRequired[List[Dict[str, Any]]]
    profile: NotRequired[Optional[Dict[str, Any]]]
    location: NotRequired[Optional[Dict[str, float]]]
    radius_km: NotRequired[float]
    meal_plan_days: NotRequired[int]  # 추가
    meal_plan_data: NotRequired[Optional[Dict[str, Any]]]  # 구조화된 식단표 데이터
    save_to_calendar_data: NotRequired[Optional[Dict[str, Any]]]  # 캘린더 저장 데이터
    calendar_save_request: NotRequired[bool]  # 캘린더 저장 요청 여부 추가
    thread_id: NotRequired[Optional[str]]  # 현재 스레드 ID 추가
    use_personalized: NotRequired[bool]  # 개인화 모드 플래그
    use_meal_planner_recipe: NotRequired[bool]  # MealPlannerAgent 레시피 사용 플래그
    fast_mode: NotRequired[bool]  # 빠른 모드 플래그
    formatted_response: NotRequired[str]  # 포맷된 응답

class KetoCoachAgent:
    """키토 코치 메인 에이전트 (LangGraph 오케스트레이터)"""
    
    def __init__(self):
        try:
            # 공통 LLM 초기화
            self.llm = create_chat_llm()
        except Exception as e:
            print(f"LLM 초기화 실패: {e}")
            self.llm = None
        
        # IntentClassifier 초기화 (하이브리드 방식용)
        try:
            self.intent_classifier = IntentClassifier()
            print("✅ IntentClassifier 초기화 성공")
        except Exception as e:
            print(f"⚠️ IntentClassifier 초기화 실패: {e}")
            self.intent_classifier = None
        
        # 도구들 초기화
        self.hybrid_search = hybrid_search_tool  # 이미 초기화된 인스턴스 사용
        self.meal_planner = MealPlannerAgent()
        self.simple_agent = SimpleKetoCoachAgent()
        self.place_search_agent = PlaceSearchAgent()  # 새로운 식당 검색 에이전트
        self.calendar_saver = CalendarSaver()
        self.calendar_utils = CalendarUtils()
        
        # 워크플로우 그래프 구성
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 구성"""
        
        workflow = StateGraph(AgentState)
        
        # 노드 추가
        workflow.add_node("router", self._router_node)
        workflow.add_node("recipe_search", self._recipe_search_node)
        workflow.add_node("place_search", self._place_search_node)
        workflow.add_node("meal_plan", self._meal_plan_node)
        workflow.add_node("calendar_save", self._calendar_save_node)  # 새로 추가!
        workflow.add_node("general", self._general_chat_node)
        workflow.add_node("answer", self._answer_node)
        
        # 시작점 설정
        workflow.set_entry_point("router")
        
        # 라우터에서 각 노드로의 조건부 엣지
        workflow.add_conditional_edges(
            "router",
            self._route_condition,
            {
                "recipe_search": "recipe_search",  # 의도 분류기와 일치
                "place_search": "place_search", 
                "meal_plan": "meal_plan",
                "calendar_save": "calendar_save",
                "general": "general"
            }
        )
        
        # 모든 노드에서 answer로 (general은 직접 END로)
        workflow.add_edge("recipe_search", "answer")
        workflow.add_edge("place_search", "answer")
        workflow.add_edge("meal_plan", "answer")
        workflow.add_edge("calendar_save", "answer")  # 새로 추가!
        workflow.add_edge("general", END)
        workflow.add_edge("answer", END)
        
        return workflow.compile()
    
    def _determine_fast_mode(self, message: str) -> bool:
        """메시지 내용에 따라 fast_mode 동적 결정"""
        
        # 정확한 검색이 필요한 키워드
        accurate_keywords = ["정확한", "자세한", "맞춤", "개인", "추천", "최적", "신중하게", "꼼꼼하게"]
        
        # 빠른 응답이 필요한 키워드
        fast_keywords = ["빠르게", "간단히", "대충", "아무거나", "급해", "빨리", "간단하게"]
        
        message_lower = message.lower()
        
        # 명시적 키워드 확인
        if any(keyword in message_lower for keyword in accurate_keywords):
            print("🔍 정확한 검색 모드 활성화")
            return False
        
        if any(keyword in message_lower for keyword in fast_keywords):
            print("⚡ 빠른 검색 모드 활성화")
            return True
        
        # 시간대 기반 결정 (저녁/새벽은 빠르게)
        current_hour = datetime.now().hour
        if current_hour >= 22 or current_hour <= 6:
            print("🌙 야간 시간대 - 빠른 모드")
            return True
        
        # 기본값: 빠른 모드
        return True
    
    def _map_intent_to_route(self, intent_enum: Intent, message: str, slots: Dict[str, Any]) -> str:
        """IntentClassifier의 Intent enum을 orchestrator 라우팅 키로 변환
        
        IntentClassifier Intent -> Orchestrator Route 매핑:
        - RECIPE_SEARCH -> recipe_search
        - MEAL_PLAN -> meal_plan
        - PLACE_SEARCH -> place_search
        - CALENDAR_SAVE -> calendar_save
        - GENERAL -> general
        """
        
        if intent_enum == Intent.MEAL_PLANNING:
            # 식단표 관련 키워드로 세분화
            mealplan_keywords = [
                "식단표", "식단 만들", "식단 생성", "식단 짜",
                "일주일", "하루치", "이틀치", "3일치", "사흘치",
                "주간", "일주일치", "메뉴 계획", "한주", "한 주",
                "이번주", "다음주", "meal plan", "weekly"
            ]
            
            recipe_keywords = [
                "레시피", "조리법", "만드는 법", "어떻게 만들",
                "요리 방법", "조리 방법", "recipe", "how to make"
            ]
            
            # 메시지에서 키워드 확인
            message_lower = message.lower()
            
            # 명확한 식단표 요청
            if any(keyword in message_lower for keyword in mealplan_keywords):
                print(f"  🗓️ 식단표 키워드 감지 → mealplan")
                return "mealplan"
            
            # 명확한 레시피 요청
            if any(keyword in message_lower for keyword in recipe_keywords):
                print(f"  🍳 레시피 키워드 감지 → recipe")
                return "recipe"
            
            # 슬롯에 days가 있으면 식단표
            if slots.get("days") or slots.get("meal_time"):
                print(f"  📅 days 슬롯 감지 → mealplan")
                return "mealplan"
            
            # 기본값은 recipe
            print(f"  🍴 기본값 → recipe")
            return "recipe"
        
        elif intent_enum == Intent.PLACE_SEARCH:
            return "place"
        
        elif intent_enum == Intent.BOTH:
            # 식당 키워드가 더 강하면 place, 아니면 recipe
            place_keywords = ["식당", "맛집", "음식점", "카페", "레스토랑", "근처", "주변"]
            if any(keyword in message for keyword in place_keywords):
                print(f"  🏪 BOTH → 식당 우선")
                return "place"
            print(f"  🍳 BOTH → 레시피 우선")
            return "recipe"
        
        else:  # Intent.GENERAL
            return "general"
    
    async def _router_node(self, state: AgentState) -> AgentState:
        """의도 기반 라우팅 (신규 기능 + 하이브리드 IntentClassifier)"""
        
        message = state["messages"][-1].content if state["messages"] else ""
        chat_history = [msg.content for msg in state["messages"]] if state["messages"] else []
        
        # IntentClassifier로 의도 분류
        if self.intent_classifier:
            try:
                result = await self.intent_classifier.classify(
                    user_input=message, 
                    context=" ".join(chat_history[-5:]) if len(chat_history) > 1 else ""
                )
                
                intent_value = result["intent"].value
                confidence = result["confidence"]
                
                print(f"🎯 의도 분류: {intent_value} (신뢰도: {confidence:.2f}, 방식: {result.get('method', 'unknown')})")
                if result.get('reasoning'):
                    print(f"💭 LLM 추론: {result['reasoning']}")
                
                # 캘린더 저장 요청 처리 (사전 차단 로직 제거 - 부분 저장으로 대체)
                if intent_value == "calendar_save":
                    print("📅 캘린더 저장 요청 감지")
                    
                    # 대화 히스토리에서 최근 식단 데이터 찾기
                    meal_plan_data = self.calendar_utils.find_recent_meal_plan(chat_history)
                    if meal_plan_data:
                        state["meal_plan_data"] = meal_plan_data
                    
                    # 사전 차단 로직 완전 제거 - 부분 저장 로직으로 대체
                    print("✅ 사전 차단 로직 제거됨 - 부분 저장 로직 사용")
                    
                    # 캘린더 저장 플로우로 라우팅
                    state["intent"] = "calendar_save"
                    state["calendar_save_request"] = True
                    return state
                
                # 나머지 기존 로직...
                if intent_value == "recipe_search":
                    # recipe_search 의도는 레시피 검색으로 처리
                    state["intent"] = "recipe_search"
                    state["use_meal_planner_recipe"] = True
                    print("🍳 레시피 모드 (recipe_search 의도)")
                elif intent_value == "meal_plan":
                    # meal_plan 의도는 식단표 생성으로 처리
                    state["intent"] = "meal_plan"
                    state["fast_mode"] = self._determine_fast_mode(message)
                    print(f"🍽️ 식단표 모드 (meal_plan 의도, fast_mode={state['fast_mode']})")
                elif intent_value == "place_search":
                    state["intent"] = "place_search"
                    print(f"🏪 식당 검색 모드 활성화 (intent_value: {intent_value})")
                elif intent_value == "both":
                    # 식당 키워드가 더 강하면 place, 아니면 recipe
                    place_keywords = ["식당", "맛집", "음식점", "카페", "레스토랑", "근처", "주변"]
                    if any(keyword in message for keyword in place_keywords):
                        state["intent"] = "place_search"
                    else:
                        state["intent"] = "recipe_search"
                else:
                    state["intent"] = "general"
                
                # 추가 검증 규칙 적용: 추천만 있고 도메인 키워드 없으면 general 강제 등
                try:
                    validated = self._validate_intent(message, state["intent"])
                    if validated != state["intent"]:
                        print(f"    🔧 의도 재조정: {state['intent']} → {validated}")
                        state["intent"] = validated
                except Exception as _e:
                    print(f"    ⚠️ 의도 재검증 실패: {_e}")

                # 기존 로직에서 확신도 검증도 필요하다면 추가
                if intent_value != "calendar_save" and confidence >= 0.8:
                    print(f"  ✅ 높은 확신도 → 분류 채택")
                    
                    state["tool_calls"].append({
                        "tool": "router",
                        "method": "keyword_based",
                        "intent": state["intent"],
                        "confidence": confidence
                    })
                    
                    return state
                
            except Exception as e:
                print(f"IntentClassifier 오류, SimpleAgent로 폴백: {e}")
                # 폴백 로직 - 기본 intent로 처리
                state["intent"] = "general"
            
        return state
    
    def _validate_intent(self, message: str, initial_intent: str) -> str:
        """의도 분류 검증 및 수정 (간소화된 버전)
        
        IntentClassifier에서 이미 검증이 완료되었으므로,
        여기서는 orchestrator 특화 검증만 수행
        """
        # 0) 추천 키워드만 있고 도메인 키워드가 없으면 general로 강제
        try:
            text = (message or "").lower()
            recommend_keywords = ["추천", "추천해줘", "골라줘"]
            recipe_keywords = ["레시피", "조리법", "만드는", "요리", "재료", "메뉴"]
            place_keywords = ["식당", "맛집", "레스토랑", "카페", "근처", "주변", "위치"]
            plan_keywords = ["식단표", "주간", "7일", "일주일", "계획", "일정", "캘린더", "플랜"]
            has_recommend = any(k in text for k in recommend_keywords)
            has_domain = any(k in text for k in (recipe_keywords + place_keywords + plan_keywords))
            if has_recommend and not has_domain:
                print("    🔍 검증: 추천만 있고 도메인 키워드 없음 → general로 변경")
                return "general"
        except Exception:
            pass

        # IntentClassifier에서 처리하지 못한 orchestrator 특화 검증
        # 예: mealplan vs recipe 세분화 등
        
        # mealplan 의도인데 구체적인 계획 요청이 아닌 경우
        if initial_intent == "mealplan":
            plan_patterns = [
                r'식단표', r'메뉴.*계획', r'일주일.*계획', r'주간.*계획',
                r'만들어.*줘', r'계획.*세워', r'계획.*만들어', r'식단.*생성',
                r'생성.*해줘', r'식단.*만들어', r'키토.*식단', r'추천.*해줘',
                r'식단.*추천', r'.*식단.*'
            ]
            
            has_plan_request = any(re.search(pattern, message, re.IGNORECASE) for pattern in plan_patterns)
            if not has_plan_request:
                print(f"    🔍 검증: mealplan이지만 구체적 요청 없음 → general로 변경")
                return "general"
        
        # recipe 의도인데 구체적인 요리 요청이 아닌 경우
        if initial_intent == "recipe":
            recipe_patterns = [
                r'레시피', r'조리법', r'만드는.*법', r'어떻게.*만들어',
                r'요리.*방법', r'만들어.*줘', r'만들어.*달라'
            ]
            
            has_recipe_request = any(re.search(pattern, message, re.IGNORECASE) for pattern in recipe_patterns)
            if not has_recipe_request:
                print(f"    🔍 검증: recipe이지만 구체적 요청 없음 → general로 변경")
                return "general"
        
        # place 의도인데 구체적인 장소 검색 요청이 아닌 경우
        if initial_intent == "place":
            place_patterns = [
                r'식당.*찾아', r'식당.*추천', r'근처.*식당', r'어디.*있어',
                r'위치.*알려', r'장소.*알려', r'검색.*해줘'
            ]
            
            has_place_request = any(re.search(pattern, message, re.IGNORECASE) for pattern in place_patterns)
            if not has_place_request:
                print(f"    🔍 검증: place이지만 구체적 요청 없음 → general로 변경")
                return "general"
        
        return initial_intent
    
    # _find_recent_meal_plan 함수 제거 - CalendarUtils로 이동

    def _route_condition(self, state: AgentState) -> str:
        """라우팅 조건 함수"""
        intent = state["intent"]
        if state.get("calendar_save_request", False):
            return "calendar_save"
        
        # Intent Enum을 문자열로 변환
        if hasattr(intent, 'value'):
            return intent.value
        return str(intent)
    
    # 🎯 다양성 점수 계산 함수 제거됨 - 검색 단계에서 다양성 확보
    
    async def _recipe_search_node(self, state: AgentState) -> AgentState:
        """레시피 검색 노드 - MealPlannerAgent 우선 사용"""
        
        # 성능 측정 시작
        node_start_time = time.time()
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # 🚀 비로그인 사용자용 레시피 템플릿 우선 확인 (0.1초)
            profile = state.get("profile", {})
            is_logged_in = bool(profile.get("user_id"))
            
            if not is_logged_in:
                # 비로그인 사용자용 인기 재료 템플릿 확인
                popular_ingredients = ["닭가슴살", "계란", "연어", "아보카도", "소고기", "돼지고기", "새우", "참치"]
                is_popular_recipe = any(ingredient in message.lower() for ingredient in popular_ingredients)
                
                if is_popular_recipe:
                    # 인기 재료 추출
                    for ingredient in popular_ingredients:
                        if ingredient in message.lower():
                            template = get_guest_recipe_template(ingredient)
                            if template:
                                # 템플릿 기반 빠른 응답 (0.1초)
                                state["response"] = format_guest_recipe_template(template)
                                state["tool_calls"].append({
                                    "tool": "guest_recipe_template",
                                    "ingredient": ingredient,
                                    "method": "template_based"
                                })
                                
                                # 성능 측정 완료
                                node_end_time = time.time()
                                node_time = node_end_time - node_start_time
                                print(f"🍳 GUEST_RECIPE_TEMPLATE | Time: {node_time:.2f}s")
                                
                                return state
                            break
            
            # 기존 하이브리드 검색 로직 (로그인 사용자 또는 템플릿에 없는 경우)
            print(f"  🔍 하이브리드 검색 실행...")
            # 🚀 MealPlannerAgent 사용 비활성화 - 템플릿 기반 빠른 응답을 위해
            # if state.get("use_meal_planner_recipe", False):
            #     # handle_recipe_request 메서드가 있는지 확인
            #     if hasattr(self.meal_planner, 'handle_recipe_request'):
            #         print("🍳 MealPlannerAgent.handle_recipe_request() 사용")
            #         
            #         # MealPlannerAgent에 위임
            #         result = await self.meal_planner.handle_recipe_request(
            #             message=message,
            #             state=state
            #         )
            #         
            #         # 결과 상태에 병합
            #         state.update(result)
            #         return state
            #     else:
            #         print("⚠️ handle_recipe_request 메서드 없음, 기존 방식 사용")
            
            # 기존 하이브리드 검색 로직
            
            # 채팅에서 임시 불호 식재료 추출 (키워드 + LLM)
            temp_dislikes = await temp_dislikes_extractor.extract_from_message_async(message)
            
            # 프로필 정보 반영
            profile_context = ""
            allergies = []
            dislikes = []
            
            if state["profile"]:
                allergies = state["profile"].get("allergies", [])
                profile_dislikes = state["profile"].get("dislikes", [])
                
                # 임시 불호 식재료와 프로필 불호 식재료 합치기
                dislikes = temp_dislikes_extractor.combine_with_profile_dislikes(
                    temp_dislikes, profile_dislikes
                )
                
                print(f"  🔍 프로필 정보: 알레르기={allergies}, 비선호={dislikes}")
            else:
                # 프로필이 없는 경우 임시 불호 식재료만 사용
                dislikes = temp_dislikes
                print(f"  ⚠️ 프로필 없음: 임시 불호 식재료만 사용={dislikes}")
            
            if allergies:
                profile_context += f"알레르기: {', '.join(allergies)}. "
            if dislikes:
                profile_context += f"싫어하는 음식: {', '.join(dislikes)}. "
            
            # 하이브리드 검색 실행
            full_query = f"{message} {profile_context}".strip()
            user_id = state.get("profile", {}).get("user_id") if state.get("profile") else None
            search_results = await self.hybrid_search.search(
                query=full_query,
                max_results=5,
                user_id=user_id,
                allergies=allergies,
                dislikes=dislikes
            )
            
            # 검색 결과가 없거나 관련성이 낮을 때 AI 레시피 생성
            valid_results = [r for r in search_results if r.get('title') != '검색 결과 없음']

            # 🎯 다양성은 이미 검색 단계에서 확보됨 (계란 1개 + 비계란 2개)
            # 검색 결과가 있으면 바로 사용 (AI 생성 불필요)
            max_score = max([r.get('similarity', 0) for r in valid_results]) if valid_results else 0
            should_generate_ai = not search_results or len(valid_results) == 0 or max_score < 0.1

            # 개인화로 인해 모두 제외된 경우 사용자 친화적 안내 반환
            if not valid_results:
                reasons = []
                if allergies:
                    reasons.append(f"알레르기: {', '.join(allergies)}")
                if dislikes:
                    reasons.append(f"비선호: {', '.join(dislikes)}")

                reasons_text = ", ".join(reasons) if reasons else "검색 조건이 엄격함"
                state["response"] = (
                    "## 🔍 추천 레시피를 찾지 못했어요\n\n"
                    f"- 제외 사유: {reasons_text}\n"
                    "- 제안: 비선호 일부 완화, 재료 키워드 변경(예: 닭가슴살/돼지고기 중심), 탄수 한도를 소폭 상향(예: +5g) 후 다시 시도해보세요."
                )
                return state
            
            # 사용자 요청에 구체적인 음식명이 있는지 확인
            food_keywords = ["아이스크림", "케이크", "쿠키", "브라우니", "머핀", "푸딩", "치즈케이크", "티라미수"]
            has_specific_food = any(keyword in message.lower() for keyword in food_keywords)
            
            # 검색 결과에 해당 음식이 포함되어 있는지 확인
            if has_specific_food and valid_results:
                matching_results = []
                for keyword in food_keywords:
                    if keyword in message.lower():
                        matching_results = [r for r in valid_results if keyword in r.get('title', '').lower()]
                        break
                
                # 구체적인 음식을 요청했는데 일치하는 결과가 없으면 AI 생성
                should_generate_ai = len(matching_results) == 0
            else:
                # 일반적인 조건: 결과 없음 또는 점수가 낮음
                max_score = max([r.get('similarity', 0) for r in valid_results]) if valid_results else 0
                should_generate_ai = not search_results or len(valid_results) == 0 or max_score < 0.1
            
            if should_generate_ai:
                print(f"  🤖 검색 결과 없음 또는 다양성 부족, AI 레시피 생성 실행...")
                
                # AI 레시피 생성 시에도 합쳐진 불호 식재료 사용
                ai_profile_context = ""
                if allergies:
                    ai_profile_context += f"알레르기: {', '.join(allergies)}. "
                if dislikes:
                    ai_profile_context += f"싫어하는 음식: {', '.join(dislikes)}. "
                
                # AI 레시피 생성 (MealPlannerAgent 사용)
                ai_recipe = await self.meal_planner.generate_single_recipe(
                    message=message,
                    profile_context=ai_profile_context
                )
                
                # AI 생성 레시피를 결과로 설정 (사용자에게 알림 포함)
                ai_response = f"""## 🤖 AI 생성 레시피

**검색 결과가 다양하지 않아 AI가 맞춤형 레시피를 생성했습니다!**

{ai_recipe}

---
💡 **AI 생성 레시피란?**
- 검색된 레시피가 모두 비슷하거나 다양성이 부족할 때
- 개인 프로필(알레르기, 비선호 식품)을 고려하여 새로 생성
- 더 다양하고 맞춤형인 레시피를 제공합니다"""
                
                state["results"] = [{
                    "title": f"AI 생성: {message}",
                    "content": ai_response,
                    "source": "ai_generated",
                    "type": "recipe"
                }]
                
                state["tool_calls"].append({
                    "tool": "ai_recipe_generator",
                    "query": message,
                    "method": "gemini_generation",
                    "reason": "no_results"
                })
            else:
                # 검색 결과가 있을 때
                state["results"] = search_results
                state["tool_calls"].append({
                    "tool": "recipe_search",
                    "query": full_query,
                    "results_count": len(search_results)
                })
            
        except Exception as e:
            print(f"Recipe search error: {e}")
            state["results"] = []
            state["response"] = "## ⚠️ 오류 안내\n\n- 레시피 검색/생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        
        # 성능 측정 완료
        node_end_time = time.time()
        node_time = node_end_time - node_start_time
        print(f"🍳 RECIPE_NODE | Time: {node_time:.2f}s | Results: {len(state.get('results', []))}")
        
        return state
    
    async def _place_search_node(self, state: AgentState) -> AgentState:
        """장소 검색 노드 (PlaceSearchAgent 사용)"""
        
        # 성능 측정 시작
        node_start_time = time.time()
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # PlaceSearchAgent에 검색 위임
            search_result = await self.place_search_agent.search_places(
                message=message,
                location=state.get("location"),
                radius_km=state.get("radius_km", 5.0),
                profile=state.get("profile")
            )
            
            # 결과를 state에 저장
            state["results"] = search_result.get("results", [])
            
            # 🔧 PlaceSearchAgent가 생성한 응답을 formatted_response에 저장
            if search_result.get("response"):
                state["formatted_response"] = search_result["response"]
                print("✅ PlaceSearchAgent 응답을 formatted_response에 저장")
            
            # tool_calls 정보 추가
            if search_result.get("tool_calls"):
                state["tool_calls"].extend(search_result["tool_calls"])
            
            print(f"✅ PlaceSearchAgent 검색 완료: {len(state['results'])}개 결과")
            
        except Exception as e:
            print(f"❌ Place search error: {e}")
            state["results"] = []
            # MD 형식 오류 안내로 래핑
            state["response"] = "## ⚠️ 오류 안내\n\n- 식당 검색 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        
        # 성능 측정 완료
        node_end_time = time.time()
        node_time = node_end_time - node_start_time
        print(f"🏪 PLACE_NODE | Time: {node_time:.2f}s | Results: {len(state.get('results', []))}")
        
        return state
    
    async def _meal_plan_node(self, state: AgentState) -> AgentState:
        """식단표 생성 노드 - MealPlannerAgent가 모든 처리"""
        
        # 성능 측정 시작
        node_start_time = time.time()
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # MealPlannerAgent에 전체 처리 위임
            print("✅ MealPlannerAgent.handle_meal_request() 사용")
            result = await self.meal_planner.handle_meal_request(
                message=message,
                state=state
            )
            
            # 디버깅: 결과 확인
            print(f"🔍 MealPlannerAgent 결과 타입: {type(result)}")
            print(f"🔍 MealPlannerAgent 결과 키: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
            if isinstance(result, dict) and "response" in result:
                print(f"🔍 응답 내용 (처음 200자): {result['response'][:200]}...")
            
            # 결과 상태에 병합
            state.update(result)
            
            # 개인화 모드였다면 로깅
            if state.get("use_personalized"):
                user_id = state.get("profile", {}).get("user_id")
                print(f"✅ 개인화 식단 생성 완료: user_id={user_id}")
            
            return state
        
        except Exception as e:
            print(f"❌ Meal plan error: {e}")
            import traceback
            print(f"❌ 상세 오류: {traceback.format_exc()}")
            state["results"] = []
            state["response"] = "죄송합니다. 식단표 생성 중 오류가 발생했습니다. 다시 시도해주세요."
            return state
        
        # 성능 측정 완료
        node_end_time = time.time()
        node_time = node_end_time - node_start_time
        print(f"🍽️ MEAL_PLAN_NODE | Time: {node_time:.2f}s | Results: {len(state.get('results', []))}")
        
        return state
    
    
    
    async def _general_chat_node(self, state: AgentState) -> AgentState:
        """일반 채팅 노드 (대화 맥락 고려)"""
        
        # 성능 측정 시작
        node_start_time = time.time()
        
        try:
            # 전체 대화 히스토리 가져오기
            messages = state["messages"]
            current_message = messages[-1].content if messages else ""
            
            print(f"💬 일반 채팅 처리: '{current_message}'")
            print(f"📚 대화 히스토리 길이: {len(messages)}")
            
            # 디버깅: 모든 메시지 내용 출력
            for i, msg in enumerate(messages):
                role = "사용자" if isinstance(msg, HumanMessage) else "AI"
                print(f"   {i+1}. {role}: {msg.content[:50]}{'...' if len(msg.content) > 50 else ''}")
            
            # 대화 맥락을 고려한 응답 생성
            context_messages = []
            
            # 토큰 수에 맞게 최근 메시지들 선택 (너무 길면 토큰 낭비)
            recent_messages = self._truncate_messages_for_context(messages, max_tokens=2000)
            
            for msg in recent_messages:
                context_messages.append(msg)
            
            # 대화 맥락을 고려한 프롬프트 생성
            context_text = ""
            # 현재 메시지를 제외한 실제 이전 대화만 고려
            previous_messages = context_messages[:-1] if len(context_messages) > 1 else []
            
            # 새로운 대화인지 더 정확히 판단
            # 1. 이전 메시지가 없거나
            # 2. 이전 메시지가 모두 AI 메시지인 경우 (사용자가 아직 메시지를 보내지 않은 경우)
            is_new_conversation = True
            if previous_messages:
                # 이전 메시지 중에 사용자 메시지가 있는지 확인
                has_user_message = any(isinstance(msg, HumanMessage) for msg in previous_messages)
                is_new_conversation = not has_user_message
            
            if len(previous_messages) > 0 and not is_new_conversation:
                context_text = "이전 대화 내용:\n"
                for i, msg in enumerate(previous_messages, 1):
                    role = "사용자" if isinstance(msg, HumanMessage) else "AI"
                    context_text += f"{i}. {role}: {msg.content}\n"
                context_text += f"\n현재 사용자 메시지: {current_message}\n"
                print(f"📚 실제 이전 대화 개수: {len(previous_messages)}")
            else:
                context_text = f"사용자 메시지: {current_message}\n"
                print(f"🆕 새로운 대화 시작 (이전 사용자 대화 없음)")
            
            # 키토 코치로서 대화 맥락을 고려한 응답 생성 (공통 템플릿 사용)
            conversation_context = "새로운 대화입니다." if is_new_conversation else f"이전 대화 {len(previous_messages)}개가 있습니다."

            profile_context = ""
            profile_parts = []
            allergies = []
            dislikes = []
            goals_kcal = None
            goals_carbs_g = None
            if state.get("profile"):
                allergies = state["profile"].get("allergies") or []
                dislikes = state["profile"].get("dislikes") or []
                goals_kcal = state["profile"].get("goals_kcal")
                goals_carbs_g = state["profile"].get("goals_carbs_g")
                if allergies:
                    profile_parts.append(f"알레르기: {', '.join(allergies)}")
                if dislikes:
                    profile_parts.append(f"비선호: {', '.join(dislikes)}")
                if goals_kcal is not None:
                    profile_parts.append(f"목표 칼로리: {goals_kcal}kcal")
                if goals_carbs_g is not None:
                    profile_parts.append(f"탄수 제한: {goals_carbs_g}g")
                profile_context = "; ".join(profile_parts)

            # 사용자가 자신의 프로필을 묻는 경우, 구조화된 요약을 즉시 반환
            try:
                msg_lower = current_message.lower()
                asks_profile = any(keyword in msg_lower for keyword in [
                    "내 프로필", "프로필", "내가 비선호", "비선호", "싫어하는", "알레르기", "목표 칼로리", "탄수", "키토 목표"
                ])
                # 추천 키워드가 함께 있으면 요약 대신 추천 생성으로 진행
                has_recommend = any(k in msg_lower for k in ["추천", "추천해줘", "골라줘"]) 
            except Exception:
                asks_profile = False
                has_recommend = False

            if asks_profile and not has_recommend and (allergies or dislikes or goals_kcal is not None or goals_carbs_g is not None):
                lines = ["## 프로필 요약"]
                if allergies:
                    lines.append(f"- 알레르기: {', '.join(allergies)}")
                if dislikes:
                    lines.append(f"- 비선호: {', '.join(dislikes)}")
                if goals_kcal is not None:
                    lines.append(f"- 목표 칼로리: {goals_kcal}kcal")
                if goals_carbs_g is not None:
                    lines.append(f"- 탄수 제한: {goals_carbs_g}g")
                state["response"] = "\n".join(lines)
                return state

            # 키토 시작 질문 감지 (템플릿 사용) - 우선 적용
            keto_start_keywords = [
                "키토 다이어트 시작하려고 해",
                "키토 다이어트 시작하려고",
                "키토 다이어트 시작",
                "키토 시작하려고 해",
                "키토 시작하려고",
                "키토 시작",
                "다이어트 시작하려고 해",
                "다이어트 시작하려고",
                "다이어트 시작"
            ]
            is_keto_start = any(keyword in current_message.lower() for keyword in keto_start_keywords)
            
            if is_keto_start:
                # 템플릿 기반 빠른 응답 (0.1초) - 기존 프로필 정보 직접 활용
                state["response"] = get_general_response_template(current_message, state.get("profile", {}))
                state["tool_calls"].append({
                    "tool": "general",
                    "method": "template_based",
                    "template": "keto_start_guide"
                })
                return state

            # 일반 질문 템플릿 감지 (빠른 응답) - 인사/소개 질문만 템플릿 사용
            general_keywords = ["안녕", "안녕하세요", "너는", "당신은", "누구야"]
            
            # 키토 관련 구체적인 질문은 LLM이 답변하도록 제외
            keto_question_keywords = ["뭘", "무엇", "어떻게", "왜", "언제", "어디서", "얼마나", "몇", "어떤", "뭐야"]
            is_keto_specific_question = any(keyword in current_message.lower() for keyword in keto_question_keywords)
            
            # 디버깅 로그 추가
            print(f"🔍 의도 분류 디버깅:")
            print(f"  - 질문: '{current_message}'")
            print(f"  - 키토 질문 키워드 매칭: {is_keto_specific_question}")
            print(f"  - 매칭된 키워드: {[kw for kw in keto_question_keywords if kw in current_message.lower()]}")
            
            is_general_question = any(keyword in current_message.lower() for keyword in general_keywords) and not is_keto_specific_question
            print(f"  - 일반 질문으로 분류: {is_general_question}")
            
            if is_general_question:
                # 템플릿 기반 빠른 응답 (0.1초) - 사용자 상태별
                template_response = get_general_response_template(current_message, state.get("profile", {}))
                
                # 빈 문자열이면 LLM 답변으로 처리
                if not template_response or template_response.strip() == "":
                    print("템플릿 응답이 비어있음, LLM 답변으로 처리")
                    # LLM 답변 로직으로 계속 진행
                else:
                    state["response"] = template_response
                    state["tool_calls"].append({
                        "tool": "general",
                        "method": "template_based",
                        "template": "general_question"
                    })
                    return state

            # general_chat.py의 프롬프트 사용 (마크다운 규칙 포함)
            from app.prompts.chat.general_chat import GENERAL_CHAT_PROMPT
            prompt = GENERAL_CHAT_PROMPT.format(
                message=current_message,
                profile_context=profile_context
            )

            # 공통 LLM 직접 사용 (간단하고 빠름) - 안전한 호출
            try:
                response = await self.llm.ainvoke([HumanMessage(content=prompt)])
                state["response"] = response.content
            except Exception as llm_error:
                print(f"LLM 호출 오류: {llm_error}")
                print(f"LLM 오류 타입: {type(llm_error)}")
                # LLM 오류 시 기본 응답
                state["response"] = "키토 다이어트에 대한 질문이시군요! 구체적인 질문을 해주시면 더 정확한 답변을 드릴 수 있습니다."
            
            state["tool_calls"].append({
                "tool": "general",
                "method": "context_aware",
                "context_length": len(context_messages)
            })
            
        except Exception as e:
            print(f"General chat error: {e}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            state["response"] = "죄송합니다. 일반 채팅 처리 중 오류가 발생했습니다. 다시 시도해주세요."
        
        # 성능 측정 완료
        node_end_time = time.time()
        node_time = node_end_time - node_start_time
        print(f"💬 GENERAL_CHAT_NODE | Time: {node_time:.2f}s")
        
        return state
    
    async def _calendar_save_node(self, state: AgentState) -> AgentState:
        """캘린더 저장 처리 노드 (CalendarSaver 사용, 자동 덮어쓰기)"""
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""

            # 대화 히스토리 가져오기
            chat_history = []
            if state["messages"]:
                chat_history = [msg.content for msg in state["messages"]]

            # 1. 먼저 식단표 생성 (사용자 요청 일수 사용)
            slots = state.get("slots", {})
            days = slots.get("days", 7)  # 기본값 7일
            print(f"🍽️ {days}일치 식단표 생성 시작...")
            
            # 사용자 프로필 정보 가져오기
            user_id = state.get("user_id")
            if not user_id:
                # state에서 user_id를 찾을 수 없으면 기본값 사용
                user_id = "default_user"
                print("⚠️ user_id를 찾을 수 없어 기본값 사용")

            # 식단표 생성 (사용자 요청 일수 사용)
            meal_plan_result = await self.meal_planner.generate_meal_plan(
                days=days,
                user_id=user_id,
                fast_mode=True
            )

            if meal_plan_result.get("success"):
                print(f"✅ {days}일치 식단표 생성 성공")
                
                # 생성된 식단표를 state에 저장
                state["meal_plan_data"] = meal_plan_result.get("meal_plan", {})
                
                # 2. CalendarSaver를 사용하여 저장 처리
                result = await self.calendar_saver.save_meal_plan_to_calendar(
                    state, message, chat_history
                )
            else:
                print(f"❌ {days}일치 식단표 생성 실패")
                result = {
                    "success": False,
                    "message": f"죄송합니다. {days}일치 식단표 생성에 실패했습니다. 다시 시도해주세요."
                }

            # 결과에 따라 상태 업데이트
            state["response"] = result["message"]

            if result.get("save_data"):
                state["save_to_calendar_data"] = result["save_data"]
                # meal_plan_data가 있으면 보존
                if result["save_data"].get("meal_plan_data"):
                    state["meal_plan_data"] = result["save_data"]["meal_plan_data"]

            state["tool_calls"].append({
                "tool": "calendar_saver",
                "success": result["success"],
                "method": "save_meal_plan_to_calendar"
            })

            return state

        except Exception as e:
            print(f"❌ 캘린더 저장 노드 오류: {e}")
            import traceback
            print(f"❌ 상세 오류: {traceback.format_exc()}")
            state["response"] = "## ⚠️ 오류 안내\n\n- 캘린더 저장 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
            return state
    
    # _is_calendar_save_request 함수 제거 - CalendarUtils로 이동

    async def _handle_calendar_save_request(self, state: AgentState, message: str) -> AgentState:
        """캘린더 저장 요청 처리 (CalendarSaver 사용, 자동 덮어쓰기)"""
        
        print("🚀🚀🚀 _handle_calendar_save_request 함수 호출됨! 🚀🚀🚀")
        print(f"🔍 DEBUG: message = '{message}'")
        print(f"🔍 DEBUG: state keys = {list(state.keys()) if state else 'None'}")
        
        try:
            # 대화 히스토리 가져오기
            chat_history = []
            if state["messages"]:
                # 최근 10개 메시지만 확인 (토큰 절약)
                recent_messages = state["messages"][-10:] if len(state["messages"]) > 10 else state["messages"]
                for msg in recent_messages:
                    if hasattr(msg, 'content'):
                        chat_history.append(msg.content)

            # 캘린더 저장 처리 (금지 문구가 있는 슬롯은 프론트엔드에서 제외하고 저장)

            # CalendarSaver를 사용하여 저장 처리
            result = await self.calendar_saver.save_meal_plan_to_calendar(
                state, message, chat_history
            )

            # 결과에 따라 상태 업데이트
            state["response"] = result["message"]

            if result.get("save_data"):
                state["save_to_calendar_data"] = result["save_data"]
                # meal_plan_data가 있으면 보존
                if result["save_data"].get("meal_plan_data"):
                    state["meal_plan_data"] = result["save_data"]["meal_plan_data"]

            return state

        except Exception as e:
            print(f"❌ 캘린더 저장 요청 처리 오류: {e}")
            state["response"] = "죄송합니다. 캘린더 저장 처리 중 오류가 발생했습니다. 다시 시도해주세요."
            return state
    
    # 기존 _handle_calendar_save_request 함수 제거됨 - 위의 새 버전 사용
    
    async def _answer_node(self, state: AgentState) -> AgentState:
        """최종 응답 생성 노드"""
        
        print("🔍 DEBUG: _answer_node 호출됨!")
        
        # 성능 측정 시작
        node_start_time = time.time()
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # 캘린더 저장 요청 감지 및 처리 (메시지 내용으로 직접 확인) - 우선 처리
            # 더 강력한 키워드 매칭
            calendar_keywords = [
                "캘린더에 저장", "캘린더 저장", "저장해줘", "저장해", 
                "캘린더에", "캘린더에 추가", "캘린더 추가", 
                "캘린더에 저장해줘", "캘린더에 저장해", "저장해줘", "저장해",
                "캘린더", "저장", "넣어줘", "넣어", "추가해줘", "추가해"
            ]
            is_calendar_save = any(keyword in message for keyword in calendar_keywords)
            
            # 추가: 더 강력한 부분 매칭
            if not is_calendar_save:
                # "캘린더"와 "저장"이 모두 포함되어 있으면 저장 요청으로 간주
                if "캘린더" in message and "저장" in message:
                    is_calendar_save = True
                    print("🔍 부분 매칭으로 캘린더 저장 요청 감지")
            
            print(f"🔍 DEBUG: 메시지 내용: '{message}'")
            print(f"🔍 DEBUG: 캘린더 저장 키워드 매칭 결과: {is_calendar_save}")
            
            if is_calendar_save:
                print("📅 캘린더 저장 요청 감지 (메시지 내용 확인) - _handle_calendar_save_request 호출")
                print(f"🔍 DEBUG: is_calendar_save = {is_calendar_save}")
                print(f"🔍 DEBUG: message = '{message}'")
                return await self._handle_calendar_save_request(state, message)
            else:
                print("❌ 캘린더 저장 요청이 감지되지 않음")
                print(f"🔍 DEBUG: is_calendar_save = {is_calendar_save}")
                print(f"🔍 DEBUG: message = '{message}'")

            # 이미 응답이 설정되어 있으면 그대로 사용 (router 선차단/노드 처리 등)
            if state.get("response"):
                print("✅ 기존 응답 사용 (이미 설정됨)")
                # 캘린더/오류 단문도 MD 제목으로 보장
                if not state["response"].lstrip().startswith(("#", "##")):
                    state["response"] = f"## ℹ️ 안내\n\n{state['response']}"
                return state
            
            # MealPlannerAgent/PlaceSearchAgent가 포맷한 응답이 있으면 공통 템플릿으로 래핑
            if state.get("formatted_response"):
                print("✅ 포맷된 응답 사용")
                formatted = state["formatted_response"]
                # 식당 응답은 공통 템플릿으로 한 번 더 감싸서 MD 일관화
                if state.get("intent") == "place":
                    location = state.get('location') or {}
                    location_info = f"위도: {location.get('lat', '정보없음')}, 경도: {location.get('lng', '정보없음')}"
                    answer_prompt = PLACE_RESPONSE_GENERATION_PROMPT.format(
                        message=message,
                        location=location_info,
                        context=formatted
                    )
                    response = await self.llm.ainvoke([HumanMessage(content=answer_prompt)])
                    # 가독성 향상을 위한 경량 후처리: 개인 맞춤 조언 섹션을 명확히 구분
                    place_text = response.content or ""
                    # '개인 맞춤 조언' 구간을 굵은 제목과 구분선으로 감싸 가독성 개선
                    if "개인 맞춤 조언" in place_text:
                        try:
                            head, tail = place_text.split("개인 맞춤 조언", 1)
                            # tail 앞쪽 불필요한 콜론/공백 보정
                            tail = tail.lstrip(" :\n")
                            wrapped = f"{head}\n\n---\n**개인 맞춤 조언:**\n\n{tail}\n---\n"
                            place_text = wrapped
                        except ValueError:
                            pass
                    state["response"] = place_text
                else:
                    # 이미 헤더가 없으면 기본 헤더 추가
                    if not formatted.lstrip().startswith(("#", "##")):
                        formatted = f"## ✅ 결과\n\n{formatted}"
                    state["response"] = formatted
                return state
            
            # 결과 기반 응답 생성
            context = ""
            answer_prompt = ""
            
            # 식당 검색 실패시 전용 프롬프트 사용
            if state["intent"] == "place" and not state["results"]:
                answer_prompt = PLACE_SEARCH_FAILURE_PROMPT.format(message=message)
            elif state["results"]:
                # AI 생성 레시피는 그대로 출력
                if state["intent"] == "recipe" and state["results"] and state["results"][0].get("source") == "ai_generated":
                    ai_text = state["results"][0].get("content", "")
                    # 스켈레톤/폴백 패턴 혹은 금지 재료 포함 여부 검사
                    skeleton_patterns = [
                        "키토 버전", "주재료:", "키토 친화적 재료", "키토 대체재:",
                        "일시적인 시스템", "기본 가이드", "잠시 후 다시 시도"
                    ]
                    has_skeleton = any(pat in ai_text for pat in skeleton_patterns)

                    # 프로필 기반 금지 재료 검출
                    banned_hits = []
                    if state.get("profile"):
                        for lst_key in ("allergies", "dislikes"):
                            for item in state["profile"].get(lst_key, []) or []:
                                if item and str(item) in ai_text:
                                    banned_hits.append(item)

                    if has_skeleton or banned_hits:
                        reasons = []
                        if banned_hits:
                            reasons.append(f"금지 재료 포함: {', '.join(sorted(set(banned_hits)))}")
                        else:
                            reasons.append("생성 결과가 부정확/불완전")

                        state["response"] = (
                            "## 🔍 추천 레시피를 찾지 못했어요\n\n"
                            f"- 제외 사유: {', '.join(reasons)}\n"
                            "- 제안: 비선호 일부 완화, 재료 키워드 변경(예: 닭가슴살/돼지고기 중심), 탄수 한도를 소폭 상향(예: +5g) 후 다시 시도해보세요."
                        )
                    else:
                        state["response"] = ai_text or "레시피 생성에 실패했습니다."
                    return state
                
                # 검색 결과 기반 레시피 포맷팅 - 조건부 템플릿 적용
                elif state["intent"] == "recipe" or state["intent"] == "recipe_search":
                    # 🎯 특정 레시피 요청인지 확인 (더 정확한 조건)
                    specific_recipe_keywords = ['만드는법', '조리법', '어떻게', '방법', '레시피를', '레시피가']
                    meal_time_keywords = ['아침', '점심', '저녁', '브렉퍼스트', '모닝', 'breakfast', 'lunch', 'dinner']
                    
                    has_specific_request = any(keyword in message.lower() for keyword in specific_recipe_keywords)
                    has_meal_time = any(keyword in message.lower() for keyword in meal_time_keywords)
                    
                    print(f"  🔍 조건 확인:")
                    print(f"    - has_specific_request: {has_specific_request}")
                    print(f"    - has_meal_time: {has_meal_time}")
                    print(f"    - message: {message}")
                    print(f"    - 조건: has_specific_request and not has_meal_time = {has_specific_request and not has_meal_time}")
                    
                    # 특정 레시피 요청이면서 식사 시간 키워드가 없으면 LLM 사용
                    if has_specific_request and not has_meal_time:
                        print(f"  🤖 특정 레시피 요청 감지 - LLM 응답 생성")
                        print(f"    🔍 has_specific_request: {has_specific_request}")
                        print(f"    🔍 has_meal_time: {has_meal_time}")
                        print(f"    🔍 message: {message}")
                        # 기존 LLM 방식 사용
                        context = "추천 레시피:\n"
                        for idx, result in enumerate(state["results"][:3], 1):
                            context += f"{idx}. {result.get('title', result.get('name', '이름 없음'))}\n"
                            if result.get('content'):
                                context += f"   내용: {result['content'][:200]}...\n"
                            if result.get('ingredients'):
                                context += f"   재료: {result['ingredients']}\n"
                            if result.get('carbs'):
                                context += f"   탄수화물: {result['carbs']}g\n"
                        
                        # 프로필 컨텍스트 구성
                        profile_parts = []
                        if state.get("profile"):
                            p = state["profile"]
                            if p.get("allergies"):
                                profile_parts.append(f"알레르기: {', '.join(p['allergies'])}")
                            if p.get("dislikes"):
                                profile_parts.append(f"비선호: {', '.join(p['dislikes'])}")
                            if p.get("goals_kcal"):
                                profile_parts.append(f"목표 칼로리: {p['goals_kcal']}kcal")
                            if p.get("goals_carbs_g") is not None:
                                profile_parts.append(f"탄수 제한: {p['goals_carbs_g']}g")
                        profile_context = "; ".join(profile_parts)

                        answer_prompt = RECIPE_RESPONSE_GENERATION_PROMPT.format(
                            message=message,
                            context=context,
                            profile_context=profile_context
                        )
                    else:
                        # 🚀 템플릿 기반 빠른 응답 생성 (식사 시간 키워드 있거나 일반 추천)
                        print(f"  ⚡ 템플릿 기반 빠른 응답 생성")
                        print(f"    🔍 템플릿 경로로 진입")
                        print(f"    🔍 has_specific_request: {has_specific_request}")
                        print(f"    🔍 has_meal_time: {has_meal_time}")
                        print(f"    🔍 message: {message}")
                        response_text = "## 🍽️ 추천 키토 레시피 TOP 3\n\n"
                        
                        # 프로필 정보 수집 (개인화 설명용)
                        profile_info = []
                        if state.get("profile"):
                            p = state["profile"]
                            if p.get("allergies"):
                                profile_info.append(f"알레르기({', '.join(p['allergies'])})")
                            if p.get("dislikes"):
                                profile_info.append(f"비선호({', '.join(p['dislikes'])})")
                        
                        # 각 레시피를 상세한 형식으로 포맷팅 (실제 DB 데이터 활용)
                        print(f"    🔍 state['results'] 타입: {type(state['results'])}")
                        print(f"    🔍 state['results'] 길이: {len(state['results'])}")
                        if state["results"]:
                            print(f"    🔍 첫 번째 결과 키들: {list(state['results'][0].keys())}")
                            print(f"    🔍 첫 번째 결과 전체: {state['results'][0]}")
                        
                        for idx, result in enumerate(state["results"][:3], 1):
                            title = result.get('title', result.get('name', '이름 없음'))
                            content = result.get('content', '')
                            blob = result.get('blob', '')  # 실제 레시피 데이터
                            ingredients = result.get('ingredients', [])  # 재료 배열
                            url = result.get('url', '')
                            
                            # blob이 비어있으면 content 사용
                            if not blob and content:
                                blob = content
                                print(f"    ✅ blob이 비어있어서 content 사용: {title}")
                            
                            # blob 데이터 디버깅
                            print(f"    🔍 레시피 {idx}: {title}")
                            print(f"    🔍 blob 존재 여부: {bool(blob)}")
                            print(f"    🔍 blob 타입: {type(blob)}")
                            print(f"    🔍 blob 길이: {len(str(blob))}")
                            if blob:
                                print(f"    🔍 blob 내용: {str(blob)[:200]}...")
                            else:
                                print(f"    ❌ blob이 비어있음")
                            
                            # URL 디버깅 및 처리
                            print(f"    🔗 URL 확인: {title[:20]}... -> {url[:50] if url else 'None'}")
                            
                            # 제목 표시 (URL이 있으면 제목도 클릭 가능)
                            if url and url.strip():
                                response_text += f"**{idx}. [{title}]({url})** [🔗]({url})"
                            else:
                                response_text += f"**{idx}. {title}**"
                            
                            response_text += "\n"
                            
                            # 실제 DB 데이터 활용
                            # 1. 재료 정보 (blob의 재료 섹션 우선 사용)
                            main_ingredients = []
                            
                            # blob에서 재료 정보 추출
                            if blob:
                                import re
                                print(f"    🔍 blob 전체 내용 (재료 추출 전):")
                                print(f"    {blob}")
                                print(f"    🔍 blob 길이: {len(blob)}")
                                
                                # 재료 섹션 찾기 (실제 blob 구조에 맞게)
                                ingredient_match = re.search(r'재료[:\s]*([^\n]+)', blob)
                                if ingredient_match:
                                    ingredient_text = ingredient_match.group(1).strip()
                                    print(f"    🔍 원본 재료 텍스트: {ingredient_text}")
                                    
                                    # 설명문이 아닌 실제 재료인지 확인
                                    if not any(word in ingredient_text for word in ['구성되어', '적합하다', '들로', '있습니다', '만들', '요리', '로 한', '로한', '입니다', '합니다', '되다', '이다']) and not ingredient_text.endswith('니다') and not ingredient_text.endswith('합니다'):
                                        # 재료를 쉼표로 분리 (공백으로는 분리하지 않음)
                                        ingredients_list = re.split(r'[,，]', ingredient_text)
                                        for ingredient in ingredients_list[:5]:  # 최대 5개
                                            if ingredient.strip():
                                                # 재료명 정리 (양, 단위, 특수문자 제거)
                                                clean_ingredient = ingredient.strip()
                                                # 영어 중복 제거 (예: "계란egg" -> "계란", "마요네즈mayonnaise" -> "마요네즈")
                                                clean_ingredient = re.sub(r'([가-힣]+)[a-zA-Z]+', r'\1', clean_ingredient)
                                                # 괄호와 내용 제거 (예: "(egg)" -> "", "(soy sauce)" -> "")
                                                clean_ingredient = re.sub(r'\([^)]*\)', '', clean_ingredient)
                                                # 숫자, 단위, ~ 제거 (예: "토마토 4~" -> "토마토", "매실청 2~" -> "매실청")
                                                clean_ingredient = re.sub(r'\s*\d+[~숟가락mlg개공기]*\s*', '', clean_ingredient)
                                                # 특수문자 제거 (~, *, -, 등)
                                                clean_ingredient = re.sub(r'[~*\-+()\[\]{}]', '', clean_ingredient)
                                                # 공백 정리
                                                clean_ingredient = clean_ingredient.strip()
                                                if clean_ingredient and len(clean_ingredient) > 1:
                                                    main_ingredients.append(clean_ingredient)
                                    else:
                                        print(f"    ⚠️ 재료 섹션이 설명문입니다: {ingredient_text}")
                                
                                print(f"    🥘 blob 재료 추출: {main_ingredients}")
                            
                            # blob에서 재료를 찾지 못한 경우 ingredients 배열 사용
                            if not main_ingredients and ingredients and isinstance(ingredients, list):
                                for ingredient in ingredients[:5]:
                                    if isinstance(ingredient, str) and ingredient.strip():
                                        clean_ingredient = ingredient.strip()
                                        import re
                                        # 영어 중복 제거 (예: "마요네즈mayonnaise" -> "마요네즈")
                                        clean_ingredient = re.sub(r'([가-힣]+)[a-zA-Z]+', r'\1', clean_ingredient)
                                        # 괄호와 내용 제거 (예: "(soy sauce)" -> "")
                                        clean_ingredient = re.sub(r'\([^)]*\)', '', clean_ingredient)
                                        # 숫자, 단위, ~ 제거 (예: "토마토 4~" -> "토마토")
                                        clean_ingredient = re.sub(r'\s*\d+[~숟가락mlg개공기]*\s*', '', clean_ingredient)
                                        # 특수문자 제거
                                        clean_ingredient = re.sub(r'[~*\-+()\[\]{}]', '', clean_ingredient)
                                        clean_ingredient = clean_ingredient.strip()
                                        if clean_ingredient and len(clean_ingredient) > 1:
                                            main_ingredients.append(clean_ingredient)
                                
                                print(f"    🥘 ingredients 배열 사용: {main_ingredients}")
                            
                            if main_ingredients:
                                response_text += f"- **준비물**: {', '.join(main_ingredients)}\n"
                            
                            # 2. 조리 방법 및 팁 (blob 데이터 직접 활용)
                            cooking_method = ""
                            cooking_tip = ""
                            
                            # blob에서 핵심 요약 추출 (조리 팁으로 사용)
                            if blob:
                                import re
                                print(f"    🔍 blob 전체 내용:")
                                print(f"    {blob}")
                                print(f"    🔍 blob 길이: {len(blob)}")
                                
                                # 1. '핵심 요약:'을 찾아서 '재료:' 앞까지 가져오기
                                summary_section = ""
                                
                                # 핵심 요약 섹션 찾기
                                summary_start = blob.find('핵심 요약:')
                                if summary_start != -1:
                                    print(f"    ✅ '핵심 요약:' 발견 at position {summary_start}")
                                    
                                    # 재료 섹션 시작점 찾기
                                    ingredients_start = blob.find('재료:', summary_start)
                                    if ingredients_start != -1:
                                        print(f"    ✅ '재료:' 발견 at position {ingredients_start}")
                                        # 핵심 요약부터 재료 앞까지 추출
                                        summary_section = blob[summary_start:ingredients_start].strip()
                                    else:
                                        # 재료가 없으면 다음 섹션까지 찾기
                                        next_section_patterns = ['태그:', '알레르기:', '보조 키워드:', '식사:']
                                        next_positions = []
                                        for pattern in next_section_patterns:
                                            pos = blob.find(pattern, summary_start)
                                            if pos != -1:
                                                next_positions.append(pos)
                                        
                                        if next_positions:
                                            next_start = min(next_positions)
                                            summary_section = blob[summary_start:next_start].strip()
                                        else:
                                            # 다음 섹션이 없으면 끝까지
                                            summary_section = blob[summary_start:].strip()
                                    
                                    print(f"    📝 핵심 요약 섹션: {summary_section}")
                                    
                                    # 2. '핵심 요약:' 제거하고 실제 내용만 추출
                                    if summary_section.startswith('핵심 요약:'):
                                        content = summary_section[5:].strip()  # '핵심 요약:' (5글자) 제거
                                        print(f"    📝 핵심 요약 내용: {content}")
                                        
                                        # 3. '.'으로 문장 분리 (더 정확한 패턴)
                                        sentences = re.split(r'[.]\s+', content)
                                        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
                                        
                                        print(f"    📝 분리된 문장 수: {len(sentences)}")
                                        for i, sentence in enumerate(sentences, 1):
                                            print(f"    📝 문장 {i}: {sentence}")
                                        
                                        # 4. 번호가 매겨진 리스트로 변환 (Markdown 들여쓰기 적용)
                                        if sentences:
                                            cooking_tips = []
                                            for i, sentence in enumerate(sentences, 1):
                                                # 콜론 제거 (문장 앞과 뒤의 : 제거)
                                                clean_sentence = sentence.strip().lstrip(':').rstrip(':').strip()
                                                # 마지막 항목의 마침표 제거
                                                if i == len(sentences):
                                                    clean_sentence = clean_sentence.rstrip('.')
                                                print(f"    🔍 원본 문장: '{sentence}'")
                                                print(f"    🔍 정리된 문장: '{clean_sentence}'")
                                                cooking_tips.append(f"  {i}. {clean_sentence}")
                                            cooking_tip = '\n'.join(cooking_tips)
                                            print(f"    ✅ 조리 팁 생성 완료: {len(sentences)}개 문장")
                                            print(f"    🔍 최종 조리 팁: {cooking_tip}")
                                        else:
                                            # 문장 분리가 안 되면 전체 내용을 하나의 팁으로
                                            clean_content = content.strip().lstrip(':').rstrip(':').strip().rstrip('.')
                                            cooking_tip = f"  1. {clean_content}"
                                            print(f"    ⚠️ 문장 분리 실패, 전체 내용을 하나의 팁으로 사용")
                                    else:
                                        print(f"    ❌ 핵심 요약 섹션 형식 오류")
                                else:
                                    print(f"    ❌ '핵심 요약:'을 찾을 수 없음")
                            else:
                                print(f"    ❌ blob 데이터가 없음")
                                
                                # 핵심 요약을 찾지 못한 경우 blob의 첫 번째 문장 사용
                                if not cooking_tip:
                                    # 첫 번째 문장 추출 (마침표까지)
                                    first_sentence = re.search(r'^([^.]*\.)', blob, re.MULTILINE)
                                    if first_sentence:
                                        cooking_tip = first_sentence.group(1).strip()
                                        print(f"    📝 첫 문장 추출: {cooking_tip[:50]}...")
                                
                                # blob에서 조리 방법 추출 (더 상세한 섹션 찾기)
                                # 다양한 조리 방법 패턴 시도
                                method_patterns = [
                                    r'조리[:\s]*([^핵심|태그|알레르기|보조|식사].*?)(?=핵심|태그|알레르기|보조|식사|$)',
                                    r'만들기[:\s]*([^핵심|태그|알레르기|보조|식사].*?)(?=핵심|태그|알레르기|보조|식사|$)',
                                    r'방법[:\s]*([^핵심|태그|알레르기|보조|식사].*?)(?=핵심|태그|알레르기|보조|식사|$)',
                                    r'레시피[:\s]*([^핵심|태그|알레르기|보조|식사].*?)(?=핵심|태그|알레르기|보조|식사|$)'
                                ]
                                
                                for pattern in method_patterns:
                                    method_match = re.search(pattern, blob, re.DOTALL | re.IGNORECASE)
                                    if method_match:
                                        cooking_method = method_match.group(1).strip()[:200] + "..."
                                        break
                                
                                if cooking_method:
                                    print(f"    🍳 조리 방법 추출: {cooking_method[:50]}...")
                                else:
                                    print(f"    ⚠️ 조리 방법 추출 실패")
                            
                            # 조리 방법 표시
                            if cooking_method:
                                response_text += f"- **조리 방법**: {cooking_method}\n"
                            
                            # 조리 팁이 없으면 에러 메시지
                            if not cooking_tip:
                                cooking_tip = "❌ 핵심 요약을 찾을 수 없습니다"
                                print(f"    ❌ 조리 팁 없음 - blob 데이터 확인 필요")
                            
                            # 간단 설명 표시 (여러 줄 지원)
                            if cooking_tip:
                                if '\n' in cooking_tip:
                                    # 여러 줄인 경우 (번호가 매겨진 리스트)
                                    response_text += f"- **간단 설명**:\n{cooking_tip}\n"
                                else:
                                    # 한 줄인 경우
                                    response_text += f"- **간단 설명**: {cooking_tip}\n"
                            
                            # 4. 탄수화물 정보 (있는 경우)
                            if result.get('carbs'):
                                response_text += f"- **탄수화물**: {result['carbs']}g\n"
                            
                            response_text += "\n"
                        
                        # 개인화 설명 추가
                        if profile_info:
                            response_text += f"💡 **개인화된 레시피**: {', '.join(profile_info)}를 제외한 맞춤형 추천입니다.\n"
                        else:
                            response_text += "💡 **개인화된 레시피**: 프로필 기반 맞춤형 추천입니다.\n"
                        
                        # 링크 안내 메시지 추가
                        response_text += "\n💡 **레시피** 혹은 🔗을 클릭하면 더욱 상세한 정보를 얻을 수 있습니다.\n"
                        
                        state["response"] = response_text
                        state["tool_calls"].append({
                            "tool": "recipe_template",
                            "method": "fast_template",
                            "results_count": len(state["results"])
                        })
                        return state
                elif state["intent"] == "place":
                    context = "추천 식당:\n"
                    for idx, result in enumerate(state["results"][:5], 1):
                        context += f"{idx}. {result.get('name', '이름 없음')} (키토점수: {result.get('keto_score', 0)})\n"
                        context += f"   주소: {result.get('address', '')}\n"
                        context += f"   카테고리: {result.get('category', '')}\n"
                        
                        # RAG 결과인 경우 메뉴 정보 추가
                        if result.get('source') == 'rag' and result.get('menu_info', {}).get('name'):
                            menu_info = result.get('menu_info', {})
                            context += f"   추천메뉴: {menu_info.get('name', '')}"
                            if menu_info.get('price'):
                                context += f" ({menu_info.get('price')}원)"
                            context += "\n"
                            if menu_info.get('description'):
                                context += f"   메뉴설명: {menu_info.get('description')}\n"
                        
                        # 키토 팁 추가
                        if result.get('tips'):
                            context += f"   키토팁: {', '.join(result['tips'][:2])}\n"
                        elif isinstance(result.get('why'), dict) and result['why']:
                            # RAG에서 온 keto_reasons 처리
                            context += f"   키토추천이유: RAG 데이터 기반\n"
                    
                    # 식당 전용 응답 생성 프롬프트 사용
                    location = state.get('location') or {}
                    location_info = f"위도: {location.get('lat', '정보없음')}, 경도: {location.get('lng', '정보없음')}"
                    answer_prompt = PLACE_RESPONSE_GENERATION_PROMPT.format(
                        message=message,
                        location=location_info,
                        context=context
                    )
                elif state["intent"] == "mealplan":
                    # 식단표 간단 포맷팅 (메뉴 이름 위주) + 바로 응답 반환
                    if state["results"] and len(state["results"]) > 0:
                        meal_plan = state["results"][0]
                        # tool_calls에서 days 정보 추출 (state가 유지되지 않는 문제 해결)
                        requested_days = 7  # 기본값
                        for tool_call in state.get("tool_calls", []):
                            if tool_call.get("tool") == "meal_planner":
                                requested_days = tool_call.get("days", 7)
                                break
                        print(f"🔍 DEBUG: tool_calls에서 추출한 days: {requested_days}")
                        print(f"🔍 DEBUG: state['meal_plan_days'] 조회: {state.get('meal_plan_days', 'NOT_FOUND')}")
                        day_text = "일" if requested_days == 1 else f"{requested_days}일"
                        response_text = f"## ✨ {day_text} 키토 식단표\n\n"
                        
                        # 각 날짜별 식단 간단 포맷팅
                        # 사용자가 요청한 일수만큼만 출력
                        meal_days = meal_plan.get("days", [])[:requested_days]
                        print(f"🔍 DEBUG: 요청 일수 {requested_days}, 생성된 일수 {len(meal_plan.get('days', []))}, 출력 일수 {len(meal_days)}")
                        
                        # 프로필 기반 금지 재료(알레르기+비선호) 수집
                        banned_terms = set()
                        if state.get("profile"):
                            allergies = [s for s in (state["profile"].get("allergies") or []) if s]
                            dislikes = [s for s in (state["profile"].get("dislikes") or []) if s]
                            banned_terms.update(allergies)
                            banned_terms.update(dislikes)
                            
                            # 동의어 확장 (ingredient_synonyms.json 사용)
                            try:
                                from pathlib import Path
                                synonym_file = Path(__file__).parent.parent / 'data' / 'ingredient_synonyms.json'
                                with open(synonym_file, 'r', encoding='utf-8') as f:
                                    synonym_data = json.load(f)
                                
                                # 알레르기 동의어 확장
                                for allergy in allergies:
                                    allergy_synonyms = synonym_data.get('알레르기', {}).get(allergy, [])
                                    banned_terms.update(allergy_synonyms)
                                
                                # 비선호 동의어 확장
                                for dislike in dislikes:
                                    dislike_synonyms = synonym_data.get('비선호', {}).get(dislike, [])
                                    banned_terms.update(dislike_synonyms)
                            except Exception as e:
                                print(f"⚠️ 동의어 사전 로드 실패 (orchestrator): {e}")

                        def contains_banned(text: str) -> bool:
                            """정확 매칭으로 금지 재료 검사 (부분문자열 금지)"""
                            if not text or not banned_terms:
                                return False
                            
                            t = (text or "").lower()
                            # 토큰화
                            tokens = re.split(r'[,\s\(\)\[\]\{\}/]+', t)
                            tokens = [tok.strip() for tok in tokens if tok.strip()]
                            
                            for term in banned_terms:
                                term_lower = str(term).lower()
                                # 정확 매칭
                                if term_lower in tokens:
                                    return True
                                # 복합어 처리 (예: "bell pepper")
                                if ' ' in term_lower and term_lower in t:
                                    return True
                            return False

                        for day_idx, day_meals in enumerate(meal_days, 1):
                            response_text += f"**{day_idx}일차:**\n"
                            
                            shown_any = False
                            for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                                if slot in day_meals and day_meals[slot]:
                                    meal = day_meals[slot]
                                    slot_name = {"breakfast": "🌅 아침", "lunch": "🌞 점심", "dinner": "🌙 저녁", "snack": "🍎 간식"}[slot]
                                    title = meal.get('title', '메뉴 없음')
                                    if not contains_banned(title):
                                        response_text += f"- {slot_name}: {title}\n"
                                        shown_any = True
                            if not shown_any:
                                response_text += "- 제약 조건으로 추천 가능한 메뉴가 없습니다.\n"
                            
                            response_text += "\n"
                        
                        # 핵심 조언만 간단히
                        notes = meal_plan.get("notes", [])
                        if notes:
                            # 기술 용어(임베딩/embedding/벡터 등) 제거
                            cleaned = []
                            for n in notes:
                                ln = str(n)
                                if any(k in ln.lower() for k in ["임베딩", "embedding", "벡터", "vector"]):
                                    continue
                                cleaned.append(ln)
                            if cleaned:
                                response_text += "### 💡 키토 팁\n"
                                for note in cleaned[:3]:  # 최대 3개만
                                    response_text += f"- {note}\n"
                        
                        # 구조화된 식단표 데이터를 응답에 포함
                        meal_plan_data = {
                            "duration_days": requested_days,
                            "days": meal_days,
                            "total_macros": meal_plan.get("total_macros", {}),
                            "notes": meal_plan.get("notes", [])
                        }
                        
                        # 응답에 구조화된 데이터 포함 (프론트엔드에서 파싱 가능)
                        state["response"] = response_text
                        state["meal_plan_data"] = meal_plan_data  # 구조화된 데이터 추가
                        return state
                    else:
                        # tool_calls에서 days 정보 추출
                        requested_days = 7  # 기본값
                        for tool_call in state.get("tool_calls", []):
                            if tool_call.get("tool") == "meal_planner":
                                requested_days = tool_call.get("days", 7)
                                break
                        print(f"🔍 DEBUG: 식단표 생성 실패, tool_calls에서 추출한 요청 일수: {requested_days}")
                        day_text = "일" if requested_days == 1 else f"{requested_days}일"
                        state["response"] = f"{day_text} 식단표 생성에 실패했습니다."
                        return state
                else:
                    context = json.dumps(state["results"][:3], ensure_ascii=False, indent=2)
                    answer_prompt = RESPONSE_GENERATION_PROMPT.format(
                        message=message,
                        intent=state["intent"],
                        context=context
                    )
            else:
                # 기본 응답 생성 프롬프트 사용 (식당이 아닌 경우)
                if state["intent"] != "place":
                    answer_prompt = RESPONSE_GENERATION_PROMPT.format(
                        message=message,
                        intent=state["intent"],
                        context=context
                    )
                else:
                    # 식당 검색 결과가 없는 경우
                    answer_prompt = PLACE_SEARCH_FAILURE_PROMPT.format(message=message)
            
            response = await self.llm.ainvoke([HumanMessage(content=answer_prompt)])
            state["response"] = response.content
            
        except Exception as e:
            print(f"❌ Answer generation error: {e}")
            print(f"❌ Error type: {type(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            state["response"] = "죄송합니다. 답변 생성 중 오류가 발생했습니다. 다시 시도해주세요."
        
        # 성능 측정 완료
        node_end_time = time.time()
        node_time = node_end_time - node_start_time
        print(f"💬 ANSWER_NODE | Time: {node_time:.2f}s")
        
        return state
    
    def _truncate_messages_for_context(self, messages: List[BaseMessage], max_tokens: int = 4000) -> List[BaseMessage]:
        """메시지 리스트를 토큰 수에 맞게 자르기 (일반 채팅용)"""
        if not messages:
            return []
        
        # 대략적인 토큰 계산 (한국어 기준: 1토큰 ≈ 1.5글자)
        def estimate_tokens(text: str) -> int:
            return len(text) // 1.5
        
        truncated_messages = []
        current_tokens = 0
        
        # 최근 메시지부터 역순으로 처리
        for msg in reversed(messages):
            msg_text = msg.content if hasattr(msg, 'content') else str(msg)
            msg_tokens = estimate_tokens(msg_text)
            
            # 현재 메시지 + 기존 토큰이 제한을 초과하면 중단
            if current_tokens + msg_tokens > max_tokens:
                break
                
            truncated_messages.insert(0, msg)  # 원래 순서 유지
            current_tokens += msg_tokens
        
        print(f"✂️ 컨텍스트 메시지 자르기: {len(messages)}개 → {len(truncated_messages)}개 (예상 토큰: {current_tokens})")
        return truncated_messages

    def _truncate_chat_history(self, chat_history: List[Any], max_tokens: int = 8000) -> List[Any]:
        """채팅 히스토리를 토큰 수에 맞게 자르기"""
        if not chat_history:
            return []
        
        # 대략적인 토큰 계산 (한국어 기준: 1토큰 ≈ 1.5글자)
        def estimate_tokens(text: str) -> int:
            return len(text) // 1.5
        
        truncated_history = []
        current_tokens = 0
        
        # 최근 메시지부터 역순으로 처리
        for msg in reversed(chat_history):
            # ChatHistory 객체 또는 딕셔너리 모두 처리
            if hasattr(msg, 'message'):
                msg_text = msg.message
            elif isinstance(msg, dict):
                msg_text = msg.get("message", "")
            else:
                msg_text = str(msg)
            
            msg_tokens = estimate_tokens(msg_text)
            
            # 현재 메시지 + 기존 토큰이 제한을 초과하면 중단
            if current_tokens + msg_tokens > max_tokens:
                break
                
            truncated_history.insert(0, msg)  # 원래 순서 유지
            current_tokens += msg_tokens
        
        print(f"✂️ 히스토리 자르기: {len(chat_history)}개 → {len(truncated_history)}개 (예상 토큰: {current_tokens})")
        return truncated_history

    async def process_message(
        self,
        message: str,
        location: Optional[Dict[str, float]] = None,
        radius_km: float = 5.0,
        profile: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        thread_id: Optional[str] = None,
        days: Optional[int] = None  # 일수 파라미터 추가
    ) -> Dict[str, Any]:
        """메시지 처리 메인 함수"""
        
        # 성능 측정 시작
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        # 대화 히스토리를 메시지에 포함
        messages = []
        
        # 이전 대화 내용 추가 (토큰 수 제한 적용)
        if chat_history:
            # 토큰 수에 맞게 히스토리 자르기
            truncated_history = self._truncate_chat_history(chat_history, max_tokens=3000)
            
            print(f"📚 대화 히스토리 {len(truncated_history)}개 메시지를 컨텍스트에 포함")
            for msg in truncated_history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.message))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.message))
            
            # 디버그: 실제 전달되는 메시지 내용 확인
            print(f"🔍 전달되는 메시지 수: {len(messages)}")
            for i, msg in enumerate(messages):
                print(f"  {i+1}. {type(msg).__name__}: {msg.content[:50]}...")
        else:
            print("⚠️ 오케스트레이터: chat_history가 비어있습니다!")
        
        # 현재 메시지는 이미 히스토리에 포함되어 있으므로 추가하지 않음
        # (chat.py에서 DB 저장 후 히스토리에 포함됨)
        
        # 초기 상태 설정
        initial_state: AgentState = {
            "messages": messages,
            "intent": "",
            "slots": {"days": days} if days else {},
            "results": [],
            "response": "",
            "tool_calls": [],
            "profile": profile,
            "location": location,
            "radius_km": radius_km or 5.0,
            "thread_id": thread_id,  # thread_id를 state에 저장
            "chat_history": [msg.message for msg in chat_history] if chat_history else []  # chat_history 추가
        }
        
        # 워크플로우 실행
        final_state = await self.workflow.ainvoke(initial_state)
        
        # 성능 측정 완료
        end_time = time.time()
        total_time = end_time - start_time
        
        # 성능 로그 출력
        intent = final_state.get("intent", "unknown")
        results_count = len(final_state.get("results", []))
        tool_calls_count = len(final_state.get("tool_calls", []))
        
        print(f"📊 PERFORMANCE [{request_id}] | Intent: {intent} | Time: {total_time:.2f}s | Results: {results_count} | Tools: {tool_calls_count}")
        
        # 상세 성능 로그 (개발용)
        logging.info(f"PERF_DETAIL [{request_id}] | Message: {message[:50]}... | Profile: {bool(profile)} | History: {len(chat_history) if chat_history else 0}")
        
        return {
            "response": final_state["response"],
            "intent": final_state["intent"],
            "results": final_state["results"],
            "tool_calls": final_state["tool_calls"],
            "meal_plan_data": final_state.get("meal_plan_data"),  # 구조화된 식단표 데이터 포함
            "save_to_calendar_data": final_state.get("save_to_calendar_data")  # 캘린더 저장 데이터 포함
        }
    
    async def stream_response(
        self,
        message: str,
        location: Optional[Dict[str, float]] = None,
        radius_km: float = 5.0,
        profile: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """스트리밍 응답 생성"""
        
        # 노드별 스트리밍 이벤트 생성
        yield {"event": "start", "message": "처리를 시작합니다..."}
        
        # 의도 분류
        yield {"event": "routing", "message": "의도를 분석하고 있습니다..."}
        
        # 워크플로우 실행
        result = await self.process_message(message, location, radius_km, profile)
        
        # 도구 실행 이벤트들
        for tool_call in result.get("tool_calls", []):
            tool_name = tool_call["tool"]
            tool_messages = {
                "router": "의도 분석 완료",
                "recipe_search": "레시피를 검색하고 있습니다...",
                "place_search": "주변 식당을 찾고 있습니다...",
                "meal_planner": "식단표를 생성하고 있습니다..."
            }
            
            yield {
                "event": "tool_execution",
                "tool": tool_name,
                "message": tool_messages.get(tool_name, f"{tool_name} 실행 중...")
            }
            
            # 약간의 지연 추가 (UX 개선)
            await asyncio.sleep(0.5)
        
        # 최종 응답
        yield {
            "event": "complete",
            "response": result["response"],
            "intent": result["intent"],
            "results": result["results"]
        }


# 사용 예시
if __name__ == "__main__":
    async def test():
        agent = KetoCoachAgent()
        
        # 테스트 1: 식당 검색
        result = await agent.process_message(
            message="강남역 근처 키토 식당 추천해줘",
            location={"lat": 37.4979, "lng": 127.0276},
            radius_km=2.0
        )
        print("식당 검색 결과:", result)
        
        # 테스트 2: 레시피 검색
        result = await agent.process_message(
            message="저탄수 아침식사 레시피 알려줘",
            profile={"allergies": ["새우"], "goals_carbs_g": 20}
        )
        print("레시피 검색 결과:", result)
        
        # 테스트 3: 식단표 생성
        result = await agent.process_message(
            message="일주일 키토 식단표 만들어줘",
            profile={"goals_kcal": 1800, "goals_carbs_g": 30}
        )
        print("식단표 생성 결과:", result)
        
        # 테스트 4: 스트리밍
        print("\n스트리밍 테스트:")
        async for event in agent.stream_response(
            message="오늘 저녁 뭐 먹을까?",
            profile={"allergies": ["땅콩"], "dislikes": ["브로콜리"]}
        ):
            print(f"[{event['event']}] {event.get('message', '')}")
    
    # asyncio.run(test())
