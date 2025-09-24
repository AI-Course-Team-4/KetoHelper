"""
LangGraph 기반 키토 코치 에이전트 오케스트레이터
의도 분류 → 도구 실행 → 응답 생성의 전체 플로우 관리
하이브리드 방식: IntentClassifier(키워드) + LLM 병합
"""

import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, BaseMessage
import json
import re

from app.core.config import settings
from app.core.intent_classifier import IntentClassifier, Intent  # 추가
from app.tools.shared.hybrid_search import hybrid_search_tool
from app.tools.restaurant.place_search import PlaceSearchTool
from app.tools.restaurant.restaurant_hybrid_search import restaurant_hybrid_search_tool
from app.tools.meal.keto_score import KetoScoreCalculator
from app.tools.shared.temporary_dislikes_extractor import temp_dislikes_extractor
from app.agents.meal_planner import MealPlannerAgent
from app.agents.chat_agent import SimpleKetoCoachAgent

# 프롬프트 모듈 import (중앙집중화된 구조)
from app.prompts.chat.intent_classification import INTENT_CLASSIFICATION_PROMPT, get_intent_prompt
from app.prompts.chat.memory_update import MEMORY_UPDATE_PROMPT
from app.prompts.chat.response_generation import RESPONSE_GENERATION_PROMPT, RESTAURANT_RESPONSE_GENERATION_PROMPT
from app.prompts.meal.recipe_response import RECIPE_RESPONSE_GENERATION_PROMPT
from app.prompts.restaurant.search_improvement import PLACE_SEARCH_IMPROVEMENT_PROMPT
from app.prompts.restaurant.search_failure import PLACE_SEARCH_FAILURE_PROMPT

from typing_extensions import TypedDict, NotRequired

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

class KetoCoachAgent:
    """키토 코치 메인 에이전트 (LangGraph 오케스트레이터)"""
    
    def __init__(self):
        try:
            # Gemini LLM 초기화
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=settings.gemini_temperature,
                max_tokens=settings.gemini_max_tokens
            )
        except Exception as e:
            print(f"Gemini AI 초기화 실패: {e}")
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
        self.place_search = PlaceSearchTool()
        self.restaurant_hybrid_search = restaurant_hybrid_search_tool  # 식당 RAG 검색
        self.keto_score = KetoScoreCalculator() 
        self.meal_planner = MealPlannerAgent()
        self.simple_agent = SimpleKetoCoachAgent()
        
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
        workflow.add_node("memory_update", self._memory_update_node)
        workflow.add_node("general_chat", self._general_chat_node)
        workflow.add_node("answer", self._answer_node)
        
        # 시작점 설정
        workflow.set_entry_point("router")
        
        # 라우터에서 각 노드로의 조건부 엣지
        workflow.add_conditional_edges(
            "router",
            self._route_condition,
            {
                "recipe": "recipe_search",
                "place": "place_search",
                "mealplan": "meal_plan",
                "memory": "memory_update",
                "other": "general_chat"
            }
        )
        
        # 모든 노드에서 answer로 (general_chat은 직접 END로)
        workflow.add_edge("recipe_search", "answer")
        workflow.add_edge("place_search", "answer")
        workflow.add_edge("meal_plan", "answer")
        workflow.add_edge("memory_update", "answer")
        workflow.add_edge("general_chat", END)
        workflow.add_edge("answer", END)
        
        return workflow.compile()
    
    def _map_intent_to_route(self, intent_enum: Intent, message: str, slots: Dict[str, Any]) -> str:
        """IntentClassifier의 Intent enum을 orchestrator 라우팅 키로 변환
        
        IntentClassifier Intent -> Orchestrator Route 매핑:
        - MEAL_PLANNING -> recipe 또는 mealplan (세분화 필요)
        - RESTAURANT_SEARCH -> place
        - BOTH -> 우선순위에 따라 결정
        - GENERAL -> other
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
        
        elif intent_enum == Intent.RESTAURANT_SEARCH:
            return "place"
        
        elif intent_enum == Intent.BOTH:
            # 식당 키워드가 더 강하면 place, 아니면 recipe
            restaurant_keywords = ["식당", "맛집", "음식점", "카페", "레스토랑", "근처", "주변"]
            if any(keyword in message for keyword in restaurant_keywords):
                print(f"  🏪 BOTH → 식당 우선")
                return "place"
            print(f"  🍳 BOTH → 레시피 우선")
            return "recipe"
        
        else:  # Intent.GENERAL
            return "other"
    
    async def _router_node(self, state: AgentState) -> AgentState:
        """하이브리드 의도 분류 노드
        
        1. IntentClassifier로 빠른 키워드 기반 분류
        2. 높은 확신도(0.8+) → 바로 사용
        3. 낮은 확신도 → LLM 분류로 폴백
        4. 두 결과를 병합하여 최종 결정
        """
        
        message = state["messages"][-1].content if state["messages"] else ""
        
        try:
            print(f"\n🎯 하이브리드 의도 분류 시작: '{message[:50]}...'")
            
            # IntentClassifier 사용 가능 여부 확인
            if self.intent_classifier:
                # 1단계: IntentClassifier로 빠른 분류
                quick_result = await self.intent_classifier.classify_intent(
                    user_input=message,
                    context=""
                )
                
                quick_intent = quick_result["intent"]
                quick_confidence = quick_result["confidence"]
                quick_method = quick_result.get("method", "unknown")
                
                # 슬롯 추출
                quick_slots = self.intent_classifier.extract_slots(message, quick_intent)
                
                print(f"  📊 키워드 분류: {quick_intent.value} (확신도: {quick_confidence:.2f}, 방법: {quick_method})")
                print(f"  📦 추출된 슬롯: {quick_slots}")
                
                # 2단계: 높은 확신도면 바로 사용
                if quick_confidence >= 0.8:
                    print(f"  ✅ 높은 확신도 → 키워드 분류 채택")
                    
                    # Intent enum을 라우팅 키로 변환
                    mapped_intent = self._map_intent_to_route(quick_intent, message, quick_slots)
                    state["intent"] = mapped_intent
                    state["slots"] = quick_slots
                    
                    # 추가 검증 (기존 로직 유지)
                    state["intent"] = self._validate_intent(message, state["intent"])
                    
                    print(f"  🎯 최종 의도: {state['intent']}")
                    
                    state["tool_calls"].append({
                        "tool": "router",
                        "method": "keyword_based",
                        "intent": state["intent"],
                        "slots": state["slots"],
                        "confidence": quick_confidence
                    })
                    
                    return state
                
                else:
                    # 3단계: 낮은 확신도 → LLM 분류
                    print(f"  🤖 낮은 확신도 → LLM 분류 실행")
                    
                    # 향상된 프롬프트 사용 (키워드 힌트 포함)
                    enhanced_prompt = get_intent_prompt(
                        message=message,
                        keyword_intent=quick_intent.value,
                        confidence=quick_confidence
                    )
                    
                    response = await self.llm.ainvoke([HumanMessage(content=enhanced_prompt)])
                    
                    # JSON 파싱
                    json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        llm_intent = result.get("intent", "other")
                        llm_slots = result.get("slots", {})
                        
                        print(f"  🤖 LLM 분류: {llm_intent}")
                        
                        # 4단계: 결과 병합
                        # LLM 결과를 우선하되, 슬롯은 병합
                        state["intent"] = llm_intent
                        state["slots"] = {**quick_slots, **llm_slots}  # 병합
                        
                        # 추가 검증
                        state["intent"] = self._validate_intent(message, state["intent"])
                        
                        print(f"  🎯 최종 의도: {state['intent']} (LLM 기반)")
                        
                        state["tool_calls"].append({
                            "tool": "router",
                            "method": "hybrid_llm",
                            "intent": state["intent"],
                            "slots": state["slots"],
                            "keyword_hint": quick_intent.value,
                            "keyword_confidence": quick_confidence
                        })
                    else:
                        # JSON 파싱 실패 시 키워드 결과 사용
                        mapped_intent = self._map_intent_to_route(quick_intent, message, quick_slots)
                        state["intent"] = mapped_intent
                        state["slots"] = quick_slots
                        state["intent"] = self._validate_intent(message, state["intent"])
                        
                        state["tool_calls"].append({
                            "tool": "router",
                            "method": "keyword_fallback",
                            "intent": state["intent"],
                            "slots": state["slots"]
                        })
            
            else:
                # IntentClassifier 없으면 기존 LLM 방식 사용
                print("  ⚠️ IntentClassifier 사용 불가 → 기존 LLM 방식")
                
                # 기본 프롬프트 사용 (키워드 힌트 없음)
                router_prompt = get_intent_prompt(message=message)
                response = await self.llm.ainvoke([HumanMessage(content=router_prompt)])
                
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    initial_intent = result.get("intent", "other")
                    state["slots"] = result.get("slots", {})
                    state["intent"] = self._validate_intent(message, initial_intent)
                    
                    state["tool_calls"].append({
                        "tool": "router",
                        "method": "llm_only",
                        "intent": state["intent"],
                        "slots": state["slots"]
                    })
                else:
                    state["intent"] = "other"
                    state["slots"] = {}
                    
                    state["tool_calls"].append({
                        "tool": "router",
                        "method": "default",
                        "intent": "other",
                        "slots": {}
                    })
            
        except Exception as e:
            print(f"  ❌ Router error: {e}")
            state["intent"] = "other"
            state["slots"] = {}
            
            state["tool_calls"].append({
                "tool": "router",
                "method": "error",
                "intent": "other",
                "error": str(e)
            })
        
        print(f"  📍 라우팅 결정: {state['intent']} → {self._route_condition(state)}")
        
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
                print(f"    🔍 검증: mealplan이지만 구체적 요청 없음 → other로 변경")
                return "other"
        
        # recipe 의도인데 구체적인 요리 요청이 아닌 경우
        if initial_intent == "recipe":
            recipe_patterns = [
                r'레시피', r'조리법', r'만드는.*법', r'어떻게.*만들어',
                r'요리.*방법', r'만들어.*줘', r'만들어.*달라'
            ]
            
            has_recipe_request = any(re.search(pattern, message, re.IGNORECASE) for pattern in recipe_patterns)
            if not has_recipe_request:
                print(f"    🔍 검증: recipe이지만 구체적 요청 없음 → other로 변경")
                return "other"
        
        # place 의도인데 구체적인 장소 검색 요청이 아닌 경우
        if initial_intent == "place":
            place_patterns = [
                r'식당.*찾아', r'식당.*추천', r'근처.*식당', r'어디.*있어',
                r'위치.*알려', r'장소.*알려', r'검색.*해줘'
            ]
            
            has_place_request = any(re.search(pattern, message, re.IGNORECASE) for pattern in place_patterns)
            if not has_place_request:
                print(f"    🔍 검증: place이지만 구체적 요청 없음 → other로 변경")
                return "other"
        
        return initial_intent

    def _route_condition(self, state: AgentState) -> str:
        """라우팅 조건 함수"""
        return state["intent"]
    
    async def _recipe_search_node(self, state: AgentState) -> AgentState:
        """레시피 검색 노드 (Hybrid Search 사용)"""
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
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
            search_results = await self.hybrid_search.search(
                query=full_query,
                max_results=5
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
        
        return state
    
    async def _place_search_node(self, state: AgentState) -> AgentState:
        """장소 검색 노드 (RAG + 카카오 API 병행)"""
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # 위치 정보 추출
            lat = state["location"].get("lat", 37.4979) if state["location"] else 37.4979  # 기본: 강남역
            lng = state["location"].get("lng", 127.0276) if state["location"] else 127.0276
            
            print(f"🔍 식당 검색 시작: '{message}' (위치: {lat}, {lng})")
            
            # 1. RAG 검색 실행
            print("  🤖 RAG 검색 실행 중...")
            rag_results = []
            try:
                rag_results = await self.restaurant_hybrid_search.hybrid_search(
                    query=message,
                    location={"lat": lat, "lng": lng},
                    max_results=10
                )
                print(f"  ✅ RAG 검색 결과: {len(rag_results)}개")
            except Exception as e:
                print(f"  ❌ RAG 검색 실패: {e}")
            
            # 2. 카카오 API 검색 실행 (기존 로직)
            print("  📍 카카오 API 검색 실행 중...")
            kakao_results = []
            try:
                # 검색 쿼리 개선
                query_improvement_prompt = PLACE_SEARCH_IMPROVEMENT_PROMPT.format(message=message)
                llm_response = await self.llm.ainvoke([HumanMessage(content=query_improvement_prompt)])
                search_keywords = llm_response.content.strip().split(", ")
                
                print(f"  🔍 LLM 생성 키워드: {search_keywords[:3]}")
                
                all_places = []
                
                # 각 키워드로 검색
                for keyword in search_keywords[:3]:  # 최대 3개 키워드
                    places = await self.place_search.search(
                        query=keyword.strip('"'),
                        lat=lat,
                        lng=lng,
                        radius=int(state["radius_km"] * 1000)
                    )
                    
                    # 키토 스코어 계산
                    for place in places:
                        score_result = self.keto_score.calculate_score(
                            name=place.get("name", ""),
                            category=place.get("category", ""),
                            address=place.get("address", "")
                        )
                        
                        place.update({
                            "keto_score": score_result["score"],
                            "why": score_result["reasons"],
                            "tips": score_result["tips"],
                            "source": "kakao_api"
                        })
                        
                        all_places.append(place)
                
                # 중복 제거
                unique_places = {}
                for place in all_places:
                    place_id = place.get("id", "")
                    if place_id not in unique_places or place["keto_score"] > unique_places[place_id]["keto_score"]:
                        unique_places[place_id] = place
                
                kakao_results = list(unique_places.values())
                print(f"  ✅ 카카오 API 검색 결과: {len(kakao_results)}개")
                
            except Exception as e:
                print(f"  ❌ 카카오 API 검색 실패: {e}")
            
            # 3. 결과 통합 및 정렬
            print("  🔄 결과 통합 중...")
            all_results = []
            
            # RAG 결과 변환 (표준 포맷으로)
            for result in rag_results:
                all_results.append({
                    "id": result.get("restaurant_id", ""),
                    "name": result.get("restaurant_name", ""),
                    "category": result.get("category", ""),
                    "address": result.get("addr_road", result.get("addr_jibun", "")),
                    "lat": result.get("lat", 0.0),
                    "lng": result.get("lng", 0.0),
                    "phone": result.get("phone", ""),
                    "keto_score": result.get("keto_score", 0),
                    "why": result.get("keto_reasons", {}),
                    "tips": [],
                    "source": "rag",
                    "menu_info": {
                        "name": result.get("menu_name", ""),
                        "description": result.get("menu_description", ""),
                        "price": result.get("menu_price")
                    },
                    "similarity": result.get("similarity", 0.0),
                    "final_score": result.get("final_score", 0.0)
                })
            
            # 카카오 결과 추가
            all_results.extend(kakao_results)
            
            # 중복 제거 (이름 + 주소 기준)
            unique_results = {}
            for result in all_results:
                key = f"{result.get('name', '')}_{result.get('address', '')}"
                if key not in unique_results:
                    unique_results[key] = result
                else:
                    # 더 높은 점수의 결과 선택
                    existing_score = unique_results[key].get("keto_score", 0)
                    current_score = result.get("keto_score", 0)
                    if current_score > existing_score:
                        unique_results[key] = result
            
            # 최종 정렬 (키토 스코어 + RAG 점수 고려)
            final_results = sorted(
                unique_results.values(),
                key=lambda x: (x.get("keto_score", 0), x.get("final_score", 0), x.get("similarity", 0)),
                reverse=True
            )
            
            state["results"] = final_results[:10]  # 상위 10개
            state["tool_calls"].append({
                "tool": "hybrid_place_search",
                "rag_results": len(rag_results),
                "kakao_results": len(kakao_results),
                "final_results": len(state["results"]),
                "location": {"lat": lat, "lng": lng}
            })
            
            print(f"  ✅ 최종 결과: {len(state['results'])}개 (RAG: {len(rag_results)}, 카카오: {len(kakao_results)})")
            
        except Exception as e:
            print(f"Place search error: {e}")
            state["results"] = []
        
        return state
    
    async def _meal_plan_node(self, state: AgentState) -> AgentState:
        """식단표 생성 노드"""
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # 채팅에서 임시 불호 식재료 추출
            temp_dislikes = temp_dislikes_extractor.extract_from_message(message)
            
            # 먼저 메시지에서 직접 일수 파싱 (더 확실한 방법)
            days = 7  # 기본값
            
            print(f"🔍 DEBUG: 메시지: {message}")
            print(f"🔍 DEBUG: 전체 슬롯: {state['slots']}")
            
            # 메시지에서 직접 일수 파싱
            if any(word in message for word in ["하루치", "하루", "1일", "오늘"]):
                days = 1
                print(f"🔍 DEBUG: 메시지에서 하루치 감지 → days = 1")
            elif any(word in message for word in ["이틀", "2일"]):
                days = 2
                print(f"🔍 DEBUG: 메시지에서 이틀 감지 → days = 2")
            elif any(word in message for word in ["3일", "사흘"]):
                days = 3
                print(f"🔍 DEBUG: 메시지에서 3일 감지 → days = 3")
            elif any(word in message for word in ["이번주", "다음주", "일주일", "한주", "한 주"]):
                days = 7
                print(f"🔍 DEBUG: 메시지에서 주간 감지 → days = 7")
            else:
                # 슬롯에서 가져오기 (메시지 파싱이 실패한 경우)
                days = int(state["slots"].get("days", 7)) if state["slots"].get("days") else 7
                print(f"🔍 DEBUG: 슬롯에서 추출된 days: {days}")
            
            print(f"🔍 DEBUG: 최종 days: {days}")
            
            # 프로필에서 제약 조건 추출
            kcal_target = None
            carbs_max = 30
            allergies = []
            dislikes = []
            
            if state["profile"]:
                kcal_target = state["profile"].get("goals_kcal")
                carbs_max = state["profile"].get("goals_carbs_g", 30)
                allergies = state["profile"].get("allergies", [])
                profile_dislikes = state["profile"].get("dislikes", [])
                
                # 임시 불호 식재료와 프로필 불호 식재료 합치기
                dislikes = temp_dislikes_extractor.combine_with_profile_dislikes(
                    temp_dislikes, profile_dislikes
                )
            else:
                # 프로필이 없는 경우 임시 불호 식재료만 사용
                dislikes = temp_dislikes
            
            # 식단표 생성
            meal_plan = await self.meal_planner.generate_meal_plan(
                days=days,
                kcal_target=kcal_target,
                carbs_max=carbs_max,
                allergies=allergies,
                dislikes=dislikes,
                fast_mode=True  # 빠른 모드 활성화
            )
            
            state["results"] = [meal_plan]
            state["tool_calls"].append({
                "tool": "meal_planner",
                "days": days,
                "constraints": {
                    "kcal_target": kcal_target,
                    "carbs_max": carbs_max,
                    "allergies": allergies,
                    "dislikes": dislikes
                }
            })
            
            # days 값을 state에 저장 (answer_node에서 사용하기 위해)
            state["meal_plan_days"] = days
            print(f"🔍 DEBUG: state에 meal_plan_days 저장: {days}")
            
        except Exception as e:
            print(f"Meal plan error: {e}")
            state["results"] = []
            # 에러 케이스에서도 days 값 저장
            state["meal_plan_days"] = days
            print(f"🔍 DEBUG: 에러 케이스에서도 state에 meal_plan_days 저장: {days}")
        
        return state
    
    async def _memory_update_node(self, state: AgentState) -> AgentState:
        """메모리/프로필 업데이트 노드"""
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # 프로필 업데이트 정보 추출
            update_prompt = MEMORY_UPDATE_PROMPT.format(message=message)
            
            response = await self.llm.ainvoke([HumanMessage(content=update_prompt)])
            
            # JSON 파싱 및 프로필 업데이트
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                updates = json.loads(json_match.group())
                if not state["profile"]:
                    state["profile"] = {}
                
                for key, value in updates.items():
                    if value:  # 빈 값이 아닌 경우만 업데이트
                        state["profile"][key] = value
                
                state["tool_calls"].append({
                    "tool": "memory_update",
                    "updates": updates
                })
            
        except Exception as e:
            print(f"Memory update error: {e}")
        
        return state
    
    async def _general_chat_node(self, state: AgentState) -> AgentState:
        """일반 채팅 노드 (simple_agent 사용)"""
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # simple_agent를 통한 일반 채팅 처리
            result = await self.simple_agent.process_message(
                message=message,
                location=state.get("location"),
                radius_km=state.get("radius_km", 5.0),
                profile=state.get("profile")
            )
            
            # 결과를 state에 저장
            state["response"] = result.get("response", "")
            state["tool_calls"].extend(result.get("tool_calls", []))
            
        except Exception as e:
            print(f"General chat error: {e}")
            state["response"] = "죄송합니다. 일반 채팅 처리 중 오류가 발생했습니다. 다시 시도해주세요."
        
        return state
    
    async def _answer_node(self, state: AgentState) -> AgentState:
        """최종 응답 생성 노드"""
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
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
                    answer_prompt = RESTAURANT_RESPONSE_GENERATION_PROMPT.format(
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
                        
                        # 바로 응답 반환 (LLM 재생성 건너뛰기)
                        state["response"] = response_text
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
        
        return state
    
    async def process_message(
        self,
        message: str,
        location: Optional[Dict[str, float]] = None,
        radius_km: float = 5.0,
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """메시지 처리 메인 함수"""
        
        # 초기 상태 설정
        initial_state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "intent": "",
            "slots": {},
            "results": [],
            "response": "",
            "tool_calls": [],
            "profile": profile,
            "location": location,
            "radius_km": radius_km or 5.0
        }
        
        # 워크플로우 실행
        final_state = await self.workflow.ainvoke(initial_state)
        
        return {
            "response": final_state["response"],
            "intent": final_state["intent"],
            "results": final_state["results"],
            "tool_calls": final_state["tool_calls"]
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
                "meal_planner": "식단표를 생성하고 있습니다...",
                "memory_update": "프로필을 업데이트하고 있습니다..."
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