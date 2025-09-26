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
    meal_plan_data: NotRequired[Optional[Dict[str, Any]]]  # 구조화된 식단표 데이터
    save_to_calendar_data: NotRequired[Optional[Dict[str, Any]]]  # 캘린더 저장 데이터
    calendar_save_request: NotRequired[bool]  # 캘린더 저장 요청 여부 추가
    thread_id: NotRequired[Optional[str]]  # 현재 스레드 ID 추가

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
        workflow.add_node("calendar_save", self._calendar_save_node)  # 새로 추가!
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
                "calendar_save": "calendar_save",  # 새로 추가!
                "memory": "memory_update",
                "other": "general_chat"
            }
        )
        
        # 모든 노드에서 answer로 (general_chat은 직접 END로)
        workflow.add_edge("recipe_search", "answer")
        workflow.add_edge("place_search", "answer")
        workflow.add_edge("meal_plan", "answer")
        workflow.add_edge("calendar_save", "answer")  # 새로 추가!
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
                
                # 캘린더 저장 요청 처리 (새로 추가!)
                if intent_value == "calendar_save":
                    print("📅 캘린더 저장 요청 감지")
                    state["intent"] = "calendar_save"
                    state["calendar_save_request"] = True
                    
                    # 대화 히스토리에서 최근 식단 데이터 찾기
                    meal_plan_data = self._find_recent_meal_plan(chat_history)
                    if meal_plan_data:
                        state["meal_plan_data"] = meal_plan_data
                        # save_to_calendar_data 생성은 별도 노드에서 처리
                    else:
                        state["response"] = "저장할 식단을 찾을 수 없습니다. 먼저 식단을 생성해주세요."
                    return state
                
                # 나머지 기존 로직...
                if intent_value == "meal_planning" or intent_value == "mealplan":
                    state["intent"] = "mealplan"
                elif intent_value == "restaurant_search" or intent_value == "restaurant":
                    state["intent"] = "place"
                elif intent_value == "both":
                    # 식당 키워드가 더 강하면 place, 아니면 recipe
                    restaurant_keywords = ["식당", "맛집", "음식점", "카페", "레스토랑", "근처", "주변"]
                    if any(keyword in message for keyword in restaurant_keywords):
                        state["intent"] = "place"
                    else:
                        state["intent"] = "recipe"
                else:
                    state["intent"] = "other"
                
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
                state["intent"] = "other"
            
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
    
    def _find_recent_meal_plan(self, chat_history: List[str]) -> Optional[Dict]:
        """대화 히스토리에서 최근 식단 데이터 찾기"""
        
        # 역순으로 탐색 (최근 대화부터)
        for msg in reversed(chat_history[-10:]):  # 최근 10개 메시지만 확인
            # 식단표 패턴 찾기
            if "일차:" in msg or "아침:" in msg or "점심:" in msg or "저녁:" in msg:
                # 간단한 파싱 (실제로는 더 정교하게 구현 필요)
                days = []
                lines = msg.split('\n')
                
                current_day = {}
                for line in lines:
                    if '아침:' in line:
                        current_day['breakfast'] = {'title': line.split('아침:')[1].strip()}
                    elif '점심:' in line:
                        current_day['lunch'] = {'title': line.split('점심:')[1].strip()}
                    elif '저녁:' in line:
                        current_day['dinner'] = {'title': line.split('저녁:')[1].strip()}
                    elif '간식:' in line:
                        current_day['snack'] = {'title': line.split('간식:')[1].strip()}
                    
                    # 하루 단위로 저장
                    if '일차:' in line and current_day:
                        days.append(current_day)
                        current_day = {}
                
                # 마지막 날 추가
                if current_day:
                    days.append(current_day)
                
                if days:
                    # duration_days를 더 정확하게 설정
                    found_duration = len(days)
                    
                    # 메시지에서 숫자(일차) 찾기로 일수 추출
                    try:
                        from app.tools.shared.date_parser import DateParser
                        date_parser = DateParser()
                        extracted_days = date_parser._extract_duration_days(msg)
                        if extracted_days and extracted_days > 0:
                            found_duration = extracted_days
                            print(f"🔍 메시지에서 추출한 일수: {found_duration}")
                    except Exception as e:
                        print(f"⚠️ 일수 추출 중 오류: {e}")
                    
                    return {
                        'days': days,
                        'duration_days': found_duration
                    }
        
        return None

    def _route_condition(self, state: AgentState) -> str:
        """라우팅 조건 함수"""
        intent = state["intent"]
        if state.get("calendar_save_request", False):
            return "calendar_save"
        return intent
    
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
            
            # DateParser를 사용하여 정확한 일수 파싱
            from app.tools.shared.date_parser import DateParser
            date_parser = DateParser()
            
            print(f"🔍 DEBUG: 메시지: {message}")
            print(f"🔍 DEBUG: 전체 슬롯: {state['slots']}")
            
            # DateParser를 사용하여 일수 추출
            days = date_parser._extract_duration_days(message)
            
            if days is not None:
                print(f"🔍 DEBUG: DateParser가 감지한 days: {days}")
            else:
                # 슬롯에서 가져오기 (DateParser 실행 실패한 경우)
                slots_days = state["slots"].get("days")
                if slots_days:
                    days = int(slots_days)
                    print(f"🔍 DEBUG: 슬롯에서 추출된 days: {days}")
                else:
                    # 기본값 없이 사용자에게 명확한 응답 요청
                    days = None
            
            # 일수를 제대로 파악하지 못한 경우
            if days is None:
                # 식단표는 생성하지 않고 사용자에게 명확한 응답 요청
                state["response"] = "몇 일치 식단표를 원하시는지 구체적으로 말씀해주세요. (예: 5일치, 일주일치, 3일치)"
                return state
            
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
            state["response"] = "죄송합니다. 식단표 생성 중 오류가 발생했습니다. 다시 시도해주세요."
            # 에러 케이스에서는 days 값 저장하지 않음 (None이면 처리하지 않도록)
        
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
        """일반 채팅 노드 (대화 맥락 고려)"""
        
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
            
            # 키토 코치로서 대화 맥락을 고려한 응답 생성
            conversation_context = "새로운 대화입니다." if is_new_conversation else f"이전 대화 {len(previous_messages)}개가 있습니다."
            
            chat_prompt = f"""당신은 친근한 키토 다이어트 코치입니다. 사용자와의 대화를 자연스럽게 이어가세요.

대화 상황: {conversation_context}

{context_text}

다음 사항을 고려하여 응답해주세요:
1. {'새로운 대화이므로 이전 내용을 언급하지 말고, 처음 만나는 것처럼 인사하세요.' if is_new_conversation else '이전 대화 내용을 참고하여 맥락에 맞는 답변을 하세요.'}
2. 사용자가 이름을 말했다면 기억하고 다음에 사용하세요
3. 사용자가 이전에 말한 내용을 물어보면 정확히 답변하세요
4. 키토 다이어트와 관련된 조언을 제공하세요
5. 친근하고 도움이 되는 톤으로 대화하세요

응답:"""
            
            response = await self.llm.ainvoke([HumanMessage(content=chat_prompt)])
            state["response"] = response.content
            
            state["tool_calls"].append({
                "tool": "general_chat",
                "method": "context_aware",
                "context_length": len(context_messages)
            })
            
        except Exception as e:
            print(f"General chat error: {e}")
            state["response"] = "죄송합니다. 일반 채팅 처리 중 오류가 발생했습니다. 다시 시도해주세요."
        
        return state
    
    async def _calendar_save_node(self, state: AgentState) -> AgentState:
        """캘린더 저장 처리 노드"""
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # 날짜 파싱
            from app.tools.shared.date_parser import DateParser
            date_parser = DateParser()
            
            # 대화 히스토리 가져오기 (메모리 히스토리 + 데이터베이스 조회)
            chat_history = []
            
            if state["messages"]:
                chat_history = [msg.content for msg in state["messages"]]
            else:
                state["response"] = "대화 히스토리를 찾을 수 없습니다. 새로운 식단을 생성해주세요."
                return state
                
            parsed_date = date_parser.extract_date_from_message_with_context(message, chat_history)
            
            if not parsed_date:
                state["response"] = "날짜를 파악할 수 없습니다. 더 구체적으로 말씀해주세요. (예: '다음주 월요일부터', '내일부터')"
                return state
            
            # meal_plan_data를 찾기 - state에서 먼저 확인
            meal_plan_data = state.get("meal_plan_data")
            
            if not meal_plan_data:
                print(f"🔍 식단 추출 중: 기존 채팅 히스토리 {len(chat_history)}개 메시지 분석")
                meal_plan_data = self._find_recent_meal_plan(chat_history)
                
                # 메모리 히스토리에서 찾지 못한 경우 데이터베이스에서 직접 조회
                if not meal_plan_data and state.get("thread_id"):
                    try:
                        from app.core.database import supabase
                        print(f"🔍 데이터베이스 조회 시도: thread_id={state['thread_id']}")
                        db_history = supabase.table("chat").select("message").eq("thread_id", state["thread_id"]).order("created_at", desc=True).limit(20).execute()
                        
                        db_messages = [msg["message"] for msg in db_history.data if msg.get("message")]
                        print(f"🔍 데이터베이스에서 {len(db_messages)}개 메시지 조회")
                        
                        if db_messages:
                            meal_plan_data = self._find_recent_meal_plan(db_messages)
                            if meal_plan_data:
                                print(f"🔍 데이터베이스에서 식단 발견: {meal_plan_data}")
                    except Exception as db_error:
                        print(f"⚠️ 데이터베이스 조회 실패: {db_error}")
                
            if not meal_plan_data:
                state["response"] = "저장할 식단을 찾을 수 없습니다. 먼저 식단을 생성해주세요."
                return state
            
            # duration_days 추출 (더 정확한 방법 사용)
            duration_days = None
            
            # 1. meal_plan_data에서 duration_days 먼저 확인
            if 'duration_days' in meal_plan_data:
                duration_days = meal_plan_data['duration_days']
                print(f"🔍 DEBUG: meal_plan_data에서 duration_days 추출: {duration_days}")
            
            # 2. days 배열 길이로 확인
            if duration_days is None and 'days' in meal_plan_data:
                duration_days = len(meal_plan_data['days'])
                print(f"🔍 DEBUG: days 배열 길이로 duration_days 추출: {duration_days}")
            
            # 3. 대화 히스토리에서 더 정확한 일수 찾기
            if duration_days is None or duration_days == 1:
                # DateParser의 _extract_duration_days로 다시 시도
                for history_msg in reversed(chat_history[-5:]):
                    extracted_days = date_parser._extract_duration_days(history_msg)
                    if extracted_days and extracted_days > 1:
                        duration_days = extracted_days
                        print(f"🔍 DEBUG: 채팅 히스토리에서 일수 재추출: {duration_days}")
                        break
            
            # 최종 기본값 (1일이 아니면)
            if duration_days is None:
                duration_days = 3  # 기본 3일
                print(f"🔍 DEBUG: 기본값 사용: {duration_days}일")
            
            print(f"🔍 DEBUG: 캘린더 저장 - meal_plan_data: {meal_plan_data}")
            print(f"🔍 DEBUG: 캘린더 저장 - 최종 duration_days: {duration_days}")
            print(f"🔍 DEBUG: 캘린더 저장 - parsed_date.date: {parsed_date.date}")
            print(f"🔍 DEBUG: 캘린더 저장 - parsed_date.description: {parsed_date.description}")
            
            # 일별 식단 데이터를 직접 포함한 save_data 생성
            days_data = []
            
            if meal_plan_data and 'days' in meal_plan_data:
                days_data = meal_plan_data['days']
            else:
                # 기본 식단으로 fallback
                for i in range(duration_days):
                    days_data.append({
                        'breakfast': {'title': f'키토 아침 메뉴 {i+1}일차'},
                        'lunch': {'title': f'키토 점심 메뉴 {i+1}일차'},
                        'dinner': {'title': f'키토 저녁 메뉴 {i+1}일차'},
                        'snack': {'title': f'키토 간식 {i+1}일차'}
                    })
            
            save_data = {
                "action": "save_to_calendar",
                "start_date": parsed_date.date.isoformat(),
                "duration_days": duration_days,
                "meal_plan_data": meal_plan_data,
                "days_data": days_data,  # 직접 프론트엔드에서 사용할 수 있는 일별 데이터 추가
                "message": f"{duration_days}일치 식단표를 {parsed_date.date.strftime('%Y년 %m월 %d일')}부터 캘린더에 저장합니다."
            }
            
            print(f"🔍 DEBUG: save_data 구조: {save_data}")
            print(f"🔍 DEBUG: days_data 길이: {len(days_data)}")
            
            # 실제 Supabase에 식단 데이터 저장
            try:
                from app.core.database import supabase
                from datetime import datetime as dt_module, timedelta
                
                # user_id 가져오기 - 여러 방법으로 시도
                user_id = None
                
                # 1. profile에서 확인
                if state.get("profile") and state["profile"].get("user_id"):
                    user_id = state["profile"]["user_id"]
                    print(f"🔍 DEBUG: user_id from profile: {user_id}")
                
                # 2. state에서 직접 user_id 확인
                if not user_id and state.get("user_id"):
                    user_id = state["user_id"]
                    print(f"🔍 DEBUG: user_id from state: {user_id}")
                
                # 3. thread_id로 데이터베이스에서 조회
                if not user_id and state.get("thread_id"):
                    try:
                        thread_response = supabase.table("chat_thread").select("user_id").eq("id", state["thread_id"]).execute()
                        if thread_response.data:
                            user_id = thread_response.data[0].get("user_id")
                            print(f"🔍 DEBUG: user_id from thread: {user_id}")
                    except Exception as thread_error:
                        print(f"⚠️ thread에서 user_id 조회 실패: {thread_error}")
                
                if not user_id:
                    # 사용자 정보를 찾지 못한 경우 알려준다
                    print(f"⚠️ 사용자 정보를 찾을 수 없어 실제 저장을 건너뜁니다")
                    state["response"] = f"데이터를 준비했습니다만, 사용자 정보가 필요합니다. 프론트엔드에서 완료될 예정입니다."
                else:
                    # 기존 해당 기간 데이터 삭제 (충돌 방지)
                    end_date = parsed_date.date + timedelta(days=duration_days - 1)
                    delete_result = supabase.table('meal_log').delete()\
                        .eq('user_id', str(user_id))\
                        .gte('date', parsed_date.date.isoformat())\
                        .lte('date', end_date.isoformat()).execute()
                    print(f"🔍 DEBUG: 기존 데이터 삭제 결과: {delete_result}")
                    
                    # 새 meal_log 데이터 생성
                    meal_logs_to_create = []
                    current_date = parsed_date.date
                    
                    for i, day_data in enumerate(days_data):
                        date_string = current_date.isoformat()
                        
                        # 각 식사 시간대별로 meal_log 생성
                        meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
                        for slot in meal_types:
                            if slot in day_data and day_data[slot]:
                                meal_item = day_data[slot]
                                meal_title = ""
                                
                                if isinstance(meal_item, str):
                                    meal_title = meal_item
                                elif isinstance(meal_item, dict) and meal_item.get('title'):
                                    meal_title = meal_item['title']
                                else:
                                    meal_title = str(meal_item) if meal_item else ""
                                
                                if meal_title and meal_title.strip():
                                    meal_log = {
                                        "user_id": str(user_id),
                                        "date": date_string,
                                        "meal_type": slot,
                                        "eaten": False,
                                        "note": meal_title.strip(),
                                        "created_at": dt_module.utcnow().isoformat(),
                                        "updated_at": dt_module.utcnow().isoformat()
                                    }
                                    meal_logs_to_create.append(meal_log)
                                    print(f"🔍 DEBUG: meal_log 추가: {meal_log}")
                        
                        current_date += timedelta(days=1)
                    
                    # Supabase에 일괄 저장
                    if meal_logs_to_create:
                        print(f"🔍 DEBUG: Supabase에 {len(meal_logs_to_create)}개 데이터 저장 시도")
                        result = supabase.table('meal_log').insert(meal_logs_to_create).execute()
                        print(f"🔍 DEBUG: Supabase 저장 결과: {result}")
                        
                        if result.data:
                            state["response"] = f"✅ {duration_days}일치 식단표가 캘린더에 성공적으로 저장되었습니다! {parsed_date.date.strftime('%Y년 %m월 %d일')}부터 해주시겠어요! 📅✨"
                        else:
                            state["response"] = f"식단을 준비했습니다만 저장 중 오류가 발생했습니다. 다시 시도해주세요."
                    else:
                        state["response"] = "저장할 식단 데이터를 찾을 수 없습니다."
                        
            except Exception as save_error:
                print(f"❌ Supabase 저장 중 오류 발생: {save_error}")
                import traceback
                print(f"❌ 상세 저장 오류: {traceback.format_exc()}")
                state["response"] = f"식단 데이터를 준비했습니다만 저장 중 오류가 발생했습니다. 프론트엔드에서 완료될 예정입니다."
            
            # fallback으로 프론트엔드에 저장 데이터도 전달
            state["save_to_calendar_data"] = save_data
            state["meal_plan_data"] = meal_plan_data
            
            return state
            
        except Exception as e:
            print(f"❌ 캘린더 저장 처리 오류: {e}")
            import traceback
            print(f"❌ 상세 오류: {traceback.format_exc()}")
            state["response"] = "죄송합니다. 캘린더 저장 처리 중 오류가 발생했습니다. 다시 시도해주세요."
            return state
    
    def _is_calendar_save_request(self, message: str) -> bool:
        """캘린더 저장 요청인지 감지"""
        save_keywords = ['저장', '추가', '계획', '등록', '넣어', '캘린더', '일정']
        date_keywords = ['다음주', '내일', '오늘', '모레', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        
        has_save_keyword = any(keyword in message for keyword in save_keywords)
        has_date_keyword = any(keyword in message for keyword in date_keywords)
        
        return has_save_keyword and has_date_keyword
    
    async def _handle_calendar_save_request(self, state: AgentState, message: str) -> AgentState:
        """캘린더 저장 요청 처리"""
        try:
            # 대화 히스토리에서 이전 식단표 데이터 찾기
            chat_history = []
            if state["messages"]:
                # 최근 10개 메시지만 확인 (토큰 절약)
                recent_messages = state["messages"][-10:] if len(state["messages"]) > 10 else state["messages"]
                for msg in recent_messages:
                    if hasattr(msg, 'content'):
                        chat_history.append(msg.content)
            
            # 날짜 파싱 (date_parser 사용)
            from app.tools.shared.date_parser import DateParser
            date_parser = DateParser()
            
            parsed_date = date_parser.extract_date_from_message_with_context(message, chat_history)
            if not parsed_date or not parsed_date.date:
                state["response"] = "죄송합니다. 날짜를 파악할 수 없습니다. 더 구체적으로 말씀해주세요. (예: '다음주 월요일부터', '내일부터')"
                return state
            
            # 대화 히스토리에서 meal_plan_data 찾기
            meal_plan_data = None
            duration_days = parsed_date.duration_days or 7  # 기본값 7일
            
            # 히스토리에서 식단표 관련 키워드와 일수 정보 찾기
            for history_msg in reversed(chat_history):
                # 동적 일수 파싱
                context_duration = date_parser._extract_duration_days(history_msg)
                if context_duration:
                    duration_days = context_duration
                    print(f"🔍 대화 맥락에서 일수 정보 발견: {duration_days}일")
                    break
                
                # 식단표 생성 메시지인지 확인
                if any(word in history_msg for word in ["식단표", "식단", "계획", "추천"]) and any(word in history_msg for word in ["만들어", "생성", "계획해"]):
                    break
            
            # 구조화된 저장 데이터 생성
            save_data = {
                "action": "save_to_calendar",
                "start_date": parsed_date.date.isoformat(),
                "duration_days": duration_days,
                "message": f"{duration_days}일치 식단표를 {parsed_date.date.strftime('%Y년 %m월 %d일')}부터 캘린더에 저장합니다."
            }
            
            # 응답 메시지 생성
            response_message = f"네! {duration_days}일치 식단표를 {parsed_date.date.strftime('%Y년 %m월 %d일')}부터 캘린더에 저장해드릴게요! 🗓️✨"
            
            state["response"] = response_message
            state["save_to_calendar_data"] = save_data
            
            return state
            
        except Exception as e:
            print(f"❌ 캘린더 저장 요청 처리 오류: {e}")
            state["response"] = "죄송합니다. 캘린더 저장 처리 중 오류가 발생했습니다. 다시 시도해주세요."
            return state
    
    async def _answer_node(self, state: AgentState) -> AgentState:
        """최종 응답 생성 노드"""
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # 캘린더 저장 요청 감지 및 처리
            if self._is_calendar_save_request(message):
                return await self._handle_calendar_save_request(state, message)
            
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
            "thread_id": thread_id  # thread_id를 state에 저장
        }
        
        # 워크플로우 실행
        final_state = await self.workflow.ainvoke(initial_state)
        
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