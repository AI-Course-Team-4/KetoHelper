"""
LangGraph 기반 키토 코치 에이전트 오케스트레이터
의도 분류 → 도구 실행 → 응답 생성의 전체 플로우 관리
"""

import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, BaseMessage
import json
import re

from app.core.config import settings
from app.shared.tools.hybrid_search import hybrid_search_tool
from app.restaurant.tools.place_search import PlaceSearchTool
from app.meal.tools.keto_score import KetoScoreCalculator
from app.meal.agents.meal_planner import MealPlannerAgent
from app.chat.agents.simple_agent import SimpleKetoCoachAgent

# 프롬프트 모듈 import
from app.chat.prompts.intent_classification import INTENT_CLASSIFICATION_PROMPT
from app.chat.prompts.memory_update import MEMORY_UPDATE_PROMPT
from app.chat.prompts.response_generation import RESPONSE_GENERATION_PROMPT
from app.restaurant.prompts.place_search_improvement import PLACE_SEARCH_IMPROVEMENT_PROMPT
from app.restaurant.prompts.search_failure import PLACE_SEARCH_FAILURE_PROMPT

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
        
        # 도구들 초기화
        self.hybrid_search = hybrid_search_tool  # 이미 초기화된 인스턴스 사용
        self.place_search = PlaceSearchTool()
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
    
    async def _router_node(self, state: AgentState) -> AgentState:
        """의도 분류 노드"""
        
        message = state["messages"][-1].content if state["messages"] else ""
        
        router_prompt = INTENT_CLASSIFICATION_PROMPT.format(message=message)
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=router_prompt)])
            
            # JSON 파싱
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                state["intent"] = result.get("intent", "other")
                state["slots"] = result.get("slots", {})
            else:
                state["intent"] = "other"
                state["slots"] = {}
            
            state["tool_calls"].append({
                "tool": "router",
                "intent": state["intent"],
                "slots": state["slots"]
            })
            
        except Exception as e:
            print(f"Router error: {e}")
            state["intent"] = "other"
            state["slots"] = {}
        
        return state
    
    def _route_condition(self, state: AgentState) -> str:
        """라우팅 조건 함수"""
        return state["intent"]
    
    async def _recipe_search_node(self, state: AgentState) -> AgentState:
        """레시피 검색 노드 (Hybrid Search 사용)"""
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # 프로필 정보 반영
            profile_context = ""
            if state["profile"]:
                allergies = state["profile"].get("allergies", [])
                dislikes = state["profile"].get("dislikes", [])
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
        """장소 검색 노드"""
        
        try:
            message = state["messages"][-1].content if state["messages"] else ""
            
            # 위치 정보 추출
            lat = state["location"].get("lat", 37.4979) if state["location"] else 37.4979  # 기본: 강남역
            lng = state["location"].get("lng", 127.0276) if state["location"] else 127.0276
            
            # 검색 쿼리 개선
            query_improvement_prompt = PLACE_SEARCH_IMPROVEMENT_PROMPT.format(message=message)
            
            llm_response = await self.llm.ainvoke([HumanMessage(content=query_improvement_prompt)])
            search_keywords = llm_response.content.strip().split(", ")
            
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
                        "tips": score_result["tips"]
                    })
                    
                    all_places.append(place)
            
            # 중복 제거 및 정렬
            unique_places = {}
            for place in all_places:
                place_id = place.get("id", "")
                if place_id not in unique_places or place["keto_score"] > unique_places[place_id]["keto_score"]:
                    unique_places[place_id] = place
            
            # 키토 스코어 순 정렬
            sorted_places = sorted(
                unique_places.values(),
                key=lambda x: x["keto_score"],
                reverse=True
            )
            
            state["results"] = sorted_places[:10]  # 상위 10개
            state["tool_calls"].append({
                "tool": "place_search",
                "keywords": search_keywords,
                "location": {"lat": lat, "lng": lng},
                "results_count": len(state["results"])
            })
            
        except Exception as e:
            print(f"Place search error: {e}")
            state["results"] = []
        
        return state
    
    async def _meal_plan_node(self, state: AgentState) -> AgentState:
        """식단표 생성 노드"""
        
        try:
            # 슬롯에서 매개변수 추출
            days = int(state["slots"].get("days", 7)) if state["slots"].get("days") else 7
            
            # 프로필에서 제약 조건 추출
            kcal_target = None
            carbs_max = 30
            allergies = []
            dislikes = []
            
            if state["profile"]:
                kcal_target = state["profile"].get("goals_kcal")
                carbs_max = state["profile"].get("goals_carbs_g", 30)
                allergies = state["profile"].get("allergies", [])
                dislikes = state["profile"].get("dislikes", [])
            
            # 식단표 생성
            meal_plan = await self.meal_planner.generate_meal_plan(
                days=days,
                kcal_target=kcal_target,
                carbs_max=carbs_max,
                allergies=allergies,
                dislikes=dislikes
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
            
        except Exception as e:
            print(f"Meal plan error: {e}")
            state["results"] = []
        
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
                # 의도별로 다른 포맷팅
                if state["intent"] == "recipe":
                    context = "추천 레시피:\n"
                    for idx, result in enumerate(state["results"][:3], 1):
                        context += f"{idx}. {result.get('name', '이름 없음')}\n"
                        if result.get('ingredients'):
                            context += f"   재료: {result['ingredients']}\n"
                        if result.get('carbs'):
                            context += f"   탄수화물: {result['carbs']}g\n"
                elif state["intent"] == "place":
                    context = "추천 식당:\n"
                    for idx, result in enumerate(state["results"][:5], 1):
                        context += f"{idx}. {result.get('name', '이름 없음')} (키토점수: {result.get('keto_score', 0)})\n"
                        context += f"   주소: {result.get('address', '')}\n"
                        if result.get('tips'):
                            context += f"   팁: {', '.join(result['tips'][:2])}\n"
                elif state["intent"] == "mealplan":
                    context = "생성된 식단표 요약"
                else:
                    context = json.dumps(state["results"][:3], ensure_ascii=False, indent=2)
                
                answer_prompt = RESPONSE_GENERATION_PROMPT.format(
                    message=message,
                    intent=state["intent"],
                    context=context
                )
            else:
                # 기본 응답 생성 프롬프트 사용
                answer_prompt = RESPONSE_GENERATION_PROMPT.format(
                    message=message,
                    intent=state["intent"],
                    context=context
                )
            
            response = await self.llm.ainvoke([HumanMessage(content=answer_prompt)])
            state["response"] = response.content
            
        except Exception as e:
            print(f"Answer generation error: {e}")
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