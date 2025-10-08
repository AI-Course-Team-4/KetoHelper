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
from app.prompts.chat.general_chat import GENERAL_CHAT_PROMPT
from app.prompts.meal.recipe_response import RECIPE_RESPONSE_GENERATION_PROMPT
from app.prompts.restaurant.search_failure import PLACE_SEARCH_FAILURE_PROMPT
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
                
                # 캘린더 저장 요청 처리 (새로 추가!)
                if intent_value == "calendar_save":
                    print("📅 캘린더 저장 요청 감지")
                    state["intent"] = "calendar_save"
                    state["calendar_save_request"] = True
                    
                    # 대화 히스토리에서 최근 식단 데이터 찾기
                    meal_plan_data = self.calendar_utils.find_recent_meal_plan(chat_history)
                    if meal_plan_data:
                        state["meal_plan_data"] = meal_plan_data
                        # save_to_calendar_data 생성은 별도 노드에서 처리
                    else:
                        state["response"] = "저장할 식단을 찾을 수 없습니다. 먼저 식단을 생성해주세요."
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
    
    async def _recipe_search_node(self, state: AgentState) -> AgentState:
        """레시피 검색 노드 - MealPlannerAgent 우선 사용"""
        
        # 성능 측정 시작
        node_start_time = time.time()
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # MealPlannerAgent 사용 플래그 확인
            if state.get("use_meal_planner_recipe", False):
                # handle_recipe_request 메서드가 있는지 확인
                if hasattr(self.meal_planner, 'handle_recipe_request'):
                    print("🍳 MealPlannerAgent.handle_recipe_request() 사용")
                    
                    # MealPlannerAgent에 위임
                    result = await self.meal_planner.handle_recipe_request(
                        message=message,
                        state=state
                    )
                    
                    # 결과 상태에 병합
                    state.update(result)
                    return state
                else:
                    print("⚠️ handle_recipe_request 메서드 없음, 기존 방식 사용")
            
            # 기존 하이브리드 검색 로직
            
            # 채팅에서 임시 불호 식재료 추출
            temp_dislikes = temp_dislikes_extractor.extract_from_message(message)
            
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
            else:
                # 프로필이 없는 경우 임시 불호 식재료만 사용
                dislikes = temp_dislikes
            
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
                print(f"  🤖 검색 결과 없음, AI 레시피 생성 실행...")
                
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
                
                # AI 생성 레시피를 결과로 설정
                state["results"] = [{
                    "title": f"AI 생성: {message}",
                    "content": ai_recipe,
                    "source": "ai_generated",
                    "type": "recipe"
                }]
                
                state["tool_calls"].append({
                    "tool": "ai_recipe_generator",
                    "query": message,
                    "method": "gemini_generation"
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
            if state.get("profile"):
                allergies = state["profile"].get("allergies") or []
                dislikes = state["profile"].get("dislikes") or []
                goals_kcal = state["profile"].get("goals_kcal")
                goals_carbs_g = state["profile"].get("goals_carbs_g")
                parts = []
                if allergies:
                    parts.append(f"알레르기: {', '.join(allergies)}")
                if dislikes:
                    parts.append(f"비선호: {', '.join(dislikes)}")
                if goals_kcal:
                    parts.append(f"목표 칼로리: {goals_kcal}kcal")
                if goals_carbs_g is not None:
                    parts.append(f"탄수 제한: {goals_carbs_g}g")
                profile_context = "; ".join(parts)

            prompt = GENERAL_CHAT_PROMPT.format(
                message=current_message,
                profile_context=profile_context,
                context=context_text + f"\n대화 상황: {conversation_context}"
            )

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            state["response"] = response.content
            
            state["tool_calls"].append({
                "tool": "general",
                "method": "context_aware",
                "context_length": len(context_messages)
            })
            
        except Exception as e:
            print(f"General chat error: {e}")
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
        try:
            # 대화 히스토리 가져오기
            chat_history = []
            if state["messages"]:
                # 최근 10개 메시지만 확인 (토큰 절약)
                recent_messages = state["messages"][-10:] if len(state["messages"]) > 10 else state["messages"]
                for msg in recent_messages:
                    if hasattr(msg, 'content'):
                        chat_history.append(msg.content)

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
        
        # 성능 측정 시작
        node_start_time = time.time()
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # 캘린더 저장 요청 감지 및 처리 (이미 calendar_save_node에서 처리했으면 스킵)
            if self.calendar_utils.is_calendar_save_request(message) and state.get("intent") != "calendar_save":
                return await self._handle_calendar_save_request(state, message)
            
            # 이미 응답이 설정되어 있으면 그대로 사용 (calendar_save_node 등에서 설정)
            if state.get("response"):
                print("✅ 기존 응답 사용 (이미 설정됨)")
                # 캘린더/오류 단문도 MD 제목으로 보장
                if not state["response"].lstrip().startswith(("#", "##")):
                    state["response"] = f"## ℹ️ 안내\n\n{state['response']}"
                return state
            
            # MealPlannerAgent/PlaceSearchAgent가 포맷한 응답이 있으면 공통 템플릿 보장
            if state.get("formatted_response"):
                print("✅ 포맷된 응답 사용")
                # 이미 헤더가 없으면 기본 헤더 추가
                formatted = state["formatted_response"]
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
                    state["response"] = state["results"][0].get("content", "레시피 생성에 실패했습니다.")
                    return state
                
                # 검색 결과 기반 레시피 포맷팅
                elif state["intent"] == "recipe":
                    context = "추천 레시피:\n"
                    for idx, result in enumerate(state["results"][:3], 1):
                        context += f"{idx}. {result.get('title', result.get('name', '이름 없음'))}\n"
                        if result.get('content'):
                            context += f"   내용: {result['content'][:200]}...\n"
                        if result.get('ingredients'):
                            context += f"   재료: {result['ingredients']}\n"
                        if result.get('carbs'):
                            context += f"   탄수화물: {result['carbs']}g\n"
                    
                    # 레시피 전용 응답 생성 프롬프트 사용
                    answer_prompt = RECIPE_RESPONSE_GENERATION_PROMPT.format(
                        message=message,
                        context=context
                    )
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
                        
                        for day_idx, day_meals in enumerate(meal_days, 1):
                            response_text += f"**{day_idx}일차:**\n"
                            
                            for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                                if slot in day_meals and day_meals[slot]:
                                    meal = day_meals[slot]
                                    slot_name = {"breakfast": "🌅 아침", "lunch": "🌞 점심", "dinner": "🌙 저녁", "snack": "🍎 간식"}[slot]
                                    response_text += f"- {slot_name}: {meal.get('title', '메뉴 없음')}\n"
                            
                            response_text += "\n"
                        
                        # 핵심 조언만 간단히
                        notes = meal_plan.get("notes", [])
                        if notes:
                            response_text += "### 💡 키토 팁\n"
                            for note in notes[:3]:  # 최대 3개만
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
        thread_id: Optional[str] = None
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
            "slots": {},
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
